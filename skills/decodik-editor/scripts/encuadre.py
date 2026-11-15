# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy>=1.26", "opencv-python-headless>=4.9,<5"]
# ///
"""Cambio de encuadre en los cortes: un tramo en plano normal, el siguiente un poco más cerrado.

Uso:
    uv run encuadre.py <carpeta del vídeo> [--zoom 1.12] [--quitar]

En un vídeo hablado a cámara con el móvil fijo, cada corte es un salto con el mismo encuadre.
Alternar plano normal y plano cerrado hace que parezcan dos cámaras y que el corte se vea
buscado. El acercamiento se centra en la cara (detectada en cada tramo) para no cortar nunca la
cabeza ni sacar la cara del plano.

Escribe 06_entrega/trabajo/encuadre.json (lo usa render.py). --quitar lo borra (sin cambio de
encuadre). Códigos: 0 bien · 2 falta algo.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from recursos import ALTO, ANCHO, cara_en  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ZOOM = 1.12
TRAMO_MIN = 0.8   # tramos más cortos no cambian de encuadre (un salto así no se ve)


def ventana(cara: tuple[int, int, int, int] | None, zoom: float) -> tuple[int, int, int, int]:
    """Recorte (x, y, ancho, alto) de 1080×1920 que, ampliado, da el plano cerrado. Se acerca
    hacia la cara: el centro de la cara queda donde estaba, pero más grande. Sin cara: al centro,
    algo por encima (donde suele estar)."""
    w, h = round(ANCHO / zoom / 2) * 2, round(ALTO / zoom / 2) * 2
    if cara is None:
        cx, cy = ANCHO / 2, ALTO * 0.35
    else:
        x, y, cw, ch = cara
        cx, cy = x + cw / 2, y + ch / 2
    # Zoom hacia el punto de la cara: x0 = cx·(1 − 1/zoom).
    x0 = min(max(round(cx * (1 - 1 / zoom)), 0), ANCHO - w)
    y0 = min(max(round(cy * (1 - 1 / zoom)), 0), ALTO - h)
    if cara is not None:
        # Que no se corte la cabeza: el pelo (35 % del alto de la cara por encima) queda dentro.
        y0 = min(y0, max(0, round(cara[1] - 0.35 * cara[3])))
    return x0, y0, w, h


def main() -> int:
    p = argparse.ArgumentParser(description="Cambio de encuadre alterno, centrado en la cara.")
    p.add_argument("carpeta", type=Path, help="carpeta del vídeo")
    p.add_argument("--zoom", type=float, default=ZOOM, help=f"acercamiento del plano cerrado (por defecto {ZOOM})")
    p.add_argument("--quitar", action="store_true", help="sin cambio de encuadre")
    args = p.parse_args()

    video = args.carpeta.resolve()
    trabajo = video / "06_entrega" / "trabajo"
    salida = trabajo / "encuadre.json"
    if args.quitar:
        salida.unlink(missing_ok=True)
        print("Sin cambio de encuadre.")
        return 0
    if not (trabajo / "cortes.json").exists():
        print(f"Falta {trabajo / 'cortes.json'}. Antes ejecuta cortar.py.")
        return 2
    cortes = json.loads((trabajo / "cortes.json").read_text(encoding="utf-8"))
    brutos = video / "02_brutos"

    planos, cerrado = [], False
    for k, s in enumerate(cortes["segmentos"]):
        dura = s["salida_fin"] - s["salida_inicio"]
        if dura < TRAMO_MIN:
            planos.append(None)
            continue
        if cerrado:
            cara = cara_en(cortes, brutos, (s["salida_inicio"] + s["salida_fin"]) / 2)
            x0, y0, w, h = ventana(cara, args.zoom)
            planos.append({"x": x0, "y": y0, "ancho": w, "alto": h, "cara": cara is not None})
        else:
            planos.append(None)
        cerrado = not cerrado

    salida.write_text(json.dumps({"zoom": args.zoom, "tramos": planos}, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(1 for x in planos if x)
    sin_cara = sum(1 for x in planos if x and not x["cara"])
    print(f"{n} de {len(planos)} tramos en plano cerrado (×{args.zoom}), alternando con el plano normal."
          + (f" En {sin_cara} no se vio la cara: acercamiento al centro." if sin_cara else ""))
    print(f"  {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
