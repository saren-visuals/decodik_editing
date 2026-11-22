"""Inventario de una carpeta de recursos: lista cada archivo con fecha, duración, orientación y miniatura.

Uso:
  python inventario.py --carpeta "<carpeta>" --out "<carpeta>/_inventario"
"""
import argparse
import datetime
from pathlib import Path

from comun import aviso, escribir_json, ffmpeg, sondear

VIDEO = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm"}
FOTO = {".jpg", ".jpeg", ".png", ".heic", ".webp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--carpeta", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    raiz, out = Path(a.carpeta), Path(a.out)
    minis = out / "miniaturas"
    minis.mkdir(parents=True, exist_ok=True)
    filas = []
    archivos = sorted(p for p in raiz.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO | FOTO
                      and out not in p.parents)
    for n, f in enumerate(archivos, 1):
        fecha = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
        fila = {"n": n, "archivo": str(f.relative_to(raiz)), "fecha": fecha, "tipo": "video" if f.suffix.lower() in VIDEO else "foto"}
        mini = minis / f"{n:04d}.jpg"
        try:
            if fila["tipo"] == "video":
                i = sondear(f)
                fila.update(duracion=round(i["duracion"], 1), orientacion="vertical" if i["alto"] > i["ancho"] else "horizontal")
                ffmpeg(["-ss", str(min(1.0, i["duracion"] / 2)), "-i", str(f), "-frames:v", "1", "-vf", "scale=320:-2", str(mini)])
            else:
                ffmpeg(["-i", str(f), "-frames:v", "1", "-vf", "scale=320:-2", str(mini)])
            fila["miniatura"] = str(mini)
        except SystemExit:
            fila["error"] = "no se pudo leer"
        filas.append(fila)
        if n % 25 == 0:
            aviso(f"{n}/{len(archivos)}…")
    escribir_json(out / "inventario.json", filas)
    lineas = ["| # | Archivo | Tipo | Fecha | Duración | Orientación |", "|---|---|---|---|---|---|"]
    for r in filas:
        lineas.append(f"| {r['n']} | {r['archivo']} | {r['tipo']} | {r['fecha']} | {r.get('duracion', '')} | {r.get('orientacion', '')} |")
    (out / "inventario.md").write_text("\n".join(lineas), encoding="utf-8")
    aviso(f"{len(filas)} archivos. Inventario en {out / 'inventario.md'}; miniaturas en {minis}")


if __name__ == "__main__":
    main()
