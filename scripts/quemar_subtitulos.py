"""Quema los subtítulos .ass sobre el vídeo (nivel básico).

Uso:
  python quemar_subtitulos.py --video 06_trabajo/cortado.mp4 --ass 06_trabajo/subtitulos/subtitulos.ass
                              --out 06_trabajo/con_subtitulos.mp4 [--fuentes <carpeta con tipografías extra>]
"""
import argparse
import shutil
import subprocess
from pathlib import Path

from comun import SKILL, aviso, codificador, error, herramienta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--ass", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fuentes", action="append", default=[])
    a = ap.parse_args()

    ass = Path(a.ass).resolve()
    carpeta = ass.parent
    fuentes = carpeta / "_fuentes"
    fuentes.mkdir(exist_ok=True)
    for origen in [SKILL / "fonts", *map(Path, a.fuentes)]:
        for f in Path(origen).glob("*"):
            if f.suffix.lower() in (".ttf", ".otf"):
                shutil.copy2(f, fuentes / f.name)

    # Rutas relativas dentro del filtro: evita los problemas de escapar C:\ en Windows.
    cmd = [herramienta("ffmpeg"), "-hide_banner", "-y", "-loglevel", "error",
           "-i", str(Path(a.video).resolve()),
           "-vf", f"ass={ass.name}:fontsdir=_fuentes", *codificador(), "-c:a", "copy",
           "-movflags", "+faststart", str(Path(a.out).resolve())]
    r = subprocess.run(cmd, cwd=carpeta, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:])
        error("No se pudieron quemar los subtítulos.")
    aviso(f"Vídeo con subtítulos: {a.out}")


if __name__ == "__main__":
    main()
