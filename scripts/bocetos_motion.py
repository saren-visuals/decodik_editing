"""Bocetos SVG de los motions del formato «Explicativo con motion graphics · pantalla dividida».

Cada elemento se dibuja en el panel de arriba (lienzo 1080×960, centrado en x 540) con trazo fino (line art),
un solo color de acento y, como mucho una vez en el vídeo, el color negativo. Los mismos tipos y parámetros
sirven para el storyboard (fotogramas clave) y para construir la animación.

REGLA (vale para todo lo que lleve motion graphics): nada se solapa y todo cabe en pantalla y en la zona segura.
- Cada elemento sabe su caja (ancho × alto). Los textos se miden y se encogen para caber en su hueco.
- Los elementos de un fotograma se apilan en vertical, sin tocarse, y el conjunto se escala para caber en
  ZONA_PANEL: la banda común de TikTok, Reels y Shorts dentro del panel (x 192-888 centrado en 540, y 300-760,
  casi centrada en el panel; el centro óptico CENTRO_Y es también el centro de la luz del fondo).
- `panel_svg` devuelve también los avisos: texto que tendría que bajar de 26 px para caber (acórtalo),
  o un fotograma con demasiados elementos.

Tipos de elemento (en storyboard.json, dentro de "keyframes"[].elementos):
  {"tipo": "producto", "estado": "normal|tachado|apagado"}         el producto real (foto o recorte); aquí, su silueta
  {"tipo": "medidor", "valor": 0-1, "etiqueta": "EFECTO", "negativo": false}   arco con aguja (cualitativo)
  {"tipo": "molecula", "pareja": "GLICINA", "icono": "limon"|null, "simbolo": "Gly"}  esfera Mg²⁺ + enlace; pareja "?" late
  {"tipo": "iconos", "lista": [["mancuerna", "ENTRENAS DURO"], ["luna", "DUERMES"]], "on": 2}  iconos que se dibujan
  {"tipo": "fila", "n": 10, "on": 6, "etiqueta": "EL MÁS BARATO"}  siluetas en fila; se apagan todas menos una
  {"tipo": "ondas", "calma": 0-1, "etiqueta": "RELAJA"}            cerebro con ondas que se calman
  {"tipo": "barra", "valor": 0-1, "etiqueta": "CARGA"}             barra que se llena
  {"tipo": "gotas", "etiqueta": "AGUA AL INTESTINO"}               gotas que caen hacia el icono del intestino
  {"tipo": "comparativa", "opciones": ["A", "B"], "criterios": [["SUEÑO", 0.3, 0.9]], "ganadora": 1, "marco": true}
  {"tipo": "etiqueta", "texto": "EQUIVOCADO", "grande": true}      texto corto (Anton) con subrayado de acento
  {"tipo": "cadena", "pasos": [{"icono": "gota", "texto": "AGUA"}, {"icono": "intestino", "marca": "no"}], "flechas": true}
        LA PIEZA PRINCIPAL: una frase visual causa → efecto. Iconos en insignias unidos por flechas, con sello
        ✓ («si») o ✗ («no»), «acento» para el paso protagonista, «on»: false para los que aún no han entrado,
        «simbolo» («Gly») en vez de icono, y como mucho 1-2 palabras por paso. "flechas": false = lista sin causa.
Iconos de línea (ICONOS): mancuerna, luna, rayo, gota, cerebro, estomago, limon, bote, intestino, precio, molecula,
musculo, calendario, corazon, bateria. En la comparativa, un criterio puede ser un icono en vez de una palabra.
"""
import html
import math

from personajes_motion import POSES

E = html.escape
BLANCO = "#F2F2F2"
TENUE = "rgba(255,255,255,.35)"
ZONA_PANEL = dict(x0=192, x1=888, y0=300, y1=800)   # dentro del panel de 1080×960: zona segura y casi centrada (y 480 es el centro del panel)
CENTRO_Y = (ZONA_PANEL["y0"] + ZONA_PANEL["y1"]) / 2  # centro óptico del panel: ahí van el motion y la luz del fondo
SEPARACION = 40                                     # px entre elementos apilados
MARGEN = 12                                         # px de aire dentro de la zona segura
MIN_TEXTO = 26                                      # px reales: por debajo no se lee en el móvil


def ancho_texto(t, tam, anton=False, espaciado=0):
    """Ancho aproximado (las mayúsculas de Anton son estrechas; Figtree 700 es ancha)."""
    k = 0.50 if anton else 0.74   # por lo alto: mejor que sobre aire a que se pise
    return len(t) * (tam * k + espaciado)


class Lienzo:
    def __init__(self):
        self.avisos = []

    def texto(self, x, y, t, tam, hueco, color=BLANCO, anton=False, espaciado=None):
        """Texto centrado en x que se encoge hasta caber en `hueco` px. Devuelve (svg, tamaño usado)."""
        esp = 0 if anton else (espaciado if espaciado is not None else round(tam * 0.12))
        w = ancho_texto(t, tam, anton, esp)
        if w > hueco:
            f = hueco / w
            tam, esp = tam * f, esp * f
        fam, peso = ("Anton", 400) if anton else ("Figtree", 700)
        return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="middle" font-family="{fam}" font-weight="{peso}" '
                f'font-size="{tam:.1f}" letter-spacing="{esp:.1f}" fill="{color}">{E(t)}</text>'), tam


def icono(nombre, x, y, s=1.0, color=BLANCO, grosor=7):
    """Icono de línea centrado en (x, y): caja de unos 170×150 px a escala 1."""
    g = (f'<g transform="translate({x:.0f},{y:.0f}) scale({s})" fill="none" stroke="{color}" stroke-width="{grosor}" '
         f'stroke-linecap="round" stroke-linejoin="round">')
    d = {
        "mancuerna": '<rect x="-80" y="-34" width="22" height="68" rx="6"/><rect x="-56" y="-48" width="22" height="96" rx="6"/>'
                     '<rect x="34" y="-48" width="22" height="96" rx="6"/><rect x="58" y="-34" width="22" height="68" rx="6"/><line x1="-34" y1="0" x2="34" y2="0"/>',
        "luna": '<path d="M30,-62 A70,70 0 1,0 30,62 A54,54 0 1,1 30,-62 Z"/>',
        "rayo": '<path d="M14,-74 L-40,8 L0,8 L-14,74 L42,-12 L2,-12 Z"/>',
        "gota": '<path d="M0,-62 C30,-20 46,6 46,26 A46,46 0 0,1 -46,26 C-46,6 -30,-20 0,-62 Z"/>',
        "cerebro": '<path d="M-8,-60 C-50,-70 -82,-36 -70,-6 C-92,14 -74,52 -40,52 C-26,70 0,66 -8,40 Z"/>'
                   '<path d="M8,-60 C50,-70 82,-36 70,-6 C92,14 74,52 40,52 C26,70 0,66 8,40 Z"/>'
                   '<path d="M-44,-20 C-30,-10 -36,10 -20,14 M44,-20 C30,-10 36,10 20,14"/>',
        "estomago": '<path d="M-20,-70 C-20,-40 -60,-36 -60,10 C-60,58 -10,70 30,52 C70,34 60,-6 30,-10 C10,-12 4,-30 6,-70"/>',
        "limon": '<ellipse cx="0" cy="0" rx="72" ry="56"/><path d="M0,-56 L0,56 M-62,-26 L62,26 M-62,26 L62,-26"/>',
        "bote": '<rect x="-46" y="-56" width="92" height="124" rx="14"/><rect x="-36" y="-80" width="72" height="24" rx="6"/><line x1="-30" y1="0" x2="30" y2="0"/>',
        "intestino": '<path d="M-60,-40 H40 A20,20 0 0,1 40,0 H-40 A20,20 0 0,0 -40,40 H60"/>',
        "precio": '<path d="M-70,-20 L-20,-70 H60 V10 L10,60 Z"/><circle cx="34" cy="-44" r="9"/><path d="M8,-12 A22,22 0 1,0 8,22 M-34,-2 H6 M-34,12 H6"/>',
        "molecula": '<circle cx="-34" cy="0" r="30"/><circle cx="40" cy="-34" r="20"/><circle cx="40" cy="38" r="20"/><path d="M-6,-12 L22,-26 M-6,12 L22,28"/>',
        "musculo": '<path d="M-70,30 C-70,-10 -40,-50 -10,-60 C10,-66 20,-50 6,-38 C-6,-28 -20,-24 -24,-6 C0,-30 40,-30 60,-6 C76,14 64,50 30,54 C0,58 -40,56 -70,30 Z"/>',
        "calendario": '<rect x="-62" y="-52" width="124" height="112" rx="14"/><path d="M-62,-18 H62 M-30,-70 V-38 M30,-70 V-38"/><path d="M-36,8 H-20 M-8,8 H8 M20,8 H36 M-36,32 H-20 M-8,32 H8"/>',
        "bateria": '<rect x="-70" y="-40" width="128" height="80" rx="14"/><rect x="58" y="-16" width="14" height="32" rx="4"/><path d="M-4,-28 L-30,6 H-6 L-16,30 L16,-6 H-8 Z"/>',
        "corazon": '<path d="M0,56 C-60,14 -76,-14 -60,-38 C-44,-60 -14,-56 0,-30 C14,-56 44,-60 60,-38 C76,-14 60,14 0,56 Z"/>',
    }
    return g + d.get(nombre, '<circle r="50"/>') + "</g>"


ICONOS = ("mancuerna", "luna", "rayo", "gota", "cerebro", "estomago", "limon", "bote", "intestino", "precio",
          "molecula", "musculo", "calendario", "corazon", "bateria")


# Cada dibujo recibe el lienzo y devuelve (svg, ancho, borde de arriba, borde de abajo, [tamaños de texto usados]),
# con x centrada en 0. Los bordes son la caja real del dibujo: con ellos se apila sin solapes.

def _producto(L, el, ac, neg):
    estado = el.get("estado", "normal")
    op = ".35" if estado == "apagado" else "1"
    svg = (f'<g opacity="{op}"><animateTransform attributeName="transform" type="translate" values="0 0;0 -10;0 0" dur="3s" repeatCount="indefinite"/><rect x="-70" y="-110" width="140" height="210" rx="22" fill="url(#vidrio)" stroke="{BLANCO}" stroke-width="3"/>'
           f'<rect x="-54" y="-142" width="108" height="36" rx="8" fill="#d9d9d9"/>'
           f'<polygon points="-40,-110 -4,-110 -34,100 -70,100" fill="url(#brillo)"/></g>')
    if estado == "tachado":
        svg += f'<path d="M-110,-120 L110,110" stroke="{ac}" stroke-width="10" stroke-linecap="round"/>'
    return svg, 240, -145, 112, []


def _medidor(L, el, ac, neg):
    v = max(0.0, min(1.0, el.get("valor", 0.5)))
    col = neg if el.get("negativo") else ac
    r = 150
    ang = math.pi * (1 - v)
    nx, ny = r * 0.85 * math.cos(ang), -r * 0.85 * math.sin(ang)
    svg = f'<path d="M{-r},40 A{r},{r} 0 0,1 {r},40" fill="none" stroke="{TENUE}" stroke-width="14" stroke-linecap="round"/>'
    if v > 0.01:
        svg += (f'<path d="M{-r},40 A{r},{r} 0 0,1 {r * math.cos(ang):.1f},{40 - r * math.sin(ang):.1f}" fill="none" '
                f'stroke="{col}" stroke-width="14" stroke-linecap="round"/>')
    tiembla = "-3 0 40;4 0 40;-3 0 40" if v < .5 else "-6 0 40;2 0 40;-6 0 40"
    svg += (f'<g><animateTransform attributeName="transform" type="rotate" values="{tiembla}" dur="{.5 if v < .5 else .9}s" repeatCount="indefinite"/>'
            f'<line x1="0" y1="40" x2="{nx:.1f}" y2="{40 + ny:.1f}" stroke="{BLANCO}" stroke-width="6" stroke-linecap="round"/></g>'
            f'<circle cx="0" cy="40" r="12" fill="{BLANCO}"/>')
    t, tam = L.texto(0, 124, el.get("etiqueta", ""), 42, 380)
    return svg + t, 380, -115, 130, [tam]


def _molecula(L, el, ac, neg):
    pareja = el.get("pareja", "?")
    svg = (f'<circle cx="-170" cy="0" r="86" fill="url(#esfera)" stroke="{BLANCO}" stroke-width="3"/>'
           f'<text x="-170" y="18" text-anchor="middle" font-family="Anton" font-size="54" fill="{BLANCO}">Mg²⁺</text>'
           f'<line x1="-80" y1="0" x2="80" y2="0" stroke="{ac}" stroke-width="6" stroke-dasharray="4 14" stroke-linecap="round"/>')
    tams = []
    if pareja == "?":
        svg += (f'<circle cx="170" cy="0" r="86" fill="none" stroke="{TENUE}" stroke-width="4" stroke-dasharray="10 10"/>'
                f'<text x="170" y="28" text-anchor="middle" font-family="Anton" font-size="84" fill="{ac}">?</text>')
        return svg, 540, -90, 90, tams
    svg += f'<circle cx="170" cy="0" r="86" fill="rgba(255,255,255,.06)" stroke="{ac}" stroke-width="4"/>'
    if el.get("icono"):
        svg += icono(el["icono"], 170, -4, .7, BLANCO, 6)
    else:   # sin icono: su símbolo dentro de la esfera (Gly, Cit…), para que el hueco no quede vacío
        sim = el.get("simbolo", pareja[:3].title())
        svg += f'<text x="170" y="18" text-anchor="middle" font-family="Anton" font-size="54" fill="{BLANCO}">{E(sim)}</text>'
    t, tam = L.texto(0, 150, pareja, 32, 540)   # el nombre de la pareja, centrado debajo de toda la molécula
    return svg + t, 540, -90, 160, [tam]


def insignia(x, y, r, encendida, ac):
    """Círculo de cristal detrás de un icono: le da peso sin rellenar la pantalla de cosas."""
    borde = ac if encendida else "rgba(255,255,255,.18)"
    return (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="url(#esfera)" stroke="{borde}" stroke-width="3"/>'
            + (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r + 14}" fill="none" stroke="{ac}" stroke-opacity=".35" stroke-width="2">'
               f'<animate attributeName="r" values="{r + 4};{r + 30}" dur="2s" repeatCount="indefinite"/>'
               f'<animate attributeName="stroke-opacity" values=".5;0" dur="2s" repeatCount="indefinite"/></circle>' if encendida else ""))


def _iconos(L, el, ac, neg):
    lista = el.get("lista", [])
    n = max(1, len(lista))
    paso = (340 if n == 2 else 290) if n > 1 else 0
    on = el.get("on", n)
    svg, tams = "", []
    for k, (ic, et) in enumerate(lista):
        x = -paso * (n - 1) / 2 + k * paso
        t, tam = L.texto(x, 168, et, 34, (paso - 30) if n > 1 else 600)   # cada etiqueta en su columna: no se pisan
        tams.append(tam)
        svg += (f'<g opacity="{1 if k < on else .18}">' + insignia(x, 0, 100, k < on, ac)
                + icono(ic, x, 0, .75, BLANCO, 7) + t + "</g>")
    ancho = paso * (n - 1) + 260 if n > 1 else max(260, min(600, ancho_texto(lista[0][1], 34, False, 4)) if lista else 260)
    return svg, ancho, -118, 180, tams


def _fila(L, el, ac, neg):
    n, on = el.get("n", 10), el.get("on")
    paso = 76
    svg = ""
    for k in range(n):
        x = -paso * (n - 1) / 2 + k * paso
        col, op = (BLANCO, 1) if on is None else ((ac, 1) if k == on else (BLANCO, .2))
        svg += f'<g opacity="{op}">' + icono("bote", x, 0, .52, col, 9) + "</g>"
    ancho, abajo, tams = paso * (n - 1) + 76, 42, []
    if on is not None and el.get("etiqueta"):
        t, tam = L.texto(0, 120, el["etiqueta"], 32, ancho, ac)   # centrada bajo la fila, no bajo el bote: no se sale
        svg += t; abajo = 135; tams.append(tam)
    return svg, ancho, -46, abajo, tams


def _ondas(L, el, ac, neg):
    calma = el.get("calma", 0)
    amp = 40 * (1 - calma) + 6
    svg = icono("cerebro", 0, -60, 1.0, BLANCO, 6)
    for k, yy in enumerate((60, 95)):
        pts = " ".join(f"{-240 + i * 20},{yy + (amp if i % 2 else -amp) * (1 - k * .4):.0f}" for i in range(25))
        svg += f'<polyline points="{pts}" fill="none" stroke="{ac if k == 0 else TENUE}" stroke-width="5" stroke-linejoin="round"/>'
    t, tam = L.texto(0, 175, el.get("etiqueta", ""), 32, 520)
    return svg + t, 520, -130, 185, [tam]


def _barra(L, el, ac, neg):
    v, w = el.get("valor", .5), 560
    t, tam = L.texto(0, -45, el.get("etiqueta", ""), 38, w)
    svg = (f'<rect x="{-w / 2}" y="-22" width="{w}" height="44" rx="22" fill="none" stroke="{TENUE}" stroke-width="4"/>'
           f'<rect x="{-w / 2 + 8}" y="-14" width="{(w - 16) * v:.0f}" height="28" rx="14" fill="{ac}"/>')
    return t + svg, w, -75, 25, [tam]


def _gotas(L, el, ac, neg):
    svg = "".join(icono("gota", -110 + k * 110, -110 + (k % 2) * 30, .4, ac, 9) for k in range(3))
    svg += icono("intestino", 0, 30, 1.2, BLANCO, 8)
    t, tam = L.texto(0, 140, el.get("etiqueta", ""), 30, 520)
    return svg + t, 520, -140, 150, [tam]


def _comparativa(L, el, ac, neg):
    """Dos columnas (opción 1 a la izquierda, opción 2 a la derecha) y una calle central con el nombre de cada
    criterio. Las barras crecen desde la calle hacia fuera, así nunca tocan el texto del criterio."""
    ops, crit, g = el.get("opciones", ["A", "B"]), el.get("criterios", []), el.get("ganadora", 1)
    col, barra, centro, aire = 230, 160, 260, 16
    n = len(crit)
    cab, fila = 84, 92
    alto = cab + fila * n + 30
    arriba = -alto / 2
    svg, tams = "", []
    xs = (-(centro / 2 + col / 2), centro / 2 + col / 2)
    for k, o in enumerate(ops[:2]):
        t, tam = L.texto(xs[k], arriba + 58, o, 46, col - 30, ac if k == g else BLANCO, True)
        svg += t; tams.append(tam)
    for j, (nom, a, b) in enumerate(crit):
        y = arriba + cab + fila * j + fila / 2
        if nom in ICONOS:   # criterio dibujado: menos texto, se entiende igual
            svg += icono(nom, 0, y, .5, "rgba(255,255,255,.9)", 8)
        else:
            t, tam = L.texto(0, y + 11, nom, 30, centro - 2 * aire, "rgba(255,255,255,.8)")
            svg += t; tams.append(tam)
        for k, v in enumerate((a, b)):
            w = barra * v
            x0 = -centro / 2 - w if k == 0 else centro / 2
            svg += f'<rect x="{x0:.0f}" y="{y - 12:.0f}" width="{w:.0f}" height="24" rx="12" fill="{ac if k == g else TENUE}"/>'
    if el.get("marco"):
        x0 = centro / 2 - 12 if g == 1 else -(centro / 2 + col)
        svg += (f'<rect x="{x0:.0f}" y="{arriba:.0f}" width="{col + 12}" height="{alto}" rx="18" fill="none" '
                f'stroke="{ac}" stroke-width="4"/>')
    return svg, 2 * col + centro, arriba - 4, alto / 2 + 4, tams


def _etiqueta(L, el, ac, neg):
    t = el.get("texto", "")
    if el.get("grande"):
        s, tam = L.texto(0, 40, t, 150, 680, BLANCO, True)
        w = min(ancho_texto(t, tam, True), 680)
        return s + f'<rect x="{-w / 2:.0f}" y="70" width="{w:.0f}" height="10" rx="5" fill="{ac}"/>', 690, -tam * .55, 82, [tam]
    s, tam = L.texto(0, 12, t, 36, 680)
    return s, 690, -20, 20, [tam]


def _marca(x, y, tipo, ac):
    """Sello pequeño arriba a la derecha de una insignia: ✓ (sí) en el color de acento, ✗ (no) en gris."""
    if tipo == "si":
        return (f'<circle cx="{x}" cy="{y}" r="26" fill="{ac}"/>'
                f'<path d="M{x - 12},{y} L{x - 3},{y + 10} L{x + 13},{y - 9}" fill="none" stroke="#111" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>')
    if tipo == "no":
        return (f'<circle cx="{x}" cy="{y}" r="26" fill="#2a2d35" stroke="rgba(255,255,255,.5)" stroke-width="3"/>'
                f'<path d="M{x - 10},{y - 10} L{x + 10},{y + 10} M{x + 10},{y - 10} L{x - 10},{y + 10}" stroke="{BLANCO}" stroke-width="6" stroke-linecap="round"/>')
    return ""


def _cadena(L, el, ac, neg):
    """Una frase visual: icono → icono → icono. Cada paso: {"icono", "texto" (1-2 palabras, opcional),
    "marca": "si"|"no"|null, "on": true|false, "simbolo": "Gly" (texto en vez de icono)}.
    Las flechas se dibujan en el color de acento: cuentan qué provoca qué."""
    pasos = el.get("pasos", [])
    n = max(1, len(pasos))
    r = 92
    paso = {1: 0, 2: 340, 3: 280}.get(n, 230)
    svg, tams = "", []
    for k, p in enumerate(pasos):
        x = -paso * (n - 1) / 2 + k * paso
        on = p.get("on", True)
        g = f'<g opacity="{1 if on else .22}">' + insignia(x, 0, r, p.get("acento", False), ac)
        if p.get("simbolo"):
            g += f'<text x="{x:.0f}" y="20" text-anchor="middle" font-family="Anton" font-size="58" fill="{BLANCO}">{E(p["simbolo"])}</text>'
        else:
            g += icono(p.get("icono", "bote"), x, 0, .72, BLANCO, 7)
        g += _marca(x + r * .72, -r * .72, p.get("marca"), ac)
        if p.get("texto"):
            t, tam = L.texto(x, r + 62, p["texto"], 34, (paso - 30) if n > 1 else 520)
            g += t; tams.append(tam)
        svg += g + "</g>"
        if k < n - 1 and el.get("flechas", True):   # flecha hacia el siguiente paso; "flechas": false para una lista sin causa
            x1, x2 = x + r + 16, x + paso - r - 16
            if x2 - x1 > 20:
                svg += (f'<g opacity="{1 if pasos[k + 1].get("on", True) else .22}"><line x1="{x1:.0f}" y1="0" x2="{x2 - 8:.0f}" y2="0" stroke="{ac}" stroke-width="5" stroke-linecap="round" stroke-dasharray="14 10">'
                        f'<animate attributeName="stroke-dashoffset" values="24;0" dur=".8s" repeatCount="indefinite"/></line>'
                        f'<path d="M{x2 - 22:.0f},-13 L{x2:.0f},0 L{x2 - 22:.0f},13" fill="none" stroke="{ac}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></g>')
    abajo = r + 70 if any(p.get("texto") for p in pasos) else r + 8
    return svg, paso * (n - 1) + 2 * r + 40, -r - 36, abajo, tams



def _persona(L, el, ac, neg):
    """Personaje pictograma que hace lo que se cuenta (ver personajes_motion.py). Se mueve en bucle."""
    pose = el.get("pose", "entrena")
    svg = POSES.get(pose, POSES["entrena"])(ac)
    tams, abajo = [], 165
    if el.get("texto"):
        t, tam = L.texto(0, 210, el["texto"], 38, 420)
        svg += t; tams.append(tam); abajo = 222
    return svg, 360, -185, abajo, tams


DIBUJA = {"producto": _producto, "medidor": _medidor, "molecula": _molecula, "iconos": _iconos, "fila": _fila,
          "ondas": _ondas, "barra": _barra, "gotas": _gotas, "comparativa": _comparativa, "etiqueta": _etiqueta,
          "cadena": _cadena, "persona": _persona}


def fondo_premium(acento="#FFE600", uid="fp"):
    """Fondo premium del panel de arriba (1080×960), igual en todos los formatos explicativos. Capas, de atrás
    adelante: degradado negro azulado · halo suave del acento en el centro del motion · rejilla fina y trama de
    puntos que se desvanecen hacia los bordes · dos haces de luz diagonales muy tenues · partículas desenfocadas
    (bokeh) · grano de película · viñeta arriba (bajo la barra de la app) y hacia la costura.
    Todo es textura: nada lleva información ni compite con el motion. Nunca la toma de la persona."""
    import random
    rnd = random.Random(7)          # siempre las mismas partículas: el fondo no «baila» entre escenas
    cy = CENTRO_Y / 960
    z = ZONA_PANEL
    puntos = []
    while len(puntos) < 24:   # las partículas, solo alrededor: nunca debajo del motion ni de un texto
        x, y = rnd.uniform(30, 1050), rnd.uniform(60, 920)
        if z["x0"] - 20 < x < z["x1"] + 20 and z["y0"] - 20 < y < z["y1"] + 20:
            continue
        puntos.append((x, y))
    bokeh = "".join(
        f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice((3, 4, 6, 9, 14, 22)):.0f}" '
        f'fill="{acento if rnd.random() < .35 else "#ffffff"}" opacity="{rnd.uniform(.05, .16):.2f}" filter="url(#{uid}-des)"/>'
        for x, y in puntos)
    return (f'<defs><linearGradient id="{uid}-base" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#16181f"/>'
            f'<stop offset="1" stop-color="#07080b"/></linearGradient>'
            f'<radialGradient id="{uid}-halo" cx=".5" cy="{cy:.3f}" r=".55"><stop offset="0" stop-color="{acento}" stop-opacity=".12"/>'
            f'<stop offset=".55" stop-color="{acento}" stop-opacity=".03"/><stop offset="1" stop-color="{acento}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="{uid}-masc" cx=".5" cy="{cy:.3f}" r=".6"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>'
            f'<mask id="{uid}-m"><rect width="1080" height="960" fill="url(#{uid}-masc)"/></mask>'
            f'<pattern id="{uid}-rej" width="60" height="60" patternUnits="userSpaceOnUse"><path d="M60,0 H0 V60" fill="none" stroke="#fff" stroke-opacity=".06" stroke-width="1"/></pattern>'
            f'<pattern id="{uid}-pun" width="15" height="15" patternUnits="userSpaceOnUse"><circle cx="7.5" cy="7.5" r="1.3" fill="#fff" fill-opacity=".09"/></pattern>'
            f'<linearGradient id="{uid}-haz" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="#fff" stop-opacity=".04"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<filter id="{uid}-des" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>'
            f'<filter id="{uid}-grano" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="3" stitchTiles="stitch"/>'
            f'<feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .11 0"/></filter>'
            f'<filter id="{uid}-nubes" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".004 .008" numOctaves="3" seed="4"/>'
            f'<feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .07 -.01"/></filter>'
            f'<linearGradient id="{uid}-vin" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity=".65"/>'
            f'<stop offset=".28" stop-color="#000" stop-opacity="0"/><stop offset=".8" stop-color="#000" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity=".6"/></linearGradient>'
            f'<radialGradient id="{uid}-lat" cx=".5" cy="{cy:.3f}" r=".75"><stop offset=".6" stop-color="#000" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient></defs>'
            f'<rect width="1080" height="960" fill="url(#{uid}-base)"/>'
            f'<rect width="1080" height="960" filter="url(#{uid}-nubes)"/>'
            f'<rect width="1080" height="960" fill="url(#{uid}-halo)"/>'
            f'<rect width="1080" height="960" fill="url(#{uid}-rej)" mask="url(#{uid}-m)"/>'
            f'<rect width="1080" height="960" fill="url(#{uid}-pun)" mask="url(#{uid}-m)" opacity=".7"/>'
            f'<rect x="-200" y="200" width="1600" height="120" fill="url(#{uid}-haz)" transform="rotate(-24 540 480)"/>'
            f'<rect x="-200" y="430" width="1600" height="60" fill="url(#{uid}-haz)" transform="rotate(-24 540 480)"/>'
            f'{bokeh}'
            f'<rect width="1080" height="960" filter="url(#{uid}-grano)"/>'
            f'<rect width="1080" height="960" fill="url(#{uid}-lat)"/>'
            f'<rect width="1080" height="960" fill="url(#{uid}-vin)"/>')


def panel_svg(elementos, acento="#FFE600", negativo="#E50914", fondo=None, devolver_avisos=False, guia=False, titulo=None):
    """Un fotograma clave del panel de arriba (1080×960). Apila los elementos sin solaparse y escala el
    conjunto para que quepa en ZONA_PANEL. Con devolver_avisos=True devuelve (svg, avisos).
    titulo: rótulo pequeño de la escena arriba de la zona («01 · CITRATO»), con dos filetes del color de acento.
    Detrás del motion van dos órbitas finas (decoración, no cuentan para los solapes) para que el panel no
    se vea vacío sin añadir información."""
    L = Lienzo()
    piezas = [DIBUJA[e["tipo"]](L, e, acento, negativo) for e in elementos]
    zx = ZONA_PANEL["x1"] - ZONA_PANEL["x0"] - 2 * MARGEN
    zy = ZONA_PANEL["y1"] - ZONA_PANEL["y0"] - 2 * MARGEN
    alto_tit = 62 if titulo else 0
    zy -= alto_tit
    altos = [p[3] - p[2] for p in piezas]
    alto_total = sum(altos) + SEPARACION * (len(piezas) - 1)
    ancho_max = max((p[1] for p in piezas), default=1)
    esc = min(2.2, zx / ancho_max, zy / alto_total) if piezas else 1
    # Dos elementos estrechos (producto + medidor…) caben más grandes uno junto al otro que apilados.
    lado = False
    if len(piezas) == 2:
        ancho_lado = piezas[0][1] + piezas[1][1] + SEPARACION * 2
        esc_lado = min(2.2, zx / ancho_lado, zy / max(altos))
        if esc_lado > esc * 1.1:
            lado, esc = True, esc_lado
    y = ZONA_PANEL["y0"] + MARGEN + alto_tit + (zy - (max(altos) if lado else alto_total) * esc) / 2
    cy_motion = y + (max(altos) if lado else alto_total) * esc / 2
    capas, rotulo = "", ""
    if lado:
        x = 540 - ancho_lado * esc / 2
        for e, (svg, w, arriba, abajo, tams), h in zip(elementos, piezas, altos):
            cx = x + w * esc / 2
            capas += f'<g transform="translate({cx:.0f},{cy_motion - (arriba + h / 2) * esc:.0f}) scale({esc:.3f})">{svg}</g>'
            x += (w + SEPARACION * 2) * esc
            for t in tams:
                if t * esc < MIN_TEXTO:
                    L.avisos.append(f"texto de «{e['tipo']}» a {t * esc:.0f} px: acórtalo o quita un elemento del fotograma")
    if titulo:
        tt, tam_t = L.texto(540, ZONA_PANEL["y0"] + MARGEN + 34, titulo, 30, 420, acento)
        wt = min(ancho_texto(titulo, tam_t, False, tam_t * .12), 420)
        rotulo += tt + "".join(f'<line x1="{x1:.0f}" y1="{ZONA_PANEL["y0"] + MARGEN + 23}" x2="{x2:.0f}" y2="{ZONA_PANEL["y0"] + MARGEN + 23}" '
                              f'stroke="{acento}" stroke-opacity=".6" stroke-width="2"/>'
                              for x1, x2 in ((540 - wt / 2 - 70, 540 - wt / 2 - 18), (540 + wt / 2 + 18, 540 + wt / 2 + 70)))
        if tam_t < MIN_TEXTO:
            L.avisos.append(f"el título «{titulo}» no cabe: acórtalo")
    orbitas = (f'<g opacity=".9"><animateTransform attributeName="transform" type="rotate" values="0 540 {cy_motion:.0f};360 540 {cy_motion:.0f}" dur="60s" repeatCount="indefinite"/><circle cx="540" cy="{cy_motion:.0f}" r="300" fill="none" stroke="#fff" stroke-opacity=".06" stroke-width="2"/>'
               f'<circle cx="540" cy="{cy_motion:.0f}" r="390" fill="none" stroke="#fff" stroke-opacity=".04" stroke-width="2" stroke-dasharray="3 12"/>'
               f'<circle cx="{540 + 300 * .707:.0f}" cy="{cy_motion - 300 * .707:.0f}" r="6" fill="{acento}" fill-opacity=".7"/>'
               f'<circle cx="{540 - 390 * .94:.0f}" cy="{cy_motion + 390 * .34:.0f}" r="4" fill="#fff" fill-opacity=".35"/></g>')
    for e, (svg, w, arriba, abajo, tams), h in (() if lado else zip(elementos, piezas, altos)):
        capas += f'<g transform="translate(540,{y - arriba * esc:.0f}) scale({esc:.3f})">{svg}</g>'
        y += (h + SEPARACION) * esc
        for t in tams:
            if t * esc < MIN_TEXTO:
                L.avisos.append(f"texto de «{e['tipo']}» a {t * esc:.0f} px: acórtalo o quita un elemento del fotograma")
    if len(elementos) > 3:
        L.avisos.append(f"{len(elementos)} elementos en un fotograma: máximo 3")
    # fondo: «premium» (por defecto) o la ruta de una imagen si el usuario la pide expresamente
    import uuid
    uid = "fp" + uuid.uuid4().hex[:6]
    if fondo and fondo != "premium":
        bg = (f'<image href="{fondo}" x="0" y="-300" width="1080" height="1920" preserveAspectRatio="xMidYMid slice" opacity=".9"/>'
              f'<rect width="1080" height="960" fill="rgba(8,9,12,.72)"/>')
    else:
        bg = fondo_premium(acento, uid)
    defs = ('<defs><linearGradient id="vidrio" x1="0" x2="1"><stop offset="0" stop-color="#cfcfcf"/><stop offset=".45" stop-color="#ffffff"/><stop offset="1" stop-color="#a9a9a9"/></linearGradient>'
            '<linearGradient id="brillo" x1="0" x2="1"><stop offset="0" stop-color="rgba(255,255,255,0)"/><stop offset=".5" stop-color="rgba(255,255,255,.55)"/><stop offset="1" stop-color="rgba(255,255,255,0)"/></linearGradient>'
            '<radialGradient id="esfera" cx=".35" cy=".3"><stop offset="0" stop-color="rgba(255,255,255,.55)"/><stop offset=".6" stop-color="rgba(255,255,255,.08)"/><stop offset="1" stop-color="rgba(255,255,255,.02)"/></radialGradient></defs>')
    z = ZONA_PANEL
    marco = (f'<rect x="{z["x0"]}" y="{z["y0"]}" width="{z["x1"] - z["x0"]}" height="{z["y1"] - z["y0"]}" fill="none" '
             f'stroke="rgba(90,170,255,.7)" stroke-width="3" stroke-dasharray="12 10"/>') if guia else ""
    svg = f'<svg viewBox="0 0 1080 960" xmlns="http://www.w3.org/2000/svg">{defs}{bg}<g class="rotulo">{rotulo}</g><g class="contenido">{orbitas}{capas}</g>{marco}</svg>'
    return (svg, L.avisos) if devolver_avisos else svg
