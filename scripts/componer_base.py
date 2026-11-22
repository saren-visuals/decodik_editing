"""Avanzado · Compone la base con texto detrás de la cabeza: toma + capa de detrás + (toma recortada con el mate).

Uso:
  python componer_base.py --toma 06_trabajo/cortado.mp4 --mate 06_trabajo/mate.mp4
                          --detras 06_trabajo/detras.mov --out 06_trabajo/graficos/assets/base.mp4
"""
import argparse
from pathlib import Path

from comun import aviso, codificador, ffmpeg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--toma", required=True)
    ap.add_argument("--mate", required=True)
    ap.add_argument("--detras", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    filtro = ("[0:v]format=rgba,split[fondo][suj];[2:v]format=rgba[det];"
              "[fondo][det]overlay=format=auto[fd];[1:v]format=gray[m];"
              "[suj][m]alphamerge[recorte];[fd][recorte]overlay=format=auto,format=yuv420p[v]")
    ffmpeg(["-i", a.toma, "-i", a.mate, "-i", a.detras, "-filter_complex", filtro, "-map", "[v]", "-map", "0:a?",
            *codificador(), "-c:a", "copy", a.out])
    aviso(f"Base con palabra detrás: {a.out}")


if __name__ == "__main__":
    main()
