"""Elige qué tramo de cada recurso entra en cada plano (lo usan storyboard_historia.py y construir_historia.py).

- "in": "auto" (o sin "in") → el tramo de la duración del plano con MÁS ACTIVIDAD del clip (indice-recursos.json,
  de analizar_recursos.py), sin repetir un trozo ya usado del mismo clip en otro plano y evitando el primer medio
  segundo y el final (arranques y cámaras colocándose), y SIN CRUZAR un corte interno del clip (si no, la imagen
  cambia de golpe en mitad del plano) ni un barrido brusco de cámara (pico > 2,2 × la actividad normal del clip).
  Además el tramo tiene que ser un PLANO ESTABLE (el encuadre del principio, la mitad y el final casi igual,
  «huellas» de analizar_recursos.py): de los estables, el más activo; si todo el clip es cámara en movimiento, el
  más estable. Un número en "in" se respeta.
- "modo": "auto" (o sin "modo") → «recuadro» si el recurso es más ancho que 3:4 (horizontal: vídeo o foto),
  «completo» si es vertical. Así nunca se recorta una imagen horizontal y se pierden caras por los lados.
Determinista: storyboard y montaje eligen lo mismo.
"""
import json
from pathlib import Path

PASO = 0.5
MARGEN_INICIO = 0.5
MARGEN_FINAL = 0.3
ESTABLE = 18     # cambio de encuadre (0-255) entre principio, mitad y final del tramo por debajo del cual es un plano estable


def cargar_indice(proyecto):
    f = Path(proyecto) / "03_recursos" / "indice-recursos.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def _clave(src):
    return src.split("03_recursos/", 1)[-1]


def mejor_tramo(rec, dur, usados):
    act = rec.get("actividad") or []
    total = rec.get("duracion", 0)
    hi = total - dur - MARGEN_FINAL
    lo = min(MARGEN_INICIO, max(0.0, hi))
    if hi <= lo or not act:
        return max(0.0, min(lo, total - dur))
    cortes = list(rec.get("cortes") or [])
    # barridos bruscos de cámara: picos de más del doble de la actividad normal del clip. Se tratan como cortes:
    # queremos acción sostenida (la persona moviéndose), no un tirón de cámara.
    if act:
        normal = sorted(act)[len(act) // 2]
        cortes += [round(i * PASO + PASO / 2, 2) for i, v in enumerate(act) if normal > 0 and v > 2.2 * normal]
    hu = rec.get("huellas") or []

    def cambio(t0, t1):
        """Cuánto cambia el encuadre entre el principio, la mitad y el final del tramo (0 = idéntico)."""
        idx = [min(len(hu) - 1, int(x / PASO)) for x in (t0, (t0 + t1) / 2, t1)]
        if len(hu) < 2:
            return 0.0
        a, m, b = (hu[i] for i in idx)
        dif = lambda x, y: sum(abs(p - q) for p, q in zip(x, y)) / len(x)
        return max(dif(a, m), dif(m, b), dif(a, b))

    candidatos = []
    t = lo
    while t <= hi + 1e-6:
        # nunca un tramo que cruce un corte interno o un barrido (0,15 s de margen a cada lado) ni uno ya usado
        cruza = any(t - 0.15 < c < t + dur + 0.15 for c in cortes)
        if not cruza and not any(t < b and t + dur > a for a, b in usados):
            i0, i1 = int(t / PASO), max(int(t / PASO) + 1, int((t + dur) / PASO))
            v = sum(act[i0:i1]) / max(1, len(act[i0:i1]))
            candidatos.append((t, v, cambio(t, t + dur)))
        t += 0.25
    # 1) planos estables: el más activo (la persona moviéndose con el encuadre quieto)
    # 2) si todo el clip es cámara en movimiento: el tramo más estable (que no parezca una imagen cortada)
    estables = [c for c in candidatos if c[2] <= ESTABLE]
    if estables:
        mejor, mejor_v = max(estables, key=lambda c: c[1])[:2]
    elif candidatos:
        mejor, mejor_v = min(candidatos, key=lambda c: c[2])[:2]
    else:
        mejor, mejor_v = lo, -1.0
    if mejor_v < 0:        # todo el clip ya usado o troceado: primero se permite repetir; si aun así no hay, se ignoran los cortes
        if usados:
            return mejor_tramo(rec, dur, [])
        if cortes:
            return mejor_tramo(dict(rec, cortes=[]), dur, [])
    return round(mejor, 2)


def resolver(planos, proyecto, duracion_total):
    """Rellena en cada plano «in_usado» y «modo_usado» (sin tocar lo que escribió el editor)."""
    indice = cargar_indice(proyecto)
    usados = {}
    for k, p in enumerate(planos):
        t1 = planos[k + 1]["t0"] if k + 1 < len(planos) else duracion_total
        if p["tipo"] == "camara":
            continue
        rec = indice.get(_clave(p["src"]), {})
        modo = p.get("modo", "auto")
        if modo in ("auto", "foto", None):
            modo = "recuadro" if rec.get("orientacion") == "horizontal" else ("foto" if p["tipo"] == "foto" else "completo")
            if p["tipo"] == "foto" and modo == "completo":
                modo = "foto"
        p["modo_usado"] = modo
        if p["tipo"] == "broll":
            dur = t1 - p["t0"]
            ent = p.get("in", "auto")
            if ent in ("auto", None):
                ent = mejor_tramo(rec, dur, usados.get(_clave(p["src"]), []))
            p["in_usado"] = float(ent)
            usados.setdefault(_clave(p["src"]), []).append((p["in_usado"], p["in_usado"] + dur))
    return planos
