"""Intermedio/avanzado · Genera el proyecto HyperFrames (tipos premium: escena_texto, llamada, capitulo, final — ver referencias/graficos.md) (index.html + subcomposiciones) a partir de:
  - 06_trabajo/subtitulos/subtitulos.json  (de subtitulos.py)
  - 06_trabajo/plan.json                   (plan de gráficos aprobado; formato abajo)
  - el estilo elegido                      (estilos/<id>.json)

Uso:
  python construir_composicion.py --trabajo 06_trabajo --estilo <SKILL>/estilos/espacial.json --modo final [--res 1080|4k]
  python construir_composicion.py --trabajo 06_trabajo --estilo ... --modo detras     (avanzado: capa detrás de la cabeza)
Después:
  cd 06_trabajo/graficos && npx hyperframes check && npx hyperframes render . -o ../con_graficos.mp4
  (modo detras: npx hyperframes render . --format mov -o ../detras.mov)

plan.json:
{
  "ocultar_subtitulos": [[11.4, 18.7]],                 # opcional: tramos sin subtítulos
  "zooms": [{"t": 7.0, "a": 1.05, "dur": 1.6}],         # opcional: si no hay, se genera un punch-in en el gancho
  "graficos": [
    {"tipo": "tarjeta",  "ancla": "entrenamiento", "hasta": 4.6, "titulo": "Piernas", "texto": "3 series de 12"},
    {"tipo": "lista",    "t": 5.0, "hasta": 9.0, "titulo": "Lo que necesitas",
                         "items": [{"texto": "Banda", "ancla": "banda"}, {"texto": "Agua", "t": 7.2}]},
    {"tipo": "cifra",    "ancla": "cien", "hasta": 6.0, "valor": "100 %", "texto": "de intensidad"},
    {"tipo": "pildora",  "t": 0.2, "hasta": 2.0, "texto": "Día 1"},
    {"tipo": "titular",  "t": 0.0, "hasta": 1.6, "texto": "PIERNAS"},
    {"tipo": "imagen",   "ancla": "app", "hasta": 8.0, "src": "../../03_recursos/captura.png", "pie": "La app"},
    {"tipo": "broll",    "t": 10.0, "hasta": 12.0, "src": "../../03_recursos/sentadilla.mp4"},
    {"tipo": "escena",   "t": 12.0, "hasta": 18.0, "titulo": "El método", "items": [{"texto": "Fuerza", "t": 13}]},
    {"tipo": "cta",      "ancla": "sígueme", "hasta": 30.0, "texto": "Sígueme para más", "sub": "@usuario"},
    {"tipo": "palabra_detras", "t": 1.6, "hasta": 2.6, "texto": "100 %"}          # solo modo detras (avanzado)
  ]
}
"t" en segundos del vídeo cortado, o "ancla": una palabra de palabras.json (se usa su primer instante tras el gráfico anterior).
"posicion": "pecho" (por defecto, bajo la barbilla; oculta los subtítulos mientras está) | "arriba".
"mantener_subtitulos": true en la raíz del plan para no ocultarlos.
Rutas de imágenes y vídeos relativas a 06_trabajo/ o absolutas: se copian a graficos/assets/.
"""
import argparse
import html
import json
import shutil
from pathlib import Path

from comun import SKILL, aviso, error, escribir_json, leer_json, normalizar_palabra, sondear
from motions import css_panel, panel_motion

NL = "\n"
DUR_ENTRADA = {"espacial": 1.1, "golpe": 0.14, "editorial": 0.01, "minimal": 0.01, "premium": 0.2}
FUENTES = ["Figtree-SemiBold.ttf", "Figtree-Bold.ttf", "Figtree-Black.ttf", "Anton-Regular.ttf", "BebasNeue-Regular.ttf",
           "InstrumentSerif-Regular.ttf", "InstrumentSerif-Italic.ttf"]
EVENTOS = []  # (segundo, efecto) para efectos_sugeridos.json
GRANO = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/>"
         "<feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .09 0'/></filter>"
         "<rect width='100%' height='100%' filter='url(%23n)'/></svg>\")")


def esc(t):
    return html.escape(str(t))


ESTADO = {"ultimo_fondo": None, "n_escena": 0}


class Anclas:
    def __init__(self, palabras):
        self.p = palabras
        self.norm = [normalizar_palabra(w["w"]) for w in palabras]
        self.ultimo = 0.0

    def buscar(self, texto, desde, hasta=None):
        """Instante en que se dice `texto` entre `desde` y `hasta` (texto palabra a palabra).
        Si no se dice (una etiqueta que no está en la voz), entra 0,12 s después de la anterior."""
        obj = normalizar_palabra(texto)
        for w, n in zip(self.p, self.norm):
            if hasta is not None and w["start"] > hasta:
                break
            if w["start"] >= desde - 0.05 and n and (n == obj or (len(obj) > 3 and n.startswith(obj[:4]))):
                return w["start"]
        return None

    def t(self, g, defecto=None):
        if "t" in g:
            return float(g["t"])
        if "ancla" in g:
            obj = normalizar_palabra(g["ancla"].split()[0])
            for w, n in zip(self.p, self.norm):
                if n == obj and w["start"] >= self.ultimo - 0.05:
                    self.ultimo = w["start"]
                    return w["start"]
            for w, n in zip(self.p, self.norm):
                if n == obj:
                    return w["start"]
            error(f"No encuentro la palabra «{g['ancla']}» en palabras.json")
        if defecto is not None:
            return defecto
        error(f"El gráfico {g} necesita 't' o 'ancla'")


def css_base(e, K):
    """CSS común de las subcomposiciones, con la paleta Decodik y el estilo."""
    m = leer_json(SKILL / "marca" / "decodik.json")["colores"]
    s = e["subtitulos"]
    px = lambda n: f"{round(n * K)}px"
    # Banda horizontal: centrada en centro_x y lo más ancha posible sin salir de x 120-960.
    # 540 (por defecto, regla de Decodik) = todo centrado en pantalla.
    # 450 = banda 120-780, a la izquierda de la columna de botones de TikTok (si algún estilo lo pide).
    def banda(c):
        mitad = min(c - 120, 960 - c)
        return c - mitad, 1080 - (c + mitad)
    cap_izq, cap_der = banda(s.get("centro_x", 540))
    g_cx = e.get("graficos", {}).get("centro_x", s.get("centro_x", 540))
    g_izq, g_der = banda(g_cx)
    arriba_der = 192 if g_cx == 450 else g_der
    caja = s.get("clave_caja")
    clave_color = s["clave_color"]
    degradado = s.get("clave_degradado")
    clave_extra = (f"background: linear-gradient(90deg, {degradado[0]}, {degradado[1]}); -webkit-background-clip: text; "
                   f"background-clip: text; color: transparent;") if degradado else f"color: {clave_color};"
    if caja:
        clave_extra = f"color: {clave_color}; background: {caja}; padding: 0 {px(16)}; border-radius: {px(10)};"
    trazo = (f"-webkit-text-stroke: {px(s['grosor_contorno'])} {s.get('contorno', m['noche'])}; paint-order: stroke fill;"
             if s.get("grosor_contorno") else "")
    may = "text-transform: uppercase;" if s.get("mayusculas") else ""
    fuentes = "".join(
        f'@font-face {{ font-family: "{f}"; src: url("assets/fonts/{a}"); font-weight: {w}; }}\n        '
        for f, a, w in [("Figtree", "Figtree-SemiBold.ttf", 600), ("Figtree", "Figtree-Bold.ttf", 700),
                        ("Figtree", "Figtree-Black.ttf", 900), ("Anton", "Anton-Regular.ttf", 400),
                        ("Bebas Neue", "BebasNeue-Regular.ttf", 400),
                        ("Instrument Serif", "InstrumentSerif-Regular.ttf", 400)])
    peso = 900 if "Black" in s["fuente"] else 700 if "Bold" in s["fuente"] else 600
    fam = lambda nombre: '"Anton"' if "Anton" in nombre else '"Bebas Neue"' if "Bebas" in nombre else '"Instrument Serif"' if "Instrument" in nombre else '"Figtree"'
    return f"""
        {fuentes}
        .cap {{ position: absolute; left: {px(cap_izq)}; right: {px(cap_der)}; bottom: {px(1920 - 1210)};
               display: flex; align-items: flex-end; justify-content: center; text-align: center; }}
        .line {{ display: flex; flex-wrap: wrap; justify-content: center; align-items: baseline; gap: 0 {px(18)}; max-width: 100%; }}
        .w {{ display: inline-block; font-family: {fam(s['fuente'])}; font-weight: {peso}; font-size: {px(s['tamano'])}; line-height: 1.05;
              color: {s['color']}; {may} {trazo} text-shadow: 0 {px(3)} {px(12)} rgba(2,16,32,.65); }}
        .w.clave {{ font-family: {fam(s['clave_fuente'])}; font-weight: 400; font-size: {px(s['clave_tamano'])}; line-height: .95;
              text-shadow: none; filter: drop-shadow(0 {px(4)} {px(14)} rgba(2,16,32,.55)); {clave_extra} }}
        .ch {{ display: inline-block; }}
        .g {{ position: absolute; left: {px(g_izq)}; right: {px(g_der)}; display: flex; justify-content: center; }}
        .g.pecho {{ bottom: {px(690)}; align-items: flex-end; }}
        .g.arriba {{ top: {px(288)}; right: {px(arriba_der)}; }}
        .in {{ display: flex; flex-direction: column; align-items: center; }}
        .tarjeta {{ position: relative; overflow: hidden; max-width: {px(660)}; padding: {px(36)} {px(44)}; border-radius: {px(32)}; }}
        .t-titulo {{ font-family: "Anton"; font-size: {px(84)}; line-height: .95; }}
        .t-texto {{ font-family: "Figtree"; font-weight: 700; font-size: {px(46)}; line-height: 1.15; margin-top: {px(12)}; }}
        .lista-items {{ margin-top: {px(14)}; }}
        .item {{ display: flex; gap: {px(22)}; align-items: center; padding: {px(10)} 0; font-family: "Figtree"; font-weight: 700; font-size: {px(50)}; }}
        .check {{ width: {px(52)}; height: {px(52)}; border-radius: {px(14)}; display: grid; place-items: center;
                  font-weight: 900; font-size: {px(34)}; background: {m['menta']}; color: {m['noche']}; flex: none; }}
        .cifra-v {{ font-family: "Anton"; font-size: {px(230)}; line-height: .9; }}
        .cifra-t {{ font-family: "Figtree"; font-weight: 700; font-size: {px(52)}; margin-top: {px(8)}; }}
        .pildora {{ display: inline-flex; gap: {px(12)}; padding: {px(12)} {px(28)}; border-radius: 999px; font-family: "Figtree";
                    font-weight: 800; font-size: {px(36)}; letter-spacing: .06em; text-transform: uppercase;
                    background: rgba(93,215,185,.18); color: {m['menta']}; border: {px(2)} solid rgba(93,215,185,.45); }}
        .titular {{ font-family: "Anton"; font-size: {px(180)}; line-height: .9; text-transform: uppercase; white-space: nowrap; }}
        .imagen img {{ max-width: {px(640)}; max-height: {px(560)}; border-radius: {px(22)}; display: block; }}
        .pie {{ font-family: "Figtree"; font-weight: 700; font-size: {px(40)}; margin-top: {px(14)}; }}
        .broll {{ position: absolute; inset: 0; }}
        .broll video {{ width: 100%; height: 100%; object-fit: cover; }}
        .escena {{ position: absolute; inset: 0; background: radial-gradient(120% 80% at 50% 0%, {m['petroleo']}, transparent 62%), {m['noche']};
                   display: flex; flex-direction: column; justify-content: center; padding: {px(288)} {px(g_der)} {px(672)} {px(g_izq)}; }}
        .e-titulo {{ font-family: "Anton"; font-size: {px(140)}; line-height: .92; margin-bottom: {px(40)}; }}
        .escena .item {{ font-size: {px(64)}; padding: {px(18)} 0; color: {m['crema']}; }}
        .cta {{ display: flex; flex-direction: column; align-items: center; gap: {px(14)}; }}
        .cta-t {{ font-family: "Anton"; font-size: {px(92)}; line-height: .95; text-align: center; }}
        .cta-s {{ font-family: "Figtree"; font-weight: 700; font-size: {px(44)}; }}
        .flecha {{ font-size: {px(90)}; line-height: 1; }}
        .flash {{ position: absolute; inset: 0; background: #fff; }}
        .detras {{ position: absolute; left: 0; right: 0; top: {px(190)}; height: {px(500)}; display: flex; align-items: center; justify-content: center; }}
        .palabra-detras {{ font-family: "Anton"; font-size: {px(420)}; line-height: .9; white-space: nowrap; }}
"""


def css_estilo(e, K):
    m = leer_json(SKILL / "marca" / "decodik.json")["colores"]
    px = lambda n: f"{round(n * K)}px"
    grad = f"background: linear-gradient(90deg, {m['menta']}, {m['cian']}); -webkit-background-clip: text; background-clip: text; color: transparent;"
    if e["id"] == "espacial":
        return f"""
        .tarjeta {{ background: linear-gradient(160deg, rgba(37,75,87,.62), rgba(2,16,32,.62)); border: {px(2)} solid rgba(197,234,234,.25);
                   backdrop-filter: blur({px(24)}) saturate(1.3); -webkit-backdrop-filter: blur({px(24)}) saturate(1.3);
                   box-shadow: 0 {px(8)} {px(24)} rgba(93,215,185,.22), 0 {px(40)} {px(80)} -{px(30)} rgba(0,0,0,.7), inset 0 {px(2)} 0 rgba(255,255,255,.12); color: {m['crema']}; }}
        .tarjeta::before {{ content: ""; position: absolute; top: 0; left: 12%; right: 12%; height: {px(2)};
                   background: linear-gradient(90deg, transparent, rgba(126,222,227,.9), transparent); }}
        .t-titulo, .cifra-v, .titular, .e-titulo, .cta-t, .palabra-detras {{ {grad} }}
        .palabra-detras {{ background: linear-gradient(180deg, {m['cian']}, {m['menta']}); -webkit-background-clip: text; background-clip: text;
                   filter: drop-shadow(0 0 {px(40)} rgba(93,215,185,.35)); }}
        .cifra-t, .pie, .cta-s {{ color: {m['crema']}; }}
        .flecha {{ color: {m['menta']}; }}
        .imagen img {{ border: {px(3)} solid rgba(197,234,234,.35); box-shadow: 0 {px(8)} {px(24)} rgba(93,215,185,.22); }}"""
    if e["id"] == "editorial":
        return f"""
        .tarjeta {{ background: {m['crema']}; color: {m['noche']}; border-radius: {px(28)}; box-shadow: 0 {px(20)} {px(40)} rgba(2,16,32,.35); }}
        .t-titulo, .cta-t, .e-titulo {{ font-family: "Bebas Neue"; font-size: {px(110)}; color: {m['noche']}; }}
        .escena {{ background: {m['crema']}; }} .escena .item, .e-titulo {{ color: {m['noche']}; }}
        .cifra-v, .titular, .palabra-detras {{ font-family: "Bebas Neue"; color: {m['crema']}; text-shadow: 0 {px(6)} {px(24)} rgba(2,16,32,.5); }}
        .cifra-t, .pie {{ color: {m['crema']}; text-shadow: 0 {px(3)} {px(12)} rgba(2,16,32,.6); }}
        .cta {{ background: {m['crema']}; padding: {px(30)} {px(40)}; border-radius: {px(28)}; box-shadow: 0 {px(20)} {px(40)} rgba(2,16,32,.35); }}
        .cta-s {{ color: {m['petroleo']}; }} .flecha {{ color: {m['menta']}; }}
        .imagen img {{ border: {px(8)} solid {m['crema']}; box-shadow: 0 {px(20)} {px(40)} rgba(2,16,32,.4); }}
        .pildora {{ background: {m['crema']}; color: {m['noche']}; border-color: {m['menta']}; }}"""
    if e["id"] == "golpe":
        trazo = f"-webkit-text-stroke: {px(6)} {m['noche']}; paint-order: stroke fill;"
        return f"""
        .tarjeta {{ background: {m['noche']}; border: {px(4)} solid {m['amarillo']}; border-radius: {px(18)}; color: {m['crema']}; }}
        .t-titulo {{ color: {m['amarillo']}; text-transform: uppercase; }}
        .cifra-v, .titular, .cta-t, .e-titulo, .palabra-detras {{ color: {m['amarillo']}; text-transform: uppercase; {trazo} }}
        .cifra-t, .pie, .cta-s {{ color: {m['crema']}; text-transform: uppercase; {trazo} }}
        .check {{ background: {m['amarillo']}; }}
        .pildora {{ background: {m['amarillo']}; color: {m['noche']}; border-color: {m['amarillo']}; }}
        .flecha {{ color: {m['amarillo']}; }}"""
    if e["id"] == "premium":
        return f"""
        .tarjeta {{ background: {m['crema']}; color: {m['petroleo']}; border: {px(1)} solid rgba(37,75,87,.18); border-radius: {px(28)};
                   box-shadow: 0 {px(12)} {px(32)} rgba(2,16,32,.28); }}
        .t-titulo {{ font-family: "Instrument Serif"; font-size: {px(96)}; color: {m['petroleo']}; }}
        .cifra-v, .titular, .cta-t {{ font-family: "Instrument Serif"; color: {m['crema']}; text-shadow: 0 {px(4)} {px(18)} rgba(2,16,32,.5); }}
        .cifra-t, .pie, .cta-s {{ color: {m['crema']}; }} .check {{ background: {m['petroleo']}; color: {m['crema']}; }}
        .w.clave {{ filter: none; text-shadow: 0 {px(2)} {px(10)} rgba(2,16,32,.55); }}
        .w {{ text-shadow: 0 {px(2)} {px(10)} rgba(2,16,32,.55); }}
        .full {{ position: absolute; inset: 0; display: flex; align-items: center; padding: 0 {px(150)}; background-image: {GRANO}; }}
        .full.noche {{ background-color: {m['noche']}; }} .full.crema {{ background-color: {m['crema']}; }}
        .full .bloque {{ max-width: {px(780)}; }}
        .full.izq {{ justify-content: flex-start; text-align: left; }} .full.centro {{ justify-content: center; text-align: center; }}
        .full.der {{ justify-content: flex-end; text-align: right; }}
        .et {{ font-family: "Figtree"; font-weight: 700; font-size: {px(60)}; text-transform: uppercase; letter-spacing: .01em; line-height: 1.1; }}
        .sv {{ font-family: "Instrument Serif"; font-size: {px(200)}; line-height: .9; letter-spacing: -.01em; }}
        .l3 {{ font-family: "Figtree"; font-weight: 700; font-size: {px(44)}; text-transform: uppercase; margin-top: {px(14)}; }}
        .noche .et, .noche .l3 {{ color: {m['crema']}; }} .noche .sv {{ color: {m['cian']}; }}
        .crema .et, .crema .l3, .crema .sv {{ color: {m['petroleo']}; }}
        .pw {{ display: inline-block; margin-right: .24em; }}
        .acento {{ color: {m['rosa2']} !important; }}
        .barrido {{ position: absolute; inset: 0; }}
        .llamada {{ position: absolute; left: {px(120)}; top: {px(330)}; max-width: {px(380)}; }}
        .llamada .fr {{ font-family: "Figtree"; font-weight: 700; font-size: {px(34)}; color: {m['crema']}; text-shadow: 0 {px(2)} {px(10)} rgba(2,16,32,.6); }}
        .llamada .cj {{ display: inline-block; margin-top: {px(6)}; background: {m['menta']}; color: {m['noche']}; padding: {px(4)} {px(16)}; border-radius: {px(6)};
                        font-family: "Instrument Serif"; font-size: {px(72)}; line-height: 1.05; }}
        .final {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background-color: {m['noche']}; background-image: {GRANO};
                  font-family: "Figtree"; font-weight: 900; font-size: {px(64)}; letter-spacing: .04em; color: {m['crema']}; }}"""
    return f".tarjeta {{ background: rgba(2,16,32,.75); color: {m['crema']}; }}"


def animaciones(e):
    """Devuelve (entrada_grafico, salida_grafico, entrada_item) según el estilo."""
    if e["id"] == "espacial":
        return ('{ opacity: 0, y: 90, scale: .92, filter: "blur(18px)" }, { opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 1.1, ease: "back.out(1.7)" }',
                '{ opacity: 0, y: -40, filter: "blur(12px)", duration: 0.22, ease: "power2.in", overwrite: "auto" }',
                '{ opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 0.35, ease: "power3.out" }')
    if e["id"] == "premium":
        return ('{ opacity: 0, scale: .96, filter: "blur(10px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.2, ease: "power3.out" }',
                '{ opacity: 0, filter: "blur(8px)", duration: 0.15, ease: "power2.in", overwrite: "auto" }',
                '{ opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "power2.out" }')
    if e["id"] == "golpe":
        return ('{ opacity: 0, scale: 1.18 }, { opacity: 1, scale: 1, duration: 0.14, ease: "power4.out" }',
                '{ opacity: 0, duration: 0.06, overwrite: "auto" }',
                '{ opacity: 0, scale: 1.2 }, { opacity: 1, scale: 1, duration: 0.12, ease: "power4.out" }')
    return ('{ opacity: 0 }, { opacity: 1, duration: 0.01 }', '{ opacity: 0, duration: 0.01, overwrite: "auto" }',
            '{ opacity: 0 }, { opacity: 1, duration: 0.01 }')


def comp(id_, dur, W, H, css, cuerpo, js, tl):
    return f"""<!doctype html>
<html lang="es"><head><meta charset="UTF-8" /></head>
  <body>
    <template>
      <style>{css}
        #{id_}-root {{ position: absolute; inset: 0; }}
      </style>
      <div id="{id_}-root" data-composition-id="{id_}" data-width="{W}" data-height="{H}" data-duration="{dur:.3f}">
{cuerpo}
      </div>
      <script>
        const {tl} = gsap.timeline({{ paused: true }});
{js}        window.__timelines["{id_}"] = {tl};
      </script>
    </template>
  </body>
</html>
"""


def copiar_asset(src, trabajo, assets):
    p = Path(src)
    if not p.is_absolute():
        p = (trabajo / src).resolve()
    if not p.exists():
        error(f"No existe el recurso {src}")
    destino = assets / "recursos" / p.name
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, destino)
    return f"assets/recursos/{p.name}"


def subtitulos_comp(subs, e, ocultar, dur, W, H, css):
    s = e["subtitulos"]
    golpe, espacial, premium = e["id"] == "golpe", e["id"] == "espacial", e["id"] == "premium"
    clips, js = [], ""
    modos = ["chars", "words", "line"]
    for i, c in enumerate(subs):
        if any(c["start"] < b - 0.01 and c["end"] > a + 0.01 for a, b in ocultar):
            continue
        d = round(c["end"] - c["start"], 3)
        modo = modos[i % 3] if espacial else ("blur" if premium else "seco")
        spans = ""
        for k, w in enumerate(c["palabras"]):
            wid = f"w{i}-{k}"
            txt = w["texto"].upper() if s.get("mayusculas") else w["texto"]
            inner = "".join(f'<span class="ch">{esc(ch)}</span>' for ch in txt) if modo == "chars" and not w["clave"] else esc(txt)
            spans += f'<span id="{wid}" class="w{" clave" if w["clave"] else ""}">{inner}</span>'
            t = max(w["start"], c["start"])
            if w["clave"]:
                if golpe:
                    js += f'        ctl.fromTo("#{wid}", {{ scale: 1.15 }}, {{ scale: 1, duration: 0.12, ease: "power4.out" }}, {t:.3f});\n'
                elif espacial:
                    js += f'        ctl.fromTo("#{wid}", {{ opacity: 0, scale: 1.12, filter: "blur(14px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.45, ease: "power3.out" }}, {t:.3f});\n'
            elif modo == "chars":
                js += f'        ctl.fromTo("#{wid} .ch", {{ opacity: 0, y: 22 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: "power2.out", stagger: 0.022 }}, {t:.3f});\n'
            elif modo == "words":
                js += f'        ctl.fromTo("#{wid}", {{ opacity: 0, y: 28, filter: "blur(8px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.38, ease: "power3.out" }}, {t:.3f});\n'
        if modo == "blur":
            js += f'        ctl.fromTo("#cap-{i} .line", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.12, ease: "power2.out" }}, {c["start"]:.3f});\n'
        if modo == "line":
            js += f'        ctl.fromTo("#cap-{i} .line", {{ opacity: 0, y: 36, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.42, ease: "power3.out" }}, {c["start"]:.3f});\n'
        clips.append(f'        <div id="cap-{i}" class="cap clip" data-start="{c["start"]:.3f}" data-duration="{d}" data-track-index="1"><div class="line">{spans}</div></div>')
    return comp("captions", dur, W, H, css, NL.join(clips), js, "ctl")


def graficos_comp(plan, anclas, e, trabajo, assets, dur, W, H, css, ocupado):
    """`ocupado` recibe los tramos con un gráfico a la altura del pecho: ahí se ocultan los subtítulos."""
    entra, sale, item_in = animaciones(e)
    clips, js = [], ""
    n = 0
    for g in plan.get("graficos", []):
        tipo = g["tipo"]
        if tipo == "palabra_detras":
            continue
        n += 1
        gid = f"g{n}"
        t0 = anclas.t(g)
        t1 = float(g.get("hasta", t0 + 2.5))
        pos = g.get("posicion", "arriba" if tipo in ("titular", "pildora") else "pecho")
        if pos == "pecho" and tipo != "broll":
            ocupado.append([t0, t1])
        d = round(t1 - t0, 3)
        sub = ""
        if tipo == "tarjeta":
            cont = f'<div class="tarjeta"><div class="t-titulo">{esc(g.get("titulo", ""))}</div>' + (f'<div class="t-texto">{esc(g["texto"])}</div>' if g.get("texto") else "") + "</div>"
        elif tipo == "lista":
            items = ""
            for k, it in enumerate(g.get("items", [])):
                iid = f"{gid}-i{k}"
                ti = anclas.t(it, t0 + 0.4 + 0.5 * k)
                items += f'<div id="{iid}" class="item"><span class="check">✓</span><span>{esc(it["texto"])}</span></div>'
                sub += f'        gtl.fromTo("#{iid}", {item_in}, {ti:.3f});\n'
            cont = f'<div class="tarjeta">' + (f'<div class="t-titulo">{esc(g["titulo"])}</div>' if g.get("titulo") else "") + f'<div class="lista-items">{items}</div></div>'
        elif tipo == "cifra":
            cont = f'<div class="cifra-v">{esc(g["valor"])}</div>' + (f'<div class="cifra-t">{esc(g["texto"])}</div>' if g.get("texto") else "")
        elif tipo == "pildora":
            cont = f'<div class="pildora">{esc(g["texto"])}</div>'
        elif tipo == "titular":
            cont = f'<div class="titular">{esc(g["texto"])}</div>'
        elif tipo == "imagen":
            src = copiar_asset(g["src"], trabajo, assets)
            cont = f'<div class="imagen"><img src="{src}" alt="" />' + (f'<div class="pie">{esc(g["pie"])}</div>' if g.get("pie") else "") + "</div>"
        elif tipo == "broll":
            src = copiar_asset(g["src"], trabajo, assets)
            clips.append(f'        <div id="{gid}" class="broll clip" data-start="{t0:.3f}" data-duration="{d}" data-track-index="1">'
                         f'<video id="{gid}-v" class="clip" src="{src}" muted playsinline data-start="{t0:.3f}" data-duration="{d}" data-track-index="5"></video></div>')
            continue
        elif tipo == "escena":
            items = ""
            for k, it in enumerate(g.get("items", [])):
                iid = f"{gid}-i{k}"
                ti = anclas.t(it, t0 + 0.6 + 0.7 * k)
                items += f'<div id="{iid}" class="item"><span class="check">✓</span><span>{esc(it["texto"])}</span></div>'
                sub += f'        gtl.fromTo("#{iid}", {item_in}, {ti:.3f});\n'
            ocupado.append([t0, t1])
            clips.append(f'        <div id="{gid}" class="escena clip" data-start="{t0:.3f}" data-duration="{d}" data-track-index="1">'
                         f'<div class="e-titulo">{esc(g.get("titulo", ""))}</div>{items}</div>')
            js += f'        gtl.fromTo("#{gid}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25, ease: "power2.out" }}, {t0:.3f});\n' + sub
            continue
        elif tipo in ("escena_texto", "capitulo", "final"):
            fondo = g.get("fondo") or ("noche" if ESTADO["ultimo_fondo"] != "noche" else "crema")
            if tipo == "final":
                fondo = "noche"
            ESTADO["ultimo_fondo"] = fondo
            ali = g.get("alineacion") or ["izq", "centro", "der"][ESTADO["n_escena"] % 3]
            if tipo == "capitulo":
                ali = "centro"
            ESTADO["n_escena"] += 1
            ocupado.append([t0, t1])
            color_barrido = {"noche": "#254B57", "crema": "#021020"}[fondo]
            clips.append(f'        <div id="{gid}-b" class="barrido clip" style="background:{color_barrido}" data-start="{max(0, t0 - 0.11):.3f}" data-duration="0.22" data-track-index="3"></div>')
            js += f'        gtl.fromTo("#{gid}-b", {{ yPercent: 100 }}, {{ yPercent: -100, duration: 0.22, ease: "power2.inOut" }}, {max(0, t0 - 0.11):.3f});\n'
            EVENTOS.append((round(max(0, t0 - 0.14), 3), "whoosh"))
            if tipo == "final":
                clips.append(f'        <div id="{gid}" class="final clip" data-start="{t0:.3f}" data-duration="{d}" data-track-index="1">{esc(g.get("texto", "SIGUE PARA MÁS"))}</div>')
                continue
            lineas = g.get("lineas") or ([{"texto": g.get("etiqueta", "PARTE"), "rol": "etiqueta"}, {"texto": g.get("titulo", ""), "rol": "clave"}] if tipo == "capitulo" else [])
            html_l, cursor, previo = "", max(0, t0 - 0.8), t0
            for li, ln in enumerate(lineas):
                cls = {"etiqueta": "et", "clave": "sv", "linea3": "l3"}.get(ln.get("rol", "etiqueta"), "et")
                pal = ""
                for wi, wtxt in enumerate(ln["texto"].split()):
                    wid = f"{gid}-l{li}w{wi}"
                    hallado = None if tipo == "capitulo" else anclas.buscar(wtxt, cursor, t1)
                    if hallado is None:
                        tw = previo + (0.12 if (li or wi) else 0)
                    else:
                        tw = max(t0, hallado)
                        cursor = hallado + 0.01
                    tw = min(tw, max(t0, t1 - 0.3))
                    previo = tw
                    ac = " acento" if ln.get("acento") else ""
                    pal += f'<span id="{wid}" class="pw{ac}">{esc(wtxt)}</span>'
                    js += f'        gtl.fromTo("#{wid}", {item_in}, {tw:.3f});\n'
                    if cls == "sv" and wi == 0:
                        EVENTOS.append((round(max(0, tw - 0.02), 3), "uiclick"))
                html_l += f'<div class="{cls}">{pal}</div>'
            clips.append(f'        <div id="{gid}" class="full {fondo} {ali} clip" data-start="{t0:.3f}" data-duration="{d}" data-track-index="1"><div class="bloque">{html_l}</div></div>')
            if tipo == "capitulo":
                EVENTOS.append((round(t0, 3), "impact"))
            continue
        elif tipo == "llamada":
            fr = f'<div class="fr">{esc(g.get("frase", ""))}</div>' if g.get("frase") else ""
            clips.append(f'        <div id="{gid}" class="llamada clip" data-start="{t0:.3f}" data-duration="{d}" data-track-index="1"><div class="in">{fr}<div class="cj">{esc(g["clave"])}</div></div></div>')
            js += f'        gtl.fromTo("#{gid} .in", {entra}, {t0:.3f});\n'
            if t1 < dur - 0.05:
                js += f'        gtl.to("#{gid} .in", {sale}, {max(t0 + 0.2, t1 - 0.15):.3f});\n'
            EVENTOS.append((round(max(0, t0 - 0.02), 3), "uiclick"))
            continue
        elif tipo == "cta":
            cont = f'<div class="cta"><div class="cta-t">{esc(g["texto"])}</div>' + (f'<div class="cta-s">{esc(g["sub"])}</div>' if g.get("sub") else "") + f'<div id="{gid}-f" class="flecha">↓</div></div>'
            sub += f'        gtl.fromTo("#{gid}-f", {{ y: 0 }}, {{ y: -22, duration: 0.45, ease: "sine.inOut", yoyo: true, repeat: {max(1, int(d / 0.45) - 1)} }}, {t0 + 0.4:.3f});\n'
        else:
            error(f"Tipo de gráfico desconocido: {tipo}")
        clips.append(f'        <div id="{gid}" class="g {pos} clip" data-start="{t0:.3f}" data-duration="{d}" data-track-index="1"><div class="in">{cont}</div></div>')
        js += f'        gtl.fromTo("#{gid} .in", {entra}, {t0:.3f});\n' + sub
        if t1 < dur - 0.05:
            js += f'        gtl.to("#{gid} .in", {sale}, {max(t0 + DUR_ENTRADA[e["id"]], t1 - 0.22):.3f});\n'
    if e["id"] == "golpe":
        clips.append('        <div id="flash" class="flash clip" data-start="0" data-duration="0.12" data-track-index="2"></div>')
        js += '        gtl.fromTo("#flash", { opacity: 0.9 }, { opacity: 0, duration: 0.1, ease: "none" }, 0);\n'
    return comp("graphics", dur, W, H, css, NL.join(clips), js, "gtl")


def detras_comp(plan, anclas, e, dur, W, H, css):
    entra, sale, _ = animaciones(e)
    clips, js = [], ""
    for n, g in enumerate([g for g in plan.get("graficos", []) if g["tipo"] == "palabra_detras"], 1):
        t0 = anclas.t(g)
        t1 = float(g.get("hasta", t0 + 1.2))
        clips.append(f'        <div id="b{n}" class="detras clip" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="1">'
                     f'<div class="in"><div class="palabra-detras">{esc(g["texto"])}</div></div></div>')
        js += f'        btl.fromTo("#b{n} .in", {entra}, {t0:.3f});\n'
        if t1 < dur - 0.05:
            js += f'        btl.to("#b{n} .in", {sale}, {max(t0 + DUR_ENTRADA[e["id"]], t1 - 0.22):.3f});\n'
    if not clips:
        error("El plan no tiene ningún gráfico de tipo palabra_detras.")
    return comp("behind", dur, W, H, css, NL.join(clips), js, "btl")


FORMATOS = ("pantalla-completa", "pantalla-dividida", "recuadro")


def css_formato(formato, K):
    """Ajustes de posición por formato (se añaden al final del CSS: mandan sobre los del estilo)."""
    px = lambda n: f"{round(n * K)}px"
    if formato == "pantalla-dividida":
        # Arriba (0-768) recursos y gráficos; abajo (768-1920) la persona; subtítulos en la costura.
        return f"""
        .g.pecho {{ top: {px(288)}; bottom: auto; height: {px(450)}; align-items: center; }}
        .cap {{ bottom: {px(1920 - 768 - 48)}; }}
"""
    if formato == "recuadro":
        # Persona en un recuadro centrado arriba (405-675 × 288-768); gráficos o motions debajo (y 800-1248).
        # Subtítulos sobre el pecho, en la parte baja del recuadro, para dejar libre la franja de abajo.
        return f"""
        .g.pecho {{ top: {px(800)}; bottom: {px(1920 - 1248)}; align-items: center; }}
        .cap {{ bottom: {px(1920 - 760)}; }}
"""
    return ""


def zooms_js(plan, e, dur):
    zmax = 1 + float(e.get("ritmo", {}).get("zoom_max", 0) or 0)
    if zmax <= 1:
        return ""
    lista = plan.get("zooms")
    if lista is None:
        lista = [{"t": 0.0, "de": min(zmax, 1.06), "a": 1.0, "dur": 1.4, "ease": "power3.out"}]
    out, actual = "", 1.0
    for z in lista:
        de = z.get("de", actual)
        a = min(float(z["a"]), zmax)
        if out:  # tras el primero, .to() parte del estado real: sin saltos al buscar
            out += f'      tl.to("#zoom", {{ scale: {a}, duration: {z.get("dur", 1.6)}, ease: "{z.get("ease", "power2.inOut")}" }}, {z["t"]});\n'
        else:
            out += f'      tl.fromTo("#zoom", {{ scale: {de} }}, {{ scale: {a}, duration: {z.get("dur", 1.6)}, ease: "{z.get("ease", "power2.inOut")}" }}, {z["t"]});\n'
        actual = a
    return out


def css_index_formato(formato, W, H):
    K = W / 1080
    px = lambda n: f"{round(n * K)}px"
    if formato == "pantalla-dividida":
        return f"""      #panel-persona {{ position: absolute; left: 0; top: {px(768)}; width: 100%; height: {px(1152)}; overflow: hidden; }}
      #panel-persona #base {{ object-position: 50% 22%; }}
      #panel-persona::before {{ content: ""; position: absolute; left: 0; right: 0; top: 0; height: {px(4)}; background: #5DD7B9; z-index: 2; }}"""
    if formato == "recuadro":
        return f"""      #fondo {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
      #panel-persona {{ position: absolute; left: {px(405)}; top: {px(288)}; width: {px(270)}; height: {px(480)}; overflow: hidden;
                        border-radius: {px(32)}; border: {px(4)} solid #5DD7B9; box-shadow: 0 {px(10)} {px(40)} rgba(2,16,32,.55); }}
      #panel-persona #zoom {{ transform: none; }}
      #panel-persona #base {{ object-position: 50% 20%; }}"""
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trabajo", required=True)
    ap.add_argument("--estilo", required=True)
    ap.add_argument("--modo", choices=["final", "detras"], default="final")
    ap.add_argument("--formato", choices=FORMATOS,
                    help="pantalla-completa (por defecto), pantalla-dividida o recuadro. También vale \"formato\" en plan.json")
    ap.add_argument("--res", choices=["1080", "4k"], default="1080")
    ap.add_argument("--base", help="Vídeo base (por defecto 06_trabajo/cortado.mp4, o graficos/assets/base.mp4 si existe)")
    a = ap.parse_args()

    tr = Path(a.trabajo).resolve()
    e = leer_json(a.estilo)
    W, H = (2160, 3840) if a.res == "4k" else (1080, 1920)
    K = W / 1080
    gdir = tr / "graficos"
    assets = gdir / "assets"
    (assets / "fonts").mkdir(parents=True, exist_ok=True)
    (gdir / "compositions").mkdir(exist_ok=True)
    for f in FUENTES:
        shutil.copy2(SKILL / "fonts" / f, assets / "fonts" / f)
    shutil.copy2(SKILL / "plantillas" / "hyperframes" / "gsap.min.js", assets / "gsap.min.js")

    plan = leer_json(tr / "plan.json") if (tr / "plan.json").exists() else {"graficos": []}
    palabras = leer_json(tr / "palabras.json")
    anclas = Anclas(palabras)
    base = Path(a.base) if a.base else (assets / "base.mp4" if (assets / "base.mp4").exists() else tr / "cortado.mp4")
    if base.resolve() != (assets / "base.mp4").resolve():
        shutil.copy2(base, assets / "base.mp4")
    dur = round(sondear(assets / "base.mp4")["duracion"], 3)
    formato = a.formato or plan.get("formato", "pantalla-completa")
    if formato not in FORMATOS:
        error(f"Formato desconocido: {formato}. Usa {', '.join(FORMATOS)}")
    css = css_base(e, K) + css_estilo(e, K) + css_formato(formato, K)
    res_attr = ' data-resolution="portrait-4k"' if a.res == "4k" else ""

    if a.modo == "detras":
        (gdir / "compositions" / "behind.html").write_text(detras_comp(plan, anclas, e, dur, W, H, css), encoding="utf-8")
        hosts = f'      <div id="capa-detras" class="layer" data-composition-id="behind" data-composition-src="compositions/behind.html" data-start="0" data-duration="{dur}" data-track-index="1" data-width="{W}" data-height="{H}"></div>'
        fondo, video, zjs = "transparent", "", ""
    else:
        subs = leer_json(tr / "subtitulos" / "subtitulos.json")
        ocupado = []
        graf = graficos_comp(plan, anclas, e, tr, assets, dur, W, H, css, ocupado)
        ocultar = plan.get("ocultar_subtitulos", []) + ([] if plan.get("mantener_subtitulos") else ocupado)
        (gdir / "compositions" / "graphics.html").write_text(graf, encoding="utf-8")
        (gdir / "compositions" / "captions.html").write_text(subtitulos_comp(subs, e, ocultar, dur, W, H, css), encoding="utf-8")
        hosts = (f'      <div id="capa-graficos" class="layer" data-composition-id="graphics" data-composition-src="compositions/graphics.html" data-start="0" data-duration="{dur}" data-track-index="2" data-width="{W}" data-height="{H}"></div>\n'
                 f'      <div id="capa-subtitulos" class="layer" data-composition-id="captions" data-composition-src="compositions/captions.html" data-track-kind="captions" data-start="0" data-duration="{dur}" data-track-index="3" data-width="{W}" data-height="{H}"></div>')
        fondo = "#021020"
        video = (f'      <div id="zoom"><video id="base" class="clip" src="assets/base.mp4" playsinline data-has-audio="true" '
                 f'data-start="0" data-duration="{dur}" data-track-index="0"></video></div>')
        zjs = zooms_js(plan, e, dur)
        if formato == "pantalla-dividida":
            # Panel de arriba: capturas/vídeos del usuario si los hay; si no, motions explicativos (motions.py)
            colores = leer_json(SKILL / "marca" / "decodik.json")["colores"]
            p_html, p_js = panel_motion(plan.get("panel", []), Anclas(palabras), lambda src: copiar_asset(src, tr, assets), dur, K)
            (gdir / "compositions" / "panel.html").write_text(
                comp("panel", dur, W, H, css + css_panel(colores, K), '        <div class="pfondo"></div>' + NL + p_html, p_js, "ptl"), encoding="utf-8")
            hosts = (f'      <div id="capa-panel" class="layer" data-composition-id="panel" data-composition-src="compositions/panel.html" '
                     f'data-start="0" data-duration="{dur}" data-track-index="1" data-width="{W}" data-height="{H}"></div>' + NL + hosts)
            video = '      <div id="panel-persona">' + NL + video + NL + '      </div>'
        elif formato == "recuadro":
            # Fondo: grabación de pantalla real si la hay; si no, motions explicativos a pantalla completa
            if plan.get("fondo"):
                fsrc = copiar_asset(plan["fondo"], tr, assets)
                fondo_html = (f'      <video id="fondo" class="clip" src="{fsrc}" muted playsinline data-has-audio="false" '
                              f'data-start="0" data-duration="{dur}" data-track-index="1"></video>')
            elif plan.get("panel"):
                colores = leer_json(SKILL / "marca" / "decodik.json")["colores"]
                p_html, p_js = panel_motion(plan["panel"], Anclas(palabras), lambda src: copiar_asset(src, tr, assets), dur, K)
                (gdir / "compositions" / "panel.html").write_text(
                    comp("panel", dur, W, H, css + css_panel(colores, K, "recuadro"), '        <div class="pfondo"></div>' + NL + p_html, p_js, "ptl"),
                    encoding="utf-8")
                # va antes del recuadro en el DOM: queda detrás de la persona
                fondo_html = (f'      <div id="capa-panel" class="layer" data-composition-id="panel" data-composition-src="compositions/panel.html" '
                              f'data-start="0" data-duration="{dur}" data-track-index="1" data-width="{W}" data-height="{H}"></div>')
            else:
                error('El formato recuadro necesita "fondo" (grabación de pantalla) o "panel" (motions explicativos) en plan.json.')
            video = fondo_html + NL + '      <div id="panel-persona">' + NL + video + NL + '      </div>'
            zjs = ""  # sin zoom dentro del recuadro

    index = f"""<!doctype html>
<html lang="es"{res_attr}>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="assets/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: {fondo}; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; }}
      #zoom {{ position: absolute; inset: 0; transform-origin: 50% 35%; }}
      #base {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
{css_index_formato(formato, W, H)}
      .layer {{ position: absolute; inset: 0; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{W}" data-height="{H}">
{video}
{hosts}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
{zjs}      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    (gdir / "index.html").write_text(index, encoding="utf-8")
    if EVENTOS and a.modo == "final":
        sfx = [{"archivo": f"05_musica/efectos/{n}.wav", "t": t, "db": {"whoosh": -24, "uiclick": -28, "impact": -20}.get(n, -24)} for t, n in sorted(EVENTOS)]
        escribir_json(tr / "efectos_sugeridos.json", sfx)
        aviso(f"Efectos sugeridos ({len(sfx)}) en 06_trabajo/efectos_sugeridos.json: revisa las rutas y úsalo con mezclar.py --efectos.")
    n = len([g for g in plan.get("graficos", []) if (g["tipo"] == "palabra_detras") == (a.modo == "detras")])
    aviso(f"Proyecto HyperFrames listo en {gdir} ({a.modo}, {W}×{H}, {dur} s, {n} gráficos, estilo {e['id']}).")
    if a.modo == "final":
        aviso("Siguiente: cd graficos && npx hyperframes check && npx hyperframes snapshot . --at <tiempos> --no-end && npx hyperframes render . -o ../con_graficos.mp4")
    else:
        aviso("Siguiente: cd graficos && npx hyperframes render . --format mov -o ../detras.mov  (y luego componer_base.py)")


if __name__ == "__main__":
    main()
