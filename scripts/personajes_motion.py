"""Personaje en estilo pictograma deportivo para los motions explicativos (cabeza redonda maciza, extremidades
gruesas y redondeadas, accesorios en el color de acento). Ilustra lo que dice la persona del vídeo como si
fuera alguien de verdad: entrena, duerme mal, le da un calambre, compra, se calma, recupera…

Cada pose se dibuja centrada en x = 0 con los pies en y = 150 y se anima en bucle con SVG/SMIL
(el storyboard la enseña moviéndose). Al construir el vídeo, el mismo movimiento se pasa a GSAP.

Uso en storyboard.json:  {"tipo": "persona", "pose": "entrena", "texto": "ENTRENO DURO"}
Poses: entrena · duerme · calambre · compra · relajado · recupera · toma · corre
Caja: unos 340 × 330 px (con accesorios). La etiqueta (1-3 palabras) va debajo.
"""
BLANCO = "#F2F2F2"
G = 30   # grosor de las extremidades (pictograma: gruesas y redondeadas)


def _linea(puntos, extra=""):
    return f'<polyline points="{puntos}" fill="none" stroke="{BLANCO}" stroke-width="{G}" stroke-linecap="round" stroke-linejoin="round"{extra}/>'


def _anim_puntos(a, b, dur, extra=""):
    """Polilínea que va de la postura a a la b y vuelve (bucle suave)."""
    return (f'<polyline points="{a}" fill="none" stroke="{BLANCO}" stroke-width="{G}" stroke-linecap="round" stroke-linejoin="round"{extra}>'
            f'<animate attributeName="points" values="{a};{b};{a}" dur="{dur}s" repeatCount="indefinite" calcMode="spline" '
            f'keySplines=".45 0 .55 1;.45 0 .55 1"/></polyline>')


def _cabeza(x, y, r=32):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{BLANCO}"/>'


def _bote(x, y, s, ac):
    return (f'<g transform="translate({x},{y}) scale({s})"><rect x="-24" y="-30" width="48" height="66" rx="9" fill="{BLANCO}"/>'
            f'<rect x="-18" y="-44" width="36" height="14" rx="4" fill="{ac}"/></g>')


def entrena(ac):
    """Press por encima de la cabeza: la barra sube y baja."""
    bar = (f'<g><line x1="-118" y1="-78" x2="118" y2="-78" stroke="{ac}" stroke-width="12" stroke-linecap="round"/>'
           f'<rect x="-132" y="-104" width="20" height="52" rx="6" fill="{ac}"/><rect x="112" y="-104" width="20" height="52" rx="6" fill="{ac}"/>'
           f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -92;0 0" dur="1.6s" repeatCount="indefinite" '
           f'calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></g>')
    return (_linea("0,20 -32,86 -36,150") + _linea("0,20 32,86 36,150") + _linea("0,-74 0,20")
            + _anim_puntos("0,-66 -52,-28 -60,-78", "0,-66 -50,-116 -60,-170", 1.6)
            + _anim_puntos("0,-66 52,-28 60,-78", "0,-66 50,-116 60,-170", 1.6)
            + _cabeza(0, -110) + bar)


def duerme(ac):
    """En la cama, dando vueltas (duerme regular); las Z suben."""
    zs = "".join(f'<text x="{70 + k * 34}" y="{-20 - k * 40}" font-family="Anton" font-size="{40 + k * 10}" fill="{ac}" opacity="0">Z'
                 f'<animate attributeName="opacity" values="0;1;0" dur="2.4s" begin="{k * .6}s" repeatCount="indefinite"/>'
                 f'<animateTransform attributeName="transform" type="translate" values="0 10;0 -16" dur="2.4s" begin="{k * .6}s" repeatCount="indefinite"/></text>'
                 for k in range(3))
    cama = (f'<line x1="-160" y1="96" x2="160" y2="96" stroke="{BLANCO}" stroke-width="12" stroke-linecap="round"/>'
            f'<line x1="-160" y1="96" x2="-160" y2="30" stroke="{BLANCO}" stroke-width="12" stroke-linecap="round"/>'
            f'<line x1="-150" y1="96" x2="-150" y2="140" stroke="{BLANCO}" stroke-width="10" stroke-linecap="round"/>'
            f'<line x1="150" y1="96" x2="150" y2="140" stroke="{BLANCO}" stroke-width="10" stroke-linecap="round"/>')
    cuerpo = (f'<g>{_cabeza(-118, 52, 25)}'
              f'<rect x="-92" y="44" width="200" height="40" rx="20" fill="{ac}" fill-opacity=".35" stroke="{ac}" stroke-width="5"/>'
              f'<animateTransform attributeName="transform" type="rotate" values="0 0 80;-4 0 80;3 0 80;0 0 80" dur="2.2s" repeatCount="indefinite"/></g>')
    return cama + cuerpo + zs


def calambre(ac):
    """A la pata coja, agarrándose el gemelo; el rayo parpadea y el cuerpo tiembla."""
    rayo = (f'<path d="M78,70 L54,104 H72 L64,132 L94,94 H76 Z" fill="{ac}">'
            f'<animate attributeName="opacity" values="1;.15;1" dur=".5s" repeatCount="indefinite"/></path>')
    cuerpo = (_linea("-6,20 -14,86 -18,150") + _linea("-6,20 34,74 6,112") + _linea("0,-74 -6,20")
              + _linea("0,-64 30,-8 18,96") + _linea("0,-64 -44,-30 -72,-8") + _cabeza(6, -110))
    return (f'<g>{cuerpo}<animateTransform attributeName="transform" type="translate" values="0 0;-4 0;4 0;-3 0;0 0" '
            f'dur=".35s" repeatCount="indefinite"/></g>' + rayo)


def compra(ac):
    """Delante de la estantería, el brazo va hacia un bote y salta la etiqueta de precio."""
    estante = (f'<line x1="30" y1="-40" x2="170" y2="-40" stroke="{BLANCO}" stroke-width="8" stroke-linecap="round" opacity=".6"/>'
               f'<line x1="30" y1="40" x2="170" y2="40" stroke="{BLANCO}" stroke-width="8" stroke-linecap="round" opacity=".6"/>'
               + "".join(_bote(55 + k * 42, -72 + f * 80, .55, ac if (k, f) == (1, 1) else "#8a8f99") for k in range(3) for f in range(2)))
    etiqueta = (f'<g><path d="M96,-8 L118,-30 H150 V0 L128,22 Z" fill="{ac}"/>'
                f'<animateTransform attributeName="transform" type="scale" values="0;0;1.1;1;1;0" keyTimes="0;.35;.5;.6;.9;1" '
                f'dur="2.4s" repeatCount="indefinite" additive="sum"/></g>')
    persona = (_linea("-90,20 -118,86 -122,150") + _linea("-90,20 -62,86 -58,150") + _linea("-90,-74 -90,20")
               + _linea("-90,-64 -122,-20 -126,30")
               + _anim_puntos("-90,-64 -66,-20 -62,22", "-90,-64 -40,-40 14,-20", 2.4)
               + _cabeza(-90, -110))
    return estante + persona + f'<g transform="translate(0,0)">{etiqueta}</g>'


def relajado(ac):
    """Sentado en calma; las ondas sobre la cabeza se abren despacio."""
    ondas = "".join(f'<path d="M-60,{-150 - k * 22} Q0,{-180 - k * 22} 60,{-150 - k * 22}" fill="none" stroke="{ac}" stroke-width="6" '
                    f'stroke-linecap="round" opacity="0"><animate attributeName="opacity" values="0;.9;0" dur="3s" begin="{k}s" repeatCount="indefinite"/></path>'
                    for k in range(3))
    cuerpo = (_linea("-78,120 0,104 78,120") + _linea("0,-40 0,70") + _linea("0,-30 -44,20 -66,92")
              + _linea("0,-30 44,20 66,92") + _cabeza(0, -76))
    respira = (f'<g>{cuerpo}<animateTransform attributeName="transform" type="scale" values="1 1;1.02 1.03;1 1" '
               f'dur="3s" repeatCount="indefinite" additive="sum"/></g>')
    return f'<g transform="translate(0,30)">{respira}{ondas}</g>'


def recupera(ac):
    """Brazos arriba en V y, al lado, una batería que se carga."""
    bat = (f'<g transform="translate(118,-10)"><rect x="-50" y="-30" width="100" height="60" rx="12" fill="none" stroke="{BLANCO}" stroke-width="7"/>'
           f'<rect x="50" y="-12" width="10" height="24" rx="3" fill="{BLANCO}"/>'
           f'<rect x="-42" y="-22" width="0" height="44" rx="6" fill="{ac}"><animate attributeName="width" values="0;84;84" keyTimes="0;.75;1" '
           f'dur="2.4s" repeatCount="indefinite"/></rect></g>')
    persona = (_linea("-70,20 -98,86 -102,150") + _linea("-70,20 -42,86 -38,150") + _linea("-70,-74 -70,20")
               + _anim_puntos("-70,-64 -110,-30 -118,10", "-70,-64 -112,-120 -126,-160", 2.4)
               + _anim_puntos("-70,-64 -30,-30 -22,10", "-70,-64 -28,-120 -14,-160", 2.4)
               + _cabeza(-70, -110))
    return persona + bat


def toma(ac):
    """Se lleva el bote a la boca."""
    mano = (f'<g>{_bote(58, 30, .7, ac)}<animateTransform attributeName="transform" type="translate" values="0 0;-36 -118;-36 -118;0 0" '
            f'keyTimes="0;.4;.7;1" dur="2.6s" repeatCount="indefinite"/></g>')
    return (_linea("0,20 -32,86 -36,150") + _linea("0,20 32,86 36,150") + _linea("0,-74 0,20")
            + _linea("0,-64 -40,-20 -46,30")
            + _anim_puntos("0,-64 44,-20 52,26", "0,-64 40,-60 16,-92", 2.6)
            + _cabeza(0, -110) + mano)


def corre(ac):
    """Corriendo: brazos y piernas alternan."""
    return (_linea("0,-74 6,18")
            + _anim_puntos("6,18 46,74 30,146", "6,18 -30,80 -58,130", .7)
            + _anim_puntos("6,18 -30,80 -58,130", "6,18 46,74 30,146", .7)
            + _anim_puntos("0,-60 40,-30 64,-56", "0,-60 -36,-20 -50,20", .7)
            + _anim_puntos("0,-60 -36,-20 -50,20", "0,-60 40,-30 64,-56", .7)
            + _cabeza(10, -110))


POSES = {"entrena": entrena, "duerme": duerme, "calambre": calambre, "compra": compra, "relajado": relajado,
         "recupera": recupera, "toma": toma, "corre": corre}
