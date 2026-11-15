# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["faster-whisper>=1.1,<2"]
# ///
"""Transcribe los brutos del talento con tiempos por palabra.

Uso:
    uv run transcribir.py <carpeta del talento o 02_brutos> [--nombres "Eileen Gu, Stanford"] [--modelo M] [--idioma es] [--forzar]

--nombres ayuda a Whisper a escribir bien nombres propios, marcas y productos.

Busca los vídeos dentro de 02_brutos/ (también en subcarpetas), en orden natural
(Clip 2 va antes que Clip 10), y escribe en <carpeta>/06_entrega/trabajo/:

    transcripcion.json   un objeto por clip: datos del vídeo, tramos de silencio, frases y palabras
                         con inicio y fin en segundos (los inicios que Whisper adelanta dentro de un
                         silencio se corrigen con la detección de silencios de ffmpeg)
    transcripcion.md     lo mismo para leerlo: cada frase con su tiempo

Si un clip no ha cambiado desde la última vez, no se vuelve a transcribir.
Códigos de salida: 0 bien · 1 error interno · 2 falta algo en la carpeta.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

EXTENSIONES = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".3gp"}
MODELO_POR_DEFECTO = "large-v3-turbo"
VERSION_FORMATO = 5


def orden_natural(ruta: Path) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", ruta.as_posix())]


def carpetas(entrada: Path) -> tuple[Path, Path]:
    """Devuelve (carpeta del talento, carpeta de brutos)."""
    entrada = entrada.resolve()
    if (entrada / "02_brutos").is_dir():
        return entrada, entrada / "02_brutos"
    if entrada.name == "02_brutos":
        return entrada.parent, entrada
    print(f"No encuentro la carpeta 02_brutos en {entrada}. Pasa la carpeta del talento o su 02_brutos.")
    sys.exit(2)


def datos_video(ruta: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,r_frame_rate:stream_side_data=rotation",
         "-of", "json", str(ruta)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        return {}
    info = json.loads(r.stdout)
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    tiene_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    rotacion = next((d.get("rotation") for d in video.get("side_data_list", []) if "rotation" in d), 0) or 0
    ancho, alto = video.get("width"), video.get("height")
    if ancho and alto and abs(int(rotacion)) in (90, 270):
        ancho, alto = alto, ancho
    num, _, den = (video.get("r_frame_rate") or "0/1").partition("/")
    fps = round(int(num) / int(den or 1), 3) if int(den or 1) else None
    return {
        "duracion": round(float(info.get("format", {}).get("duration", 0)), 3),
        "ancho": ancho, "alto": alto, "fps": fps, "audio": tiene_audio,
    }


def huella(ruta: Path, modelo: str, idioma: str, nombres: str) -> str:
    st = ruta.stat()
    return f"{st.st_size}-{int(st.st_mtime)}-{modelo}-{idioma}-{nombres}-v{VERSION_FORMATO}"


def audio_16k(ruta: Path):
    """Saca el audio con ffmpeg (mono, 16 kHz) como array de numpy, sin depender del lector de vídeo de Python."""
    import numpy as np

    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-i", str(ruta), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
        capture_output=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg no pudo leer el audio de {ruta.name}: {r.stderr.decode(errors='replace')[-200:]}")
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0


UMBRAL_SILENCIO_DB = -35
SILENCIO_MIN_S = 0.25


def silencios(ruta: Path) -> list[tuple[float, float]]:
    """Tramos sin voz según ffmpeg (por debajo de UMBRAL_SILENCIO_DB durante al menos SILENCIO_MIN_S).

    Une tramos separados por menos de 50 ms (un clic o un roce no es voz).
    """
    r = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-i", str(ruta), "-vn",
         "-af", f"silencedetect=n={UMBRAL_SILENCIO_DB}dB:d={SILENCIO_MIN_S}", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    inicios = [float(x) for x in re.findall(r"silence_start: (-?[0-9.]+)", r.stderr)]
    finales = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    tramos = []
    for a, b in zip(inicios, finales):
        a = max(a, 0.0)
        if tramos and a - tramos[-1][1] < 0.05:
            tramos[-1] = (tramos[-1][0], b)
        else:
            tramos.append((a, b))
    return tramos


def ajustar_inicios(frases: list[dict], tramos: list[tuple[float, float]]) -> int:
    """Whisper suele adelantar la primera palabra que llega después de una pausa y la coloca
    dentro del silencio. Si una palabra empieza dentro de un silencio y al menos la mitad de
    ella es silencio, su inicio pasa al final de ese silencio. Devuelve cuántas se movieron."""
    movidas = 0
    palabras = [w for f in frases for w in f["palabras"]]
    for i, w in enumerate(palabras):
        dur = max(w["fin"] - w["inicio"], 1e-3)
        for a, b in tramos:
            if a <= w["inicio"] < b:
                solape = min(w["fin"], b) - w["inicio"]
                if solape / dur >= 0.5:
                    siguiente = palabras[i + 1]["inicio"] if i + 1 < len(palabras) else None
                    nuevo = round(b, 3)
                    if siguiente is not None and nuevo >= siguiente:
                        break
                    w["inicio_whisper"] = w["inicio"]
                    w["inicio"] = nuevo
                    if w["fin"] <= nuevo:
                        w["fin_whisper"] = w["fin"]
                        w["fin"] = round(min(nuevo + dur, siguiente) if siguiente else nuevo + dur, 3)
                    movidas += 1
                break
    for f in frases:
        f["inicio"], f["fin"] = f["palabras"][0]["inicio"], f["palabras"][-1]["fin"]
    return movidas


def transcribir_clip(modelo, ruta: Path, idioma: str, nombres: str) -> list[dict]:
    segmentos, _ = modelo.transcribe(
        audio_16k(ruta),
        language=idioma,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300, "speech_pad_ms": 200},
        condition_on_previous_text=False,
        beam_size=5,
        # Sin prompt ni palabras clave a propósito: con ellos Whisper a veces se salta una toma
        # repetida, y las tomas repetidas son justo lo que hay que detectar al cortar.
    )
    lista = [n.strip() for n in nombres.split(",") if n.strip()]
    frases = []
    for s in segmentos:
        palabras = [
            {"p": w.word.strip(), "inicio": round(w.start, 3), "fin": round(w.end, 3), "prob": round(w.probability, 3)}
            for w in (s.words or []) if w.word.strip()
        ]
        if not palabras:
            continue
        palabras = corregir_nombres(palabras, lista)
        frases.append({
            "inicio": palabras[0]["inicio"],
            "fin": palabras[-1]["fin"],
            "texto": " ".join(w["p"] for w in palabras),
            "palabras": palabras,
        })
    return frases


PUNTUACION = ".,;:!?¡¿…\"'«»()"


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin_tildes if c.isalnum())


def corregir_nombres(palabras: list[dict], nombres: list[str]) -> list[dict]:
    """Escribe bien los nombres propios que Whisper oyó parecido («Eilengu» → «Eileen Gu»).

    Compara grupos de 1 a n+1 palabras seguidas con cada nombre, sin tildes, espacios ni
    mayúsculas. Si se parecen lo suficiente, las une en una sola entrada con el nombre bien
    escrito y guarda lo que oyó Whisper en «p_whisper».
    """
    for nombre in nombres:
        objetivo = normalizar(nombre)
        if len(objetivo) < 3:
            continue
        n = len(nombre.split())
        i = 0
        while i < len(palabras):
            mejor = None
            for largo in range(1, n + 2):
                grupo = palabras[i:i + largo]
                if len(grupo) < largo:
                    break
                oido = normalizar("".join(w["p"] for w in grupo))
                # El grupo tiene que empezar y acabar como el nombre: así «en Stanford» no se come el «en».
                if not oido or oido[:2] != objetivo[:2] or oido[-2:] != objetivo[-2:]:
                    continue
                parecido = SequenceMatcher(None, oido, objetivo).ratio()
                if parecido >= 0.85 and (mejor is None or parecido > mejor[1]):
                    mejor = (largo, parecido)
            if mejor:
                largo = mejor[0]
                grupo = palabras[i:i + largo]
                oido = " ".join(w["p"] for w in grupo)
                ultimo = grupo[-1]["p"]
                final = ultimo[len(ultimo.rstrip(PUNTUACION)):]
                nuevo = {
                    "p": nombre + final,
                    "inicio": grupo[0]["inicio"],
                    "fin": grupo[-1]["fin"],
                    "prob": min(w["prob"] for w in grupo),
                }
                if oido.rstrip(PUNTUACION) != nombre:
                    nuevo["p_whisper"] = oido
                palabras[i:i + largo] = [nuevo]
            i += 1
    return palabras


def tiempo(seg: float) -> str:
    return f"{int(seg // 60)}:{seg % 60:05.2f}"


def escribir_md(destino: Path, resultado: dict) -> None:
    lineas = [f"# Transcripción · {resultado['carpeta']}", "",
              f"_Modelo {resultado['modelo']} · idioma {resultado['idioma']} · {len(resultado['clips'])} clips_", ""]
    for c in resultado["clips"]:
        lineas.append(f"## {c['archivo']} · {c['video'].get('duracion', 0):.1f} s")
        if not c["frases"]:
            lineas.append("_(sin voz detectada)_")
        for f in c["frases"]:
            lineas.append(f"- `{tiempo(f['inicio'])}–{tiempo(f['fin'])}` {f['texto']}")
        lineas.append("")
    destino.write_text("\n".join(lineas), encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Transcribe los brutos con tiempos por palabra.")
    p.add_argument("carpeta", type=Path, help="carpeta del talento (con 02_brutos/) o la propia 02_brutos")
    p.add_argument("--modelo", default=MODELO_POR_DEFECTO, help=f"modelo de Whisper (por defecto {MODELO_POR_DEFECTO})")
    p.add_argument("--idioma", default="es", help="idioma del audio (por defecto es)")
    p.add_argument("--nombres", default="", help="nombres propios, marcas o productos separados por comas")
    p.add_argument("--forzar", action="store_true", help="vuelve a transcribir aunque no haya cambios")
    args = p.parse_args()

    talento, brutos = carpetas(args.carpeta)
    clips = sorted((r for r in brutos.rglob("*") if r.is_file() and r.suffix.lower() in EXTENSIONES), key=orden_natural)
    if not clips:
        print(f"No hay vídeos en {brutos}. Sube los clips del móvil (mp4 o mov) y vuelve a intentarlo.")
        return 2

    trabajo = talento / "06_entrega" / "trabajo"
    trabajo.mkdir(parents=True, exist_ok=True)
    salida = trabajo / "transcripcion.json"
    anterior = {}
    if salida.exists() and not args.forzar:
        try:
            anterior = {c["archivo"]: c for c in json.loads(salida.read_text(encoding="utf-8"))["clips"]}
        except (json.JSONDecodeError, KeyError):
            anterior = {}

    print(f"{len(clips)} clips en {brutos}")
    modelo = None
    resultado = {"version": VERSION_FORMATO, "carpeta": talento.name, "modelo": args.modelo,
                 "idioma": args.idioma, "nombres": args.nombres, "clips": []}
    inicio_total = time.time()
    for ruta in clips:
        rel = ruta.relative_to(brutos).as_posix()
        h = huella(ruta, args.modelo, args.idioma, args.nombres)
        if rel in anterior and anterior[rel].get("huella") == h:
            resultado["clips"].append(anterior[rel])
            print(f"  = {rel} (sin cambios)")
            continue
        video = datos_video(ruta)
        if not video.get("audio"):
            print(f"  ! {rel}: no tiene audio, lo salto.")
            resultado["clips"].append({"archivo": rel, "huella": h, "video": video, "frases": []})
            continue
        if modelo is None:
            print(f"  … Cargando el modelo {args.modelo} (la primera vez se descarga, puede tardar unos minutos).")
            from faster_whisper import WhisperModel
            modelo = WhisperModel(args.modelo, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
        t0 = time.time()
        frases = transcribir_clip(modelo, ruta, args.idioma, args.nombres)
        tramos = silencios(ruta)
        movidas = ajustar_inicios(frases, tramos)
        n = sum(len(f["palabras"]) for f in frases)
        ajuste = f" · {movidas} inicios ajustados al audio" if movidas else ""
        print(f"  ✓ {rel} · {video.get('duracion', 0):.1f} s · {n} palabras{ajuste} · {time.time() - t0:.1f} s")
        resultado["clips"].append({
            "archivo": rel, "huella": h, "video": video,
            "silencios": [[round(a, 3), round(b, 3)] for a, b in tramos],
            "frases": frases,
        })

    salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    escribir_md(trabajo / "transcripcion.md", resultado)
    total_palabras = sum(len(f["palabras"]) for c in resultado["clips"] for f in c["frases"])
    print(f"\nListo en {time.time() - inicio_total:.0f} s: {total_palabras} palabras.")
    print(f"  {salida}")
    print(f"  {trabajo / 'transcripcion.md'}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
