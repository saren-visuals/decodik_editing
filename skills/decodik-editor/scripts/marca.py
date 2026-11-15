"""Marca que se aplica a subtítulos y textos en pantalla (ver references/marca-decodik.md).

Orden de preferencia: lo que pida el talento (opciones de los scripts) → 06_entrega/trabajo/
marca.json (la marca del cliente en UGC, o la identidad del talento; lo escribe Claude) → la
marca DECODIK, que es la de por defecto. Solo biblioteca estándar.
"""

from __future__ import annotations

import json
from pathlib import Path

# Paleta DECODIK (sin blanco ni negro puros).
DECODIK = {
    "amarillo": "F7CE07", "amarillo_suave": "FFEF88", "amarillo_pildora": "FADE4E",
    "azul_noche": "010F20", "azul_medio": "0D2334", "azul_cielo": "ACD0DF",
    "menta": "5DD7B9", "menta_suave": "B9E8E4", "petroleo": "163843",
    "rosa": "FF5FA2", "rosa_suave": "F799C4",
    "crema": "F8F2E9", "papel": "F7F1E8", "tinta": "021020",
}

# Papeles que usan los scripts.
POR_DEFECTO = {
    "texto": DECODIK["crema"],        # texto general
    "contorno": DECODIK["tinta"],     # contorno y sombra del texto
    "clave": DECODIK["amarillo"],     # la palabra que destaca (una por subtítulo)
    "caja": DECODIK["crema"],         # fondo de cajas y etiquetas
    "texto_caja": DECODIK["tinta"],   # texto sobre una caja clara
    "acento2": DECODIK["menta"],      # segundo color, cuando un estilo necesita otro (Impacto)
}

# Letras de la marca: nombre interno (para los subtítulos) y archivo.
FUENTES = {
    "subtitulos": ("Figtree ExtraBold", "Figtree-ExtraBold.ttf"),
    "grande": ("Anton", "Anton-Regular.ttf"),
    "etiqueta": ("Bebas Neue", "BebasNeue-Regular.ttf"),
}


def cargar(trabajo: Path) -> dict:
    """Colores que mandan para este vídeo: DECODIK, con lo que diga marca.json encima."""
    colores = dict(POR_DEFECTO)
    f = trabajo / "marca.json"
    if f.exists():
        try:
            datos = json.loads(f.read_text(encoding="utf-8"))
            for k, v in (datos.get("colores") or {}).items():
                if k in colores and isinstance(v, str):
                    colores[k] = v.lstrip("#").upper()
        except json.JSONDecodeError:
            print(f"  ! {f.name} no es un JSON válido: se usa la marca DECODIK.")
    return colores


def origen(trabajo: Path) -> str:
    f = trabajo / "marca.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8")).get("origen") or "marca.json"
        except json.JSONDecodeError:
            pass
    return "marca DECODIK"
