"""Subtítulos en bloques animados (estilos con "motor": "bloques", p. ej. Neón lima).

Cada línea de frases.txt es un bloque de tres pisos:
  [palabras de antes, pequeñas, arriba a la izquierda]
  [PROTAGONISTA: la primera racha de *palabras clave*, enorme, en color y con resplandor]
  [palabras de después, pequeñas, abajo a la derecha]
Otras *claves* sueltas van pequeñas en el color de la protagonista y ~palabra~ se tacha.

Las palabras salen una a una en su arranque de voz y el bloque entero se asienta con una
curva exponencial (nace fuera de escala y se frena sin rebote). Como libass no tiene
curvas de este tipo ni escala de grupo, el .ass se escribe fotograma a fotograma durante
la animación y se juntan los fotogramas iguales en un solo evento.

Lo llama subtitulos.py; el .ass resultante se quema con quemar_subtitulos.py como siempre.
"""
import math
import os
import shutil
from pathlib import Path

from comun import SKILL, aviso

CARPETAS_FUENTES = [
    SKILL / "fonts",
    Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts",
    Path.home() / "Library" / "Fonts",
    Path("/Library/Fonts"),
    Path.home() / ".local" / "share" / "fonts",
    Path("/usr/share/fonts"),
]


def buscar_fuente(archivo):
    for carpeta in CARPETAS_FUENTES:
        if not str(carpeta) or not carpeta.exists():
            continue
        directo = carpeta / archivo
        if directo.exists():
            return directo
        for f in carpeta.rglob(archivo):
            return f
    return None


class Fuente:
    """Medidas de una fuente tal como las usa libass (tamaño ASS = ascendente + descendente de Windows)."""

    def __init__(self, ruta, familia):
        from fontTools.ttLib import TTFont
        from PIL import ImageFont
        t = TTFont(str(ruta), lazy=True)
        o, upm = t["OS/2"], t["head"].unitsPerEm
        alto = (o.usWinAscent + o.usWinDescent) or (t["hhea"].ascent - t["hhea"].descent)
        self.ruta, self.familia = Path(ruta), familia
        self.em_por_ass = upm / alto            # px de em por cada punto de tamaño ASS
        self.desc = o.usWinDescent / upm        # descendente (en em) por debajo de la línea base
        self.cap = (getattr(o, "sCapHeight", 0) or 700) / upm
        self._pil, self._ImageFont = {}, ImageFont

    def ancho(self, texto, tam_ass, interletraje_px=0.0):
        em = round(tam_ass * self.em_por_ass)
        if em not in self._pil:
            self._pil[em] = self._ImageFont.truetype(str(self.ruta), em)
        escala = tam_ass * self.em_por_ass / em
        return self._pil[em].getlength(texto) * escala + interletraje_px * max(len(texto) - 1, 0)


def color_bgr(hexa):
    h = hexa.lstrip("#")
    return f"&H{h[4:6]}{h[2:4]}{h[0:2]}&".upper()


def alfa(opacidad):
    return f"&H{max(0, min(255, round((1 - opacidad) * 255))):02X}&"


def t_ass(t):
    t = max(t, 0)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ease_out(p):
    p = min(max(p, 0.0), 1.0)
    return 1 - (1 - p) ** 3


def preparar_fuente(s, carpeta_out):
    """Busca la fuente del estilo (o la alternativa), la deja en <out>/_fuentes y devuelve sus medidas."""
    for fam, arch in ((s.get("fuente"), s.get("fuente_archivo")),
                      (s.get("fuente_alternativa"), s.get("fuente_alternativa_archivo"))):
        if not arch:
            continue
        ruta = buscar_fuente(arch)
        if ruta:
            destino = Path(carpeta_out) / "_fuentes"
            destino.mkdir(parents=True, exist_ok=True)
            if not (destino / ruta.name).exists():
                shutil.copy2(ruta, destino / ruta.name)
            if fam != s.get("fuente"):
                aviso(f"⚠️ No encuentro {s.get('fuente_archivo')}: uso {fam}.")
            return Fuente(ruta, fam)
    raise SystemExit(f"No encuentro la fuente {s.get('fuente_archivo')} ni la alternativa.")


# ---------------------------------------------------------------- bloques

# Palabras que nunca hacen de protagonista cuando el bloque no trae *clave*.
VACIAS = set("""a al algo ante así aun aunque bajo cada como con contra cual cuando de del desde donde
el ella ellas ellos en entre era eres es esa ese eso esta este esto está están estoy fue ha han has hay he
la las le les lo los me mi mis muy más ni no nos o os para pero por porque que qué se ser si sí sin
sobre son su sus también te ti tu tus tú un una uno unos unas va vas voy y ya yo""".split())

DETERMINANTES = set("el la los las un una unos unas mi mis tu tus su sus este esta ese esa nuestro nuestra".split())

VARIANTES = ("golpe", "empuje", "caida", "deriva", "lento")


def _rachas(tokens):
    """Rachas seguidas de *claves* dentro de una lista de palabras: [(inicio, fin), ...]."""
    rachas, i = [], 0
    while i < len(tokens):
        if tokens[i]["clave"]:
            j = i
            while j + 1 < len(tokens) and tokens[j + 1]["clave"]:
                j += 1
            rachas.append((i, j))
            i = j + 1
        else:
            i += 1
    return rachas


def _elegir_prota(tokens):
    """Primera racha de *claves*; si no hay, la palabra con más contenido (la más larga que no sea de enlace)."""
    rachas = _rachas(tokens)
    if rachas:
        return rachas[0], False
    candidatas = [i for i, x in enumerate(tokens) if x["texto"].lower() not in VACIAS] or list(range(len(tokens)))

    def puntos(i):  # detrás de un artículo o posesivo suele ir el sustantivo: «el skill», «las muletillas»
        tras_articulo = i > 0 and tokens[i - 1]["texto"].lower() in DETERMINANTES
        return (len(tokens[i]["texto"]) + (3 if tras_articulo else 0), -i)
    i = max(candidatas, key=puntos)
    return (i, i), True


def _cabe(tokens, s, palabras):
    if len(_rachas(tokens)) > 1:
        return False
    (a, b), _ = _elegir_prota(tokens)
    if a > s.get("palabras_arriba_max", 4) or len(tokens) - 1 - b > s.get("palabras_abajo_max", 4):
        return False
    idx = [x["idx"] for x in tokens if x.get("idx") is not None]
    if idx and palabras[max(idx)]["end"] - palabras[min(idx)]["start"] > s.get("bloque_max_s", 2.4):
        return False
    return True


def _coste(tokens, palabras):
    """Cuánto «cuesta» un bloque: cada bloque cuenta 1; sin *clave* propia, +0,8; de 1-2 palabras, +0,5;
    de menos de 0,7 s, +0,8; más de 4 palabras en una fila pequeña, +0,4 por cada una; más de 6 palabras,
    +0,3 por cada una (la referencia usa bloques de 3 a 7 palabras que duran 1-2 s)."""
    c = 1.0
    idx = [x["idx"] for x in tokens if x.get("idx") is not None]
    if idx and palabras[max(idx)]["end"] - palabras[min(idx)]["start"] < 0.7:
        c += 0.8
    if not _rachas(tokens):
        c += 0.8
    if len(tokens) <= 2:
        c += 0.5
    (a, b), _ = _elegir_prota(tokens)
    c += 0.4 * max(a - 4, 0) + 0.4 * max(len(tokens) - 1 - b - 4, 0)  # filas pequeñas largas
    return c + 0.3 * max(len(tokens) - 6, 0)


def _mejor_particion(trozos, s, palabras):
    """Reparte los trozos (|) de una línea en bloques que caben, con el menor coste total."""
    n = len(trozos)
    mejor = [0.0] + [float("inf")] * n
    corte = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(j):
            tokens = [x for t in trozos[i:j] for x in t["tokens"]]
            if j - i > 1 and not _cabe(tokens, s, palabras):
                continue
            c = mejor[i] + _coste(tokens, palabras)
            if c < mejor[j]:
                mejor[j], corte[j] = c, i
    grupos, j = [], n
    while j > 0:
        grupos.append(trozos[corte[j]:j])
        j = corte[j]
    return grupos[::-1]


def agrupar_bloques(validos, palabras, s):
    """Parte cada línea de frases.txt en bloques que caben como en la referencia (una protagonista,
    como mucho ~4 palabras arriba y ~4 abajo, ≤ 2,4 s), siempre por los | de los trozos."""
    frases, actual, frase = [], [], object()
    for t in validos:
        if actual and t.get("frase") != frase:
            frases.append(actual)
            actual = []
        frase = t.get("frase")
        actual.append(t)
    if actual:
        frases.append(actual)

    salida, avisos = [], []
    for trozos in frases:
        grupos = _mejor_particion(trozos, s, palabras)
        for g_i, g in enumerate(grupos):
            tokens = [x for t in g for x in t["tokens"]]
            ultimo = g[0]["start"]
            for x in tokens:  # momento en que aparece cada palabra: su arranque de voz
                if x.get("idx") is not None:
                    ultimo = max(ultimo, palabras[x["idx"]]["start"])
                x["t"] = ultimo
            (a, b), auto = _elegir_prota(tokens)
            if auto:
                avisos.append(f"«{' '.join(x['texto'] for x in tokens)}» no tiene *clave*: "
                              f"protagonista «{tokens[a]['texto']}» (márcala en frases.txt si prefieres otra)")
            salida.append({"tokens": tokens, "prota": (a, b), "start": g[0]["start"], "end": g[-1]["end"],
                           "end_voz": max(t["end_voz"] for t in g),
                           "variante": g[0].get("variante") if g_i == 0 else None})
    for k, b in enumerate(salida):  # el bloque se queda hasta el siguiente (salida en seco)
        if k + 1 < len(salida):
            sig = salida[k + 1]["start"]
            b["end"] = sig if sig - b["end_voz"] < 1.0 else max(b["end"], b["end_voz"] + 0.3)
    return salida, avisos


def elegir_variantes(bloques, rotacion):
    """Cada bloque entra distinto, como en la referencia. Reglas, en orden:
    [variante] al principio de la línea de frases.txt manda · primer bloque = golpe (gancho) ·
    bloque con tachado = caida · último bloque = lento · tras una pausa de ≥ 0,35 s = caida ·
    el resto rota sin repetir la del bloque anterior."""
    previa, r = None, 0
    for k, b in enumerate(bloques):
        v = b.get("variante")
        if v not in VARIANTES:
            pausa = k > 0 and b["start"] - bloques[k - 1]["end_voz"] >= 0.35
            if k == 0:
                v = "golpe"
            elif any(x.get("tachado") for x in b["tokens"]):
                v = "caida"
            elif k == len(bloques) - 1 and len(bloques) > 2 and previa != "lento":
                v = "lento"
            elif pausa and previa != "caida":
                v = "caida"
            else:
                v = rotacion[r % len(rotacion)]
                r += 1
                if v == previa or (v == "lento" and k == len(bloques) - 2):
                    v = rotacion[r % len(rotacion)]
                    r += 1
        b["variante"], previa = v, v


# ---------------------------------------------------------------- maquetación

def maquetar(bloque, s, F, ancho_lienzo):
    """Coloca cada palabra en su sitio final (escala 1), con las proporciones medidas en la referencia:
    - la protagonista ocupa entre el 62 % y el 86 % del ancho del vídeo;
    - las filas pequeñas caben SIEMPRE dentro del ancho de la protagonista (si no, la protagonista crece);
    - fila de arriba: sangrada un 15 % desde el borde izquierdo de la protagonista y montada un 12 % sobre sus mayúsculas;
    - fila de abajo: alineada a la derecha (5 % hacia dentro), separada un 24 % de la altura de mayúscula."""
    toks = bloque["tokens"]
    a, b = bloque["prota"]
    antes, prota, despues = toks[:a], toks[a:b + 1], toks[b + 1:]

    tp, tc0 = s["tamano"], s["clave_tamano"]
    ki = s.get("clave_interletraje", 0)
    textos_p = [x["texto"] for x in prota]
    if s.get("clave_inicial_mayuscula") and textos_p:
        textos_p[0] = textos_p[0][:1].upper() + textos_p[0][1:]
    texto_p = " ".join(textos_p)

    def ancho_prota(tc):
        return F.ancho(texto_p, tc, ki * tc * F.em_por_ass)

    def ancho_fila(tokens):
        return F.ancho(" ".join(x["texto"] for x in tokens), tp) if tokens else 0

    w0 = ancho_prota(tc0)
    minimo = s.get("clave_ancho_min", 0.62) * ancho_lienzo
    maximo = s.get("clave_ancho_max", 0.86) * ancho_lienzo
    # las filas pequeñas tienen que caber dentro de la protagonista (con su sangría)
    necesario = max(ancho_fila(antes) / 0.85, ancho_fila(despues) / 0.95, minimo)
    factor = min(max(necesario / w0, s.get("clave_escala_min", 0.8)), s.get("clave_escala_max", 1.75))
    if w0 * factor > maximo:
        factor = maximo / w0
    tc = tc0 * factor
    em_c = tc * F.em_por_ass
    sp = ki * em_c
    wk = ancho_prota(tc)
    cap_c = F.cap * em_c

    cx = s.get("centro_x", ancho_lienzo / 2)
    base_p = s.get("posicion_y", 1120) + cap_c / 2
    x0p, x1p = cx - wk / 2, cx + wk / 2
    margen = s.get("margen_x", 60)
    els = []

    def fila(tokens, x, base, tam, tipo, espaciado=0.0):
        hueco = F.ancho(" ", tam)
        for k, tok in enumerate(tokens):
            texto = textos_p[k] if tipo == "prota" else tok["texto"]
            w = F.ancho(texto, tam, espaciado)
            els.append({"texto": texto, "x": x, "base": base, "tam": tam, "sp": espaciado, "ancho": w,
                        "tipo": "prota" if tipo == "prota" else ("lima" if tok["clave"] else "peq"),
                        "t": tok["t"], "tachado": tok.get("tachado", False)})
            x += w + hueco

    fila(prota, x0p, base_p, tc, "prota", sp)
    cap_p = F.cap * tp * F.em_por_ass
    if antes:
        w = ancho_fila(antes)
        x = x0p + s.get("sangria_arriba", 0.15) * wk
        x = max(x0p, min(x, x1p - 0.03 * wk - w))
        if w > wk * 0.97:  # más ancha que la protagonista (ya al máximo): centrada sobre ella
            x = cx - w / 2
        x = min(max(x, margen), ancho_lienzo - margen - w)
        base = base_p - cap_c + s.get("solape_arriba", 0.12) * cap_c
        fila(antes, x, base, tp, "peq")
    if despues:
        w = ancho_fila(despues)
        x = max(x0p, x1p - s.get("sangria_abajo", 0.05) * wk - w)
        if w > wk * 0.97:
            x = cx - w / 2
        x = min(max(x, margen), ancho_lienzo - margen - w)
        base = base_p + s.get("hueco_abajo", 0.24) * cap_c + cap_p
        fila(despues, x, base, tp, "peq")
    return els, (cx, base_p - cap_c / 2)


# ---------------------------------------------------------------- animación

# Entrada de cada variante (medidas en la referencia):
#   escala inicial del bloque → 1 (curva exponencial con su vida media en s), desplazamiento vertical inicial → 0,
#   y cómo aparece cada palabra: (duración s, opacidad inicial, desenfoque inicial px).
#   golpe : nace grande y se frena (gancho, «Prospects»); la protagonista entra desenfocada.
#   empuje: nace algo pequeña, más abajo, y sube creciendo; la protagonista aparece seca («Understand»).
#   caida : cae desde arriba mientras se reduce (tras una pausa o con tachado, «Content»).
#   deriva: aparece seca y crece despacio durante 1 s («content matters»).
#   lento : casi sin zoom; cada palabra sube de opacidad desenfocada en 0,25 s (cierre, «Your plate»).
PERFILES = {
    "golpe":  {"escala": 1.22, "vida": 0.17, "dy": 0,   "prota": (0.08, 0.55, 12), "peq": (0.10, 0.0, 4)},
    "empuje": {"escala": 0.93, "vida": 0.12, "dy": 16,  "prota": (0.0, 1.0, 0),    "peq": (0.07, 0.0, 2)},
    "caida":  {"escala": 1.14, "vida": 0.12, "dy": -26, "prota": (0.10, 0.4, 10),  "peq": (0.10, 0.0, 4)},
    "deriva": {"escala": 0.97, "lineal_s": 1.0, "dy": 0, "prota": (0.0, 1.0, 0),   "peq": (0.05, 0.0, 0)},
    "lento":  {"escala": 1.03, "vida": 0.35, "dy": 0,   "prota": (0.25, 0.2, 10),  "peq": (0.18, 0.0, 6)},
}


def movimiento(variante, dt, primero):
    """Escala y desplazamiento vertical del bloque dt segundos después de que entre la protagonista."""
    perfil = PERFILES[variante]
    s0 = 1.30 if primero and variante == "golpe" else perfil["escala"]
    if "lineal_s" in perfil:
        p = min(max(dt / perfil["lineal_s"], 0), 1)
        return s0 + (1 - s0) * (1 - (1 - p) ** 1.6), 0.0
    esc = 1 + (s0 - 1) * math.pow(0.5, dt / perfil["vida"])
    dy = perfil["dy"] * math.pow(0.5, dt / (perfil["vida"] * 0.6))
    if abs(esc - 1) < 0.0015 and abs(dy) < 0.3:
        return 1.0, 0.0
    return esc, dy


def escribir_ass_bloques(validos, palabras, estilo, ruta, ancho, alto, fps=30):
    s = dict(estilo["subtitulos"])
    k = alto / (estilo.get("lienzo", {}).get("alto") or 1920)
    for clave in ("tamano", "clave_tamano", "posicion_y", "centro_x", "margen_x"):
        if clave in s:
            s[clave] = s[clave] * k
    F = preparar_fuente(s, Path(ruta).parent)
    brillo = s.get("resplandor", {})
    sombra = s.get("sombra_difusa", {})
    tach = s.get("tachado", {})
    c_peq, c_clave = color_bgr(s["color"]), color_bgr(s["clave_color"])

    bloques, avisos = agrupar_bloques(validos, palabras, s)
    elegir_variantes(bloques, s.get("rotacion_variantes", ["empuje", "deriva", "golpe", "lento"]))
    eventos = []  # (capa, inicio_fotograma, fin_fotograma, texto)

    for nb, bl in enumerate(bloques):
        els, (ax, ay) = maquetar(bl, s, F, ancho)
        perfil = PERFILES[bl["variante"]]
        f0, f1 = round(bl["start"] * fps), round(bl["end"] * fps)
        abiertos = {}

        def emitir(clave, capa, f, texto):
            ab = abiertos.get(clave)
            if ab and ab[1] == texto and ab[2] == f:
                ab[2] = f + 1
                return
            if ab:
                eventos.append((ab[0], ab[3], ab[2], ab[1]))
            abiertos[clave] = [capa, texto, f + 1, f]

        # El bloque espera en su posición de salida y se asienta cuando cae la protagonista (como «Prospects»):
        # así cada variante se ve en el golpe de la palabra importante y no se gasta en las pequeñas.
        t_golpe = min(e["t"] for e in els if e["tipo"] == "prota") - 0.03
        for f in range(f0, max(f1, f0 + 1)):
            t = f / fps
            esc, dy = movimiento(bl["variante"], max(t - t_golpe, 0.0), nb == 0)
            for n, e in enumerate(els):
                dt = t - e["t"]
                if dt < -1e-6:
                    continue
                dur, op0, bl0 = perfil["prota"] if e["tipo"] == "prota" else perfil["peq"]
                p = 1.0 if dur <= 0 else ease_out(dt / dur)
                op, bl_px = op0 + (1 - op0) * p, bl0 * (1 - p)
                if op <= 0.01:
                    continue
                # esquina inferior izquierda de la caja (línea base + descendente), escalada desde el ancla
                yb = e["base"] + F.desc * e["tam"] * F.em_por_ass
                x = ax + (e["x"] - ax) * esc
                y = ay + (yb - ay) * esc + dy
                comun = (f"\\an1\\pos({x:.1f},{y:.1f})\\fn{F.familia}\\fs{e['tam']:.1f}"
                         f"\\fscx{esc * 100:.2f}\\fscy{esc * 100:.2f}\\fsp{e['sp'] * esc:.2f}")
                color = c_peq if e["tipo"] == "peq" else c_clave
                texto = e["texto"].replace("{", "(").replace("}", ")")
                if e["tipo"] == "prota" and brillo:
                    emitir((n, "brillo"), 0, f,
                           f"{{{comun}\\1c{color_bgr(brillo['color'])}\\3c{color_bgr(brillo['color'])}"
                           f"\\bord{brillo.get('borde', 12) * esc:.1f}\\shad0\\blur{brillo.get('desenfoque', 22):.0f}"
                           f"\\alpha{alfa(brillo.get('opacidad', 0.4) * op)}}}{texto}")
                elif sombra:
                    emitir((n, "sombra"), 0, f,
                           f"{{{comun}\\1c{color_bgr(sombra['color'])}\\3c{color_bgr(sombra['color'])}"
                           f"\\bord{sombra.get('borde', 4) * esc:.1f}\\shad0\\blur{sombra.get('desenfoque', 14):.0f}"
                           f"\\alpha{alfa(sombra.get('opacidad', 0.5) * op)}}}{texto}")
                emitir((n, "texto"), 2, f,
                       f"{{{comun}\\1c{color}\\bord0\\shad0\\blur{bl_px:.1f}\\alpha{alfa(op)}}}{texto}")
                # tachado: trazo que crece de izquierda a derecha, ligeramente inclinado
                if e["tachado"] and tach:
                    p = ease_out((dt - tach.get("retraso_s", 0.13)) / tach.get("duracion_s", 0.33))
                    if p > 0:
                        cap = F.cap * e["tam"] * F.em_por_ass
                        xa, xb = e["x"] - 0.03 * e["ancho"], e["x"] + 1.03 * e["ancho"]
                        ym = e["base"] - cap * 0.5
                        incl = tach.get("inclinacion", 0.08) * (xb - xa)
                        xe = xa + (xb - xa) * p
                        ya, ye = ym - incl / 2, ym - incl / 2 + incl * p
                        g = tach.get("grosor", 11) / 2
                        pts = [(xa, ya - g), (xe, ye - g), (xe, ye + g), (xa, ya + g)]
                        pts = [(ax + (px - ax) * esc, ay + (py - ay) * esc + dy) for px, py in pts]
                        dibujo = " ".join(f"{px:.0f} {py:.0f}" for px, py in pts[1:])
                        emitir((n, "tachado"), 3, f,
                               f"{{\\an7\\pos(0,0)\\1c{color_bgr(tach.get('color', '#CC0826'))}\\bord0\\shad0"
                               f"\\blur0.6\\p1}}m {pts[0][0]:.0f} {pts[0][1]:.0f} l {dibujo}")
        for ab in abiertos.values():
            eventos.append((ab[0], ab[3], ab[2], ab[1]))

    cab = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {ancho}\nPlayResY: {alto}\nWrapStyle: 2\n"
           "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
           "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
           "MarginL, MarginR, MarginV, Encoding\n"
           f"Style: Bloque,{F.familia},{s['tamano']:.0f},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,"
           "100,100,0,0,1,0,0,1,0,0,0,1\n\n[Events]\n"
           "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    eventos.sort(key=lambda e: (e[1], e[0]))
    lineas = [f"Dialogue: {c},{t_ass(a / fps)},{t_ass(b / fps)},Bloque,,0,0,0,,{txt}" for c, a, b, txt in eventos]
    Path(ruta).write_text(cab + "\n".join(lineas) + "\n", encoding="utf-8")
    resumen = [f"{b['start']:5.2f}s  {b['variante']:6s}  {' '.join(x['texto'] for x in b['tokens'])}" for b in bloques]
    return len(bloques), len(eventos), F.familia, resumen, avisos
