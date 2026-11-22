"""Crea la carpeta Decodik y/o un proyecto nuevo con su estructura y proyecto.json.

Uso:
  python crear_proyecto.py --raiz "<Documentos>/Decodik" --solo-raiz
  python crear_proyecto.py --raiz "<Decodik>" --nombre "rutina piernas" --caso marca-personal --nivel basico --toma "<ruta>"
"""
import argparse
import datetime
import re
import shutil
import unicodedata
from pathlib import Path

from comun import aviso, escribir_json

LEEME_RAIZ = """CARPETA DECODIK
===============
Abre Claude Code siempre en esta carpeta.

_mi-estilo/       tu estilo: reglas.md, estilo.json, referencias/, logos/, tipografias/, efectos/
_recursos/        tu biblioteca de clips y fotos ordenada (indice.md)
_tomas-sueltas/   deja aquí vídeos sin proyecto si solo quieres cortarlos
proyectos/        un proyecto por vídeo
"""

LEEME_PROYECTO = """01_brief/     solo vídeos para marcas: brief, guion, guía de marca
02_tomas/     tus vídeos grabados. NUNCA se modifican: Claude trabaja con copias
03_recursos/  fotos, capturas y B-roll para este vídeo
04_marca/     logo, tipografías y colores (de la marca o tuyos)
05_musica/    música con licencia y efectos/ (opcional)
06_trabajo/   archivos intermedios. Se puede borrar al publicar
07_entrega/   el vídeo final, subtítulos y portada
"""

CARPETAS = ["01_brief", "02_tomas", "03_recursos", "04_marca", "05_musica", "06_trabajo", "07_entrega"]


def slug(texto):
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:40] or "video"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", required=True)
    ap.add_argument("--solo-raiz", action="store_true")
    ap.add_argument("--nombre")
    ap.add_argument("--caso", choices=["cortar", "marca-personal", "marca"])
    ap.add_argument("--nivel", choices=["basico", "intermedio", "avanzado"], default="basico")
    ap.add_argument("--toma", help="Vídeo a copiar en 02_tomas/")
    a = ap.parse_args()

    raiz = Path(a.raiz).expanduser()
    for c in ["_mi-estilo/referencias", "_mi-estilo/logos", "_mi-estilo/tipografias", "_mi-estilo/efectos",
              "_recursos", "_tomas-sueltas", "proyectos"]:
        (raiz / c).mkdir(parents=True, exist_ok=True)
    if not (raiz / "LEEME.txt").exists():
        (raiz / "LEEME.txt").write_text(LEEME_RAIZ, encoding="utf-8")
    if a.solo_raiz:
        aviso(f"Carpeta lista: {raiz}")
        return

    if not (a.nombre and a.caso):
        raise SystemExit("Faltan --nombre y --caso")
    hoy = datetime.date.today().isoformat()
    proyecto = raiz / "proyectos" / f"{hoy}_{slug(a.nombre)}"
    for c in CARPETAS:
        (proyecto / c).mkdir(parents=True, exist_ok=True)
    (proyecto / "05_musica" / "efectos").mkdir(exist_ok=True)
    (proyecto / "LEEME.txt").write_text(LEEME_PROYECTO, encoding="utf-8")

    toma = None
    if a.toma:
        src = Path(a.toma).expanduser()
        if not src.exists():
            raise SystemExit(f"No existe la toma: {src}")
        destino = proyecto / "02_tomas" / src.name
        if src.resolve() != destino.resolve():
            shutil.copy2(src, destino)
        toma = str(destino)

    escribir_json(proyecto / "proyecto.json", {
        "nombre": a.nombre, "fecha": hoy, "caso": a.caso, "nivel": a.nivel,
        "toma": toma, "estilo": None, "formato": "pantalla-completa", "revision": None,
        "graficos": None, "musica": None, "red": None, "resolucion": "1080",
        "palabra_detras": False, "pasadas_hechas": [],
    })
    aviso(f"Proyecto creado: {proyecto}")
    print(proyecto)


if __name__ == "__main__":
    main()
