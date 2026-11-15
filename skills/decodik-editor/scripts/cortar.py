# /// script
# requires-python = ">=3.10"
# ///
"""Corte automático: deja solo la voz útil de los brutos.

Uso:
    uv run cortar.py <carpeta del talento> [--pausa-max 0.3] [--sin-video] [--rapido]

Lee 06_entrega/trabajo/transcripcion.json (de transcribir.py) y:
  1. quita muletillas («eh», «em», «mmm») y palabras repetidas pegadas («que que»);
  2. detecta frases dichas más de una vez (tomas repetidas y arranques en falso) y se queda
     con la MEJOR toma: la más clara y completa, con menos pausas y muletillas;
  3. quita el silencio del principio y del final de cada frase y acorta a cero las pausas
     de más de --pausa-max segundos, dejando un pequeño margen para no cortar sílabas.

Escribe en 06_entrega/trabajo/:
    cortes.json   tramos que se quedan (clip, inicio, fin, texto) y lo que se quitó con su motivo
    cortes.md     lo mismo para leerlo
    corte.mp4     borrador vertical 1080×1920 sin subtítulos, para escucharlo (salvo --sin-video)

Solo usa la biblioteca estándar de Python y ffmpeg. Códigos: 0 bien · 1 error · 2 falta algo.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MARGEN_ANTES = 0.08      # s de aire antes de la primera palabra de un tramo
MARGEN_DESPUES = 0.12    # s de aire después de la última palabra de un tramo
ALARGAR_HASTA = 0.35     # si el silencio empieza hasta 0,35 s después del fin de Whisper, la voz sigue hasta ahí
PARECIDO_TOMA = 0.6      # parecido mínimo entre dos frases para considerarlas la misma toma
MULETILLA = re.compile(r"^(e+h+|e+m+|m{2,}|h+m+|a+h+m*|u+m+)$")


# ---------- texto ----------

def norm(palabra: str) -> str:
    s = unicodedata.normalize("NFD", palabra.lower())
    return "".join(c for c in s if c.isalnum())


def es_muletilla(palabra: str) -> bool:
    return bool(MULETILLA.match(norm(palabra)))


def tiempo(seg: float) -> str:
    return f"{int(seg // 60)}:{seg % 60:05.2f}"


# ---------- análisis ----------

def limpiar(frase: dict, descartes: list, clip: str) -> list[dict]:
    """Quita muletillas y la primera de dos palabras iguales seguidas. Devuelve las palabras que quedan."""
    quedan = []
    for w in frase["palabras"]:
        if es_muletilla(w["p"]):
            descartes.append({"clip": clip, "inicio": w["inicio"], "fin": w["fin"], "texto": w["p"], "motivo": "muletilla"})
            continue
        if quedan and norm(quedan[-1]["p"]) == norm(w["p"]) and w["inicio"] - quedan[-1]["fin"] < 0.6:
            anterior = quedan.pop()
            descartes.append({"clip": clip, "inicio": anterior["inicio"], "fin": anterior["fin"],
                              "texto": anterior["p"], "motivo": "palabra repetida"})
        quedan.append(w)
    return quedan


def puntuar(toma: dict, mas_larga: int) -> float:
    """Más alto = mejor toma: palabras oídas con claridad, completa, sin pausas largas ni muletillas."""
    ws = toma["palabras"]
    if not ws:
        return -1.0
    claridad = sum(w["prob"] for w in ws) / len(ws)
    completa = len(ws) / mas_larga
    pausas = sum(1 for a, b in zip(ws, ws[1:]) if b["inicio"] - a["fin"] > 0.5)
    return round(claridad - 0.5 * (1 - completa) - 0.05 * pausas - 0.1 * toma["muletillas"], 4)


def misma_toma(a: dict, b: dict) -> bool:
    pa = [norm(w["p"]) for w in a["palabras"]]
    pb = [norm(w["p"]) for w in b["palabras"]]
    if not pa or not pb:
        return False
    if SequenceMatcher(None, pa, pb).ratio() >= PARECIDO_TOMA:
        return True
    # Arranque en falso: una frase corta que es el principio de la siguiente.
    corta, larga = (pa, pb) if len(pa) <= len(pb) else (pb, pa)
    return len(corta) >= 3 and SequenceMatcher(None, corta, larga[:len(corta)]).ratio() >= 0.8


def elegir_tomas(frases: list[dict], descartes: list) -> list[dict]:
    """Agrupa frases que son la misma toma (hasta 2 frases de distancia) y deja la mejor de cada grupo."""
    grupo_de = list(range(len(frases)))
    for i in range(len(frases)):
        for j in (i + 1, i + 2):
            if j < len(frases) and misma_toma(frases[i], frases[j]):
                grupo_de[j] = grupo_de[i]
    grupos: dict[int, list[int]] = {}
    for i, g in enumerate(grupo_de):
        grupos.setdefault(g, []).append(i)

    elegidas = set()
    for indices in grupos.values():
        if len(indices) == 1:
            elegidas.add(indices[0])
            continue
        mas_larga = max(len(frases[i]["palabras"]) for i in indices)
        notas = {i: puntuar(frases[i], mas_larga) for i in indices}
        mejor = max(indices, key=lambda i: (notas[i], i))
        elegidas.add(mejor)
        frases[mejor]["tomas"] = {f"{frases[i]['clip']} {tiempo(frases[i]['palabras'][0]['inicio'])}": notas[i] for i in indices}
        for i in indices:
            if i != mejor:
                f = frases[i]
                descartes.append({"clip": f["clip"], "inicio": f["palabras"][0]["inicio"], "fin": f["palabras"][-1]["fin"],
                                  "texto": " ".join(w["p"] for w in f["palabras"]),
                                  "motivo": f"toma repetida (nota {notas[i]}; se queda la de {frases[mejor]['clip']} "
                                            f"{tiempo(frases[mejor]['palabras'][0]['inicio'])}, nota {notas[mejor]})"})
    return [f for i, f in enumerate(frases) if i in elegidas]


def fin_real(w_fin: float, siguiente: float | None, silencios: list[list[float]], duracion: float) -> float:
    """Whisper a veces corta el final de la última sílaba. Si el audio sigue sonando un poco
    después, el tramo llega hasta donde empieza el silencio."""
    limite = siguiente if siguiente is not None else duracion
    for a, _ in silencios:
        if w_fin - 0.05 <= a <= w_fin + ALARGAR_HASTA:
            return min(a + 0.05, limite)
    return min(w_fin + MARGEN_DESPUES, limite)


def tramos_de_frase(frase: dict, todas: list[dict], silencios: list[list[float]], duracion: float, pausa_max: float) -> list[dict]:
    """Convierte las palabras que se quedan en tramos [inicio, fin] del clip original."""
    ws = frase["palabras"]
    tramos = []
    actual = [ws[0]]
    for a, b in zip(ws, ws[1:]):
        contiguas = todas.index(b) == todas.index(a) + 1
        if b["inicio"] - a["fin"] > pausa_max or not contiguas:
            tramos.append(actual)
            actual = [b]
        else:
            actual.append(b)
    tramos.append(actual)

    resultado = []
    for grupo in tramos:
        i0, i1 = todas.index(grupo[0]), todas.index(grupo[-1])
        anterior_fin = todas[i0 - 1]["fin"] if i0 > 0 else 0.0
        siguiente_ini = todas[i1 + 1]["inicio"] if i1 + 1 < len(todas) else None
        inicio = max(grupo[0]["inicio"] - MARGEN_ANTES, anterior_fin, 0.0)
        fin = fin_real(grupo[-1]["fin"], siguiente_ini, silencios, duracion)
        resultado.append({"inicio": round(inicio, 3), "fin": round(fin, 3), "texto": " ".join(w["p"] for w in grupo)})
    return resultado


AIRE_ENTRADA = 0.06   # s de silencio real que se deja antes de que empiece a sonar la voz
AIRE_SALIDA = 0.06    # s de silencio real que se deja después de que deje de sonar


def silencios_finos(ruta: Path) -> list[list[float]]:
    """Silencios de al menos 50 ms (más detalle que los de la transcripción) para afinar las uniones."""
    r = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-i", str(ruta), "-vn",
         "-af", "silencedetect=n=-35dB:d=0.05", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    inicios = [max(float(x), 0.0) for x in re.findall(r"silence_start: (-?[0-9.]+)", r.stderr)]
    finales = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    return [[a, b] for a, b in zip(inicios, finales)]


def ajustar_a_silencios(tramos: list[dict], silencios: list[list[float]], pausa_max: float) -> list[dict]:
    """Los tiempos de Whisper son aproximados. Con el mapa de silencios de ffmpeg:
    - si un tramo empieza o acaba dentro de un silencio, se recorta hasta casi donde suena la voz;
    - si dentro de un tramo hay un silencio real más largo que pausa_max, el tramo se parte en dos."""
    resultado = []
    for t in tramos:
        ini, fin = t["inicio"], t["fin"]
        for a, b in silencios:
            # La voz empieza donde acaba el silencio. Si eso cae cerca del inicio del tramo
            # (un poco antes o después), la entrada se fija a AIRE_ENTRADA antes de que suene.
            if a <= ini < b:
                # El tramo empieza en silencio: se adelanta hasta casi donde suena la voz.
                ini = b - AIRE_ENTRADA
            elif ini - 0.15 <= b <= ini:
                # La voz empezó un poco antes que la palabra de Whisper: se recupera ese arranque.
                ini = max(b - AIRE_ENTRADA, a)
            if a < fin <= b:
                fin = min(fin, a + AIRE_SALIDA)
        trozos = [[ini, fin]]
        for a, b in silencios:
            ultimo = trozos[-1]
            if ultimo[0] + 0.01 < a and b < ultimo[1] - 0.01 and b - a > pausa_max:
                trozos[-1] = [ultimo[0], a + AIRE_SALIDA]
                trozos.append([b - AIRE_ENTRADA, ultimo[1]])
        for k, (x, y) in enumerate(trozos):
            if y - x > 0.05:
                resultado.append({**t, "inicio": round(x, 3), "fin": round(y, 3),
                                  "texto": t["texto"] if k == 0 else "…"})
    return resultado


# ---------- vídeo ----------

def filtro_video(hdr: bool, transfer: str = "arib-std-b67") -> str:
    base = "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920"
    if hdr:
        # Los iPhone graban en HDR (HLG). Se pasa a color normal (SDR, BT.709) para que no salga lavado.
        base += (f",zscale=tin={transfer}:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,"
                 "zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv")
    return base + ",setsar=1,fps=30,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"


def render(segmentos: list[dict], brutos: Path, salida: Path, rapido: bool) -> None:
    hdr = {}
    entradas, partes = [], []
    for k, s in enumerate(segmentos):
        ruta = brutos / s["clip"]
        if s["clip"] not in hdr:
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                "stream=color_transfer", "-of", "csv=p=0", str(ruta)], capture_output=True, text=True)
            t = r.stdout.strip()
            hdr[s["clip"]] = t if t in ("arib-std-b67", "smpte2084") else ""
        d = s["fin"] - s["inicio"]
        entradas += ["-ss", f"{s['inicio']:.3f}", "-t", f"{d:.3f}", "-i", str(ruta)]
        t = hdr[s["clip"]]
        partes.append(f"[{k}:v:0]{filtro_video(bool(t), t or 'arib-std-b67')}[v{k}];"
                      f"[{k}:a:0]aformat=sample_rates=48000:channel_layouts=stereo,"
                      f"afade=t=in:d=0.01,afade=t=out:st={max(d - 0.01, 0):.3f}:d=0.01[a{k}];")
    union = "".join(f"[v{k}][a{k}]" for k in range(len(segmentos)))
    grafo = "".join(partes) + f"{union}concat=n={len(segmentos)}:v=1:a=1[v][a]"
    script = salida.with_suffix(".filtro.txt")
    script.write_text(grafo, encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin", *entradas,
           "-/filter_complex", str(script), "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "veryfast" if rapido else "medium", "-crf", "23" if rapido else "18",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(salida)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    script.unlink(missing_ok=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-800:])


# ---------- principal ----------

def main() -> int:
    p = argparse.ArgumentParser(description="Corte automático de silencios, muletillas y tomas repetidas.")
    p.add_argument("carpeta", type=Path, help="carpeta del talento")
    p.add_argument("--pausa-max", type=float, default=0.3, help="pausa máxima que se deja dentro de una frase (s)")
    p.add_argument("--sin-video", action="store_true", help="solo calcula los cortes, no renderiza corte.mp4")
    p.add_argument("--rapido", action="store_true", help="render más rápido y de menos calidad")
    args = p.parse_args()

    talento = args.carpeta.resolve()
    trabajo = talento / "06_entrega" / "trabajo"
    origen = trabajo / "transcripcion.json"
    if not origen.exists():
        print(f"Falta {origen}. Antes transcribe los brutos con transcribir.py.")
        return 2
    datos = json.loads(origen.read_text(encoding="utf-8"))
    brutos = talento / "02_brutos"

    descartes: list[dict] = []
    frases, por_clip = [], {}
    for c in datos["clips"]:
        todas = [w for f in c["frases"] for w in f["palabras"]]
        por_clip[c["archivo"]] = (todas, c.get("silencios", []), c["video"].get("duracion", 0))
        for f in c["frases"]:
            antes = len(f["palabras"])
            quedan = limpiar(f, descartes, c["archivo"])
            muletillas = sum(1 for w in f["palabras"] if es_muletilla(w["p"]))
            if quedan:
                frases.append({"clip": c["archivo"], "palabras": quedan, "muletillas": muletillas,
                               "quitadas": antes - len(quedan)})

    elegidas = elegir_tomas(frases, descartes)

    segmentos, finos = [], {}
    for f in elegidas:
        todas, silencios, duracion = por_clip[f["clip"]]
        tramos = tramos_de_frase(f, todas, silencios, duracion, args.pausa_max)
        if f["clip"] not in finos:
            finos[f["clip"]] = silencios_finos(brutos / f["clip"])
        for t in ajustar_a_silencios(tramos, finos[f["clip"]], args.pausa_max):
            segmentos.append({"clip": f["clip"], **t})

    # Une tramos del mismo clip que se tocan.
    unidos: list[dict] = []
    for s in segmentos:
        if unidos and unidos[-1]["clip"] == s["clip"] and s["inicio"] <= unidos[-1]["fin"] + 0.01:
            unidos[-1]["fin"] = max(unidos[-1]["fin"], s["fin"])
            unidos[-1]["texto"] += " " + s["texto"]
        else:
            unidos.append(dict(s))
    segmentos = unidos

    bruto_total = sum(c["video"].get("duracion", 0) for c in datos["clips"])
    final_total = sum(s["fin"] - s["inicio"] for s in segmentos)
    resultado = {
        "version": 1,
        "pausa_max": args.pausa_max,
        "duracion_brutos": round(bruto_total, 2),
        "duracion_corte": round(final_total, 2),
        "segmentos": segmentos,
        "descartes": descartes,
        "tomas": [{"clip": f["clip"], "notas": f["tomas"]} for f in elegidas if "tomas" in f],
    }
    (trabajo / "cortes.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")

    lineas = ["# Cortes", "", f"Brutos: {bruto_total:.1f} s → corte: {final_total:.1f} s · {len(segmentos)} tramos", "",
              "## Lo que se queda", "", "| # | Clip | Desde | Hasta | Texto |", "|---|---|---|---|---|"]
    for k, s in enumerate(segmentos, 1):
        lineas.append(f"| {k} | {Path(s['clip']).name} | {tiempo(s['inicio'])} | {tiempo(s['fin'])} | {s['texto']} |")
    lineas += ["", "## Lo que se quita", ""]
    lineas += [f"- **{d['motivo']}** · {Path(d['clip']).name} {tiempo(d['inicio'])}: «{d['texto']}»" for d in descartes] or ["- Nada aparte de silencios."]
    (trabajo / "cortes.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    print(f"Brutos {bruto_total:.1f} s → corte {final_total:.1f} s en {len(segmentos)} tramos.")
    for d in descartes:
        print(f"  − {d['motivo']}: {Path(d['clip']).name} {tiempo(d['inicio'])} «{d['texto'][:60]}»")

    if not args.sin_video:
        salida = trabajo / "corte.mp4"
        print("Renderizando el borrador del corte…")
        render(segmentos, brutos, salida, args.rapido)
        print(f"  {salida}")
    print(f"  {trabajo / 'cortes.md'}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as e:
        print(f"No se pudo renderizar el corte: {e}")
        sys.exit(1)
