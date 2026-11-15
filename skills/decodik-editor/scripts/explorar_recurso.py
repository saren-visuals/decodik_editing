# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["faster-whisper>=1.1,<2"]
# ///
"""Explora un vídeo largo de 03_recursos/ para elegir fragmentos (reportaje, partido, directo…).

Uso:
    uv run explorar_recurso.py <carpeta del vídeo> "<archivo de 03_recursos>" [--cada 20] [--sin-voz] [--idioma en]

Escribe en 06_entrega/trabajo/explorar/:
    <nombre>-hoja-N.jpg   hojas de fotogramas (uno cada --cada segundos, con su minuto:segundo)
    <nombre>.md           lo que se dice, frase a frase con su minuto:segundo (salvo --sin-voz)

Con eso, Claude elige qué fragmentos casan con lo que dice el talento y los pone en recursos.json
con "desde" (p. ej. "desde": "4:12"). El color y el sonido del vídeo no se tocan.
Códigos: 0 bien · 2 falta el archivo.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fuentes  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POR_HOJA = 24          # 6 × 4 fotogramas por hoja
ANCHO_FOTO = 320


def mmss(seg: float) -> str:
    return f"{int(seg // 60)}:{int(seg % 60):02d}"


def main() -> int:
    p = argparse.ArgumentParser(description="Hojas de fotogramas y transcripción de un vídeo largo de recursos.")
    p.add_argument("carpeta", type=Path)
    p.add_argument("archivo", help="nombre del archivo dentro de 03_recursos/")
    p.add_argument("--cada", type=float, default=20, help="segundos entre fotogramas (por defecto 20)")
    p.add_argument("--sin-voz", action="store_true", help="no transcribe")
    p.add_argument("--idioma", default=None, help="idioma del audio (por defecto, lo detecta)")
    args = p.parse_args()

    video = args.carpeta.resolve()
    origen = video / "03_recursos" / args.archivo
    if not origen.exists():
        print(f"No está {origen}.")
        return 2
    salida = video / "06_entrega" / "trabajo" / "explorar"
    salida.mkdir(parents=True, exist_ok=True)
    nombre = origen.stem
    dur = float(json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json",
                                           str(origen)], capture_output=True, text=True).stdout)["format"]["duration"])
    letra = (fuentes.asegurar(["InterDisplay-Bold.ttf"]) / "InterDisplay-Bold.ttf").as_posix().replace(":", "\\:")

    # Hojas de fotogramas: un fotograma cada --cada segundos con su minuto:segundo encima.
    n = int(dur // args.cada) + 1
    hojas = 0
    for h in range(0, n, POR_HOJA):
        cuantos = min(POR_HOJA, n - h)
        t0 = h * args.cada
        # Un fotograma justo en cada marca (0, cada, 2·cada…): «fps=1/N» cogería el del medio
        # del intervalo y las marcas saldrían adelantadas N/2 segundos.
        filtro = (f"select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,{args.cada - 0.02})',setpts=N/TB,"
                  f"scale={ANCHO_FOTO}:-2,"
                  f"drawtext=fontfile='{letra}':text='%{{eif\\:trunc(({t0}+n*{args.cada})/60)\\:d}}\\:"
                  f"%{{eif\\:mod({t0}+n*{args.cada}\\,60)\\:d\\:2}}':x=6:y=6:fontsize=22:fontcolor=white:"
                  f"box=1:boxcolor=black@0.7:boxborderw=5,tile=6x4:padding=4:color=black")
        hojas += 1
        destino = salida / f"{nombre}-hoja-{hojas}.jpg"
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.2f}", "-t", f"{cuantos * args.cada:.2f}",
                            "-i", str(origen), "-vf", filtro, "-frames:v", "1", "-q:v", "4", str(destino)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print(f"  ! No se pudo hacer la hoja {hojas}: {r.stderr.strip()[-200:]}")
            continue
        print(f"  · {destino.name}: {mmss(t0)}–{mmss(min(t0 + cuantos * args.cada, dur))}")

    if not args.sin_voz:
        import numpy as np
        from faster_whisper import WhisperModel

        print(f"  … Transcribiendo {mmss(dur)} de audio (tarda más o menos lo que dura el vídeo).")
        audio = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(origen), "-vn", "-ac", "1", "-ar", "16000",
                                "-f", "s16le", "-"], capture_output=True).stdout
        arr = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
        modelo = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
        segs, info = modelo.transcribe(arr, language=args.idioma, vad_filter=True, condition_on_previous_text=False)
        lineas = [f"# {origen.name} · {mmss(dur)} · idioma {info.language}", ""]
        lineas += [f"- `{mmss(s.start)}` {s.text.strip()}" for s in segs]
        (salida / f"{nombre}.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
        print(f"  · {nombre}.md: {len(lineas) - 2} frases")
    print(f"Listo: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
