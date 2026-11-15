# /// script
# requires-python = ">=3.10"
# ///
"""Una carpeta por vídeo dentro de la carpeta del talento.

Uso:
    uv run videos.py nuevo <carpeta del talento> "<nombre del vídeo>"
    uv run videos.py lista <carpeta del talento>

nuevo   crea «AAAA-MM-DD Nombre/» con 01_brief … 06_entrega y escribe su ruta en la última línea.
        Si ese nombre ya existe ese día, añade « (2)», « (3)»… Nunca toca una carpeta existente.
lista   enseña los vídeos del talento, del más reciente al más antiguo, con cuántos clips tiene
        cada uno y la última versión entregada. Con --json, la misma lista en JSON.

Solo biblioteca estándar. Códigos: 0 bien · 2 nombre o carpeta no válidos.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SUBCARPETAS = ("01_brief", "02_brutos", "03_recursos", "04_marca", "05_musica", "06_entrega")
VIDEO = re.compile(r"^(\d{4}-\d{2}-\d{2}) (.+)$")
EXTENSIONES = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".3gp"}
PROHIBIDOS = '<>:"/\\|?*'


def limpiar_nombre(nombre: str) -> str:
    """Quita lo que Windows o macOS no aceptan en un nombre de carpeta."""
    limpio = "".join(" " if c in PROHIBIDOS or ord(c) < 32 else c for c in nombre)
    limpio = re.sub(r"\s+", " ", limpio).strip(" .")
    return limpio[:60].strip(" .")


def nuevo(talento: Path, nombre: str) -> Path:
    limpio = limpiar_nombre(nombre)
    if not limpio:
        print("El nombre del vídeo está vacío o solo tiene signos que no valen para una carpeta. Elige otro.")
        sys.exit(2)
    base = f"{dt.date.today().isoformat()} {limpio}"
    destino = talento / base
    n = 2
    while destino.exists():
        destino = talento / f"{base} ({n})"
        n += 1
    for sub in SUBCARPETAS:
        (destino / sub).mkdir(parents=True)
    return destino


def ultima_version(entrega: Path) -> str | None:
    versiones = [int(m.group(1)) for p in entrega.glob("video-v*.mp4") if (m := re.match(r"video-v(\d+)\.mp4$", p.name))]
    return f"video-v{max(versiones)}.mp4" if versiones else None


def lista(talento: Path) -> list[dict]:
    videos = []
    for d in talento.iterdir():
        if d.is_dir() and VIDEO.match(d.name) and (d / "02_brutos").is_dir():
            clips = sum(1 for f in (d / "02_brutos").rglob("*") if f.is_file() and f.suffix.lower() in EXTENSIONES)
            videos.append({"carpeta": d.name, "ruta": str(d), "clips": clips,
                           "ultima_version": ultima_version(d / "06_entrega"),
                           "modificado": max((f.stat().st_mtime for f in d.rglob("*")), default=d.stat().st_mtime)})
    return sorted(videos, key=lambda v: (v["carpeta"][:10], v["modificado"]), reverse=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Carpetas de vídeo del talento.")
    sub = p.add_subparsers(dest="accion", required=True)
    a = sub.add_parser("nuevo", help="crea la carpeta de un vídeo nuevo")
    a.add_argument("talento", type=Path)
    a.add_argument("nombre")
    b = sub.add_parser("lista", help="lista los vídeos del talento")
    b.add_argument("talento", type=Path)
    b.add_argument("--json", action="store_true")
    args = p.parse_args()

    talento = args.talento.resolve()
    if not talento.is_dir():
        print(f"No existe la carpeta {talento}.")
        return 2

    if args.accion == "nuevo":
        destino = nuevo(talento, args.nombre)
        print(f"Vídeo nuevo: «{destino.name}». Los clips van en {destino / '02_brutos'}")
        print(destino)
        return 0

    videos = lista(talento)
    if args.json:
        print(json.dumps(videos, ensure_ascii=False, indent=1))
        return 0
    if not videos:
        print("Todavía no hay vídeos en esta carpeta.")
        return 0
    for k, v in enumerate(videos, 1):
        estado = f"entregado: {v['ultima_version']}" if v["ultima_version"] else "sin entregar"
        print(f"{k}. {v['carpeta']} · {v['clips']} clips · {estado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
