# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""El estilo de edición del talento: lo aplica a este vídeo y lo guarda para los siguientes.

Uso:
    uv run estilo.py ver      <carpeta del vídeo>   ¿hay estilo guardado? Lo enseña en una tabla.
    uv run estilo.py aplicar  <carpeta del vídeo>   aplica el estilo de este vídeo y dice qué opciones usar.
    uv run estilo.py guardar  <carpeta del vídeo>   lo guarda como estilo del talento (estilo-talento.json).

De dónde sale el estilo de este vídeo (06_entrega/trabajo/estilo.json):
    1. si Claude lo ha escrito (desde un vídeo de referencia, o porque el talento pidió algo), ese;
    2. si no, el guardado en <carpeta del talento>/estilo-talento.json, y se copia aquí;
    3. si no hay ninguno, el estilo DECODIK por defecto.

«aplicar» escribe 06_entrega/trabajo/marca.json con los colores (para subtitulos.py y textos.py) y
lista las opciones de los demás pasos. Los colores se pasan al tono DECODIK más cercano, salvo que el
estilo diga "colores_exactos": true (el talento pidió un hex concreto).
Códigos: 0 bien · 1 estilo.json mal escrito · 2 no hay nada que guardar o ver.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import marca  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ESTILOS_SUB = ["clave", "serif", "frase", "impacto", "caja", "condensada", "mixta", "minimo"]
RECURSOS = ["tarjeta", "completo", "partida", "mixto"]
POR_DEFECTO = {
    "origen": "estilo DECODIK por defecto",
    "subtitulos": "clave",
    "colores": {},
    "colores_exactos": False,
    "pausa_max": 0.3,
    "gancho": True,
    "cifras": True,
    "cta": True,
    "recursos": "mixto",
    "encuadre": True,
    "notas": "",
}
NOMBRES = {v: k for k, v in marca.DECODIK.items()}


def rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# «Papel» es el fondo claro: para texto y colores de estilo se usa «Crema», casi igual.
CANDIDATOS = [v for k, v in marca.DECODIK.items() if k != "papel"]


def decodik_mas_cercano(h: str) -> str:
    r, g, b = rgb(h)
    return min(CANDIDATOS,
               key=lambda d: (rgb(d)[0] - r) ** 2 + (rgb(d)[1] - g) ** 2 + (rgb(d)[2] - b) ** 2)


def rutas(video: Path) -> tuple[Path, Path]:
    trabajo = video / "06_entrega" / "trabajo"
    return trabajo / "estilo.json", video.parent / "estilo-talento.json"


def leer(f: Path) -> dict:
    datos = json.loads(f.read_text(encoding="utf-8"))
    est = {**POR_DEFECTO, **datos}
    errores = []
    if est["subtitulos"] not in ESTILOS_SUB:
        errores.append(f"subtitulos «{est['subtitulos']}» no existe (valen: {', '.join(ESTILOS_SUB)})")
    if est["recursos"] not in RECURSOS:
        errores.append(f"recursos «{est['recursos']}» no existe (valen: {', '.join(RECURSOS)})")
    for k, v in (est.get("colores") or {}).items():
        if k not in marca.POR_DEFECTO:
            errores.append(f"color «{k}» no existe (valen: {', '.join(marca.POR_DEFECTO)})")
        elif not isinstance(v, str) or len(v.lstrip("#")) != 6:
            errores.append(f"color «{k}» debe ser un hex de 6 cifras")
    if not 0.1 <= float(est["pausa_max"]) <= 1.0:
        errores.append("pausa_max debe estar entre 0.1 y 1.0")
    if errores:
        raise ValueError("; ".join(errores))
    return est


def tabla(est: dict) -> str:
    col = est.get("colores") or {}
    clave = col.get("clave", marca.POR_DEFECTO["clave"]).lstrip("#").upper()
    texto = col.get("texto", marca.POR_DEFECTO["texto"]).lstrip("#").upper()
    ritmo = {0.2: "rápido", 0.3: "medio", 0.45: "pausado"}.get(round(float(est["pausa_max"]), 2),
                                                              f"pausas de {est['pausa_max']} s")
    textos = [n for n, k in (("gancho", "gancho"), ("cifras grandes", "cifras"), ("CTA", "cta")) if est[k]]
    filas = [
        ("Subtítulos", est["subtitulos"]),
        ("Palabra clave", f"#{clave} ({NOMBRES.get(clave, 'color propio')})"),
        ("Texto", f"#{texto} ({NOMBRES.get(texto, 'color propio')})"),
        ("Ritmo", ritmo),
        ("Textos en pantalla", ", ".join(textos) or "ninguno"),
        ("Recursos", est["recursos"]),
        ("Cambio de encuadre", "sí" if est["encuadre"] else "no"),
    ]
    out = ["| | |", "|---|---|"] + [f"| {a} | {b} |" for a, b in filas]
    if est.get("notas"):
        out.append(f"\nNotas: {est['notas']}")
    out.append(f"\n_Origen: {est.get('origen', '—')}_")
    return "\n".join(out)


def cmd_ver(video: Path) -> int:
    _, guardado = rutas(video)
    if not guardado.exists():
        print("Sin estilo guardado: pregunta por un vídeo de referencia o usa el estilo DECODIK.")
        return 2
    print("Estilo guardado del talento:\n")
    print(tabla(leer(guardado)))
    return 0


def cmd_aplicar(video: Path) -> int:
    propio, guardado = rutas(video)
    propio.parent.mkdir(parents=True, exist_ok=True)
    if propio.exists():
        fuente = "el estilo de este vídeo (estilo.json)"
    elif guardado.exists():
        shutil.copyfile(guardado, propio)
        fuente = "el estilo guardado del talento (estilo-talento.json)"
    else:
        propio.write_text(json.dumps(POR_DEFECTO, ensure_ascii=False, indent=2), encoding="utf-8")
        fuente = "el estilo DECODIK por defecto"
    try:
        est = leer(propio)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"estilo.json no es válido: {e}")
        return 1

    colores, cambios = {}, []
    for k, v in (est.get("colores") or {}).items():
        v = v.lstrip("#").upper()
        if not est.get("colores_exactos"):
            d = decodik_mas_cercano(v)
            if d != v:
                cambios.append(f"{k}: #{v} → #{d} ({NOMBRES[d]})")
            v = d
        colores[k] = v
    if cambios:   # el estilo queda ya en tonos DECODIK (y así se guarda)
        est["colores"] = colores
        datos = json.loads(propio.read_text(encoding="utf-8"))
        datos["colores"] = colores
        propio.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    marca_json = propio.parent / "marca.json"
    if colores:
        marca_json.write_text(json.dumps({"origen": f"estilo del talento ({est.get('origen', '')})",
                                          "colores": colores}, ensure_ascii=False, indent=2), encoding="utf-8")
    elif marca_json.exists() and "estilo del talento" in marca_json.read_text(encoding="utf-8"):
        marca_json.unlink()   # quedaba de un estilo anterior; vuelve la marca DECODIK

    print(f"Estilo aplicado: {fuente}.\n")
    print(tabla(est))
    for c in cambios:
        print(f"  · color pasado al tono DECODIK: {c}")
    print("\nOpciones para los pasos siguientes:")
    print(f"  5  cortar.py ... --pausa-max {est['pausa_max']}")
    print(f"  6  subtitulos.py ... --estilo {est['subtitulos']}" + ("  (colores en marca.json)" if colores else ""))
    print(f"  6 bis textos.json: gancho={'sí' if est['gancho'] else 'no'}, cifras={'sí' if est['cifras'] else 'no'}, "
          f"CTA={'sí' if est['cta'] else 'no'}")
    print(f"  6 ter recursos.json: modo preferido «{est['recursos']}»")
    print(f"  6 quater encuadre.py ...{'' if est['encuadre'] else ' --quitar'}")
    return 0


def cmd_guardar(video: Path) -> int:
    propio, guardado = rutas(video)
    if not propio.exists():
        print("Este vídeo no tiene estilo.json: ejecuta antes «estilo.py aplicar».")
        return 2
    try:
        est = leer(propio)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"estilo.json no es válido: {e}")
        return 1
    if guardado.exists():
        anterior = guardado.with_name("estilo-talento-anterior.json")
        shutil.copyfile(guardado, anterior)
        print(f"El estilo que tenía guardado queda en {anterior.name}, por si quiere volver a él.")
    est["guardado"] = date.today().isoformat()
    est["video"] = video.name
    guardado.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardado en {guardado.name}: los próximos vídeos saldrán con este estilo.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Estilo de edición del talento.")
    p.add_argument("accion", choices=["ver", "aplicar", "guardar"])
    p.add_argument("carpeta", type=Path, help="carpeta del vídeo")
    a = p.parse_args()
    video = a.carpeta.resolve()
    return {"ver": cmd_ver, "aplicar": cmd_aplicar, "guardar": cmd_guardar}[a.accion](video)


if __name__ == "__main__":
    sys.exit(main())
