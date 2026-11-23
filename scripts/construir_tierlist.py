# -*- coding: utf-8 -*-
"""Formato Tier list · dibuja el vídeo a partir de tierlist-plan.json.

  python construir_tierlist.py --trabajo 06_trabajo --fotos 1,4.3,20     (fotogramas de prueba + hoja)
  python construir_tierlist.py --trabajo 06_trabajo --salida ../07_entrega/tierlist-v1.mp4

Encima del vídeo cortado: título fijo arriba, tabla de niveles bajo la barbilla,
fotos que se presentan grandes y bajan a su nivel, subtítulos de 1-3 palabras,
destello al quitar la tabla y píldora de «Follow» en la llamada a seguir.
No toca el color de la persona. Voz a -14 LUFS.
"""
import argparse, json, math, os, re, subprocess, sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SKILL = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
CARPETAS_FUENTES = [SKILL / "fonts", Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
                    Path("/System/Library/Fonts/Supplemental"), Path("/Library/Fonts"),
                    Path.home() / "Library" / "Fonts", Path("/usr/share/fonts/truetype/msttcorefonts")]
_fuentes = {}


def fuente(nombres, px):
    """Primera fuente que exista de la lista. Instrument Serif se engorda con trazo."""
    clave = (tuple(nombres), px)
    if clave not in _fuentes:
        for n in nombres:
            for c in CARPETAS_FUENTES:
                if (c / n).exists():
                    _fuentes[clave] = (ImageFont.truetype(str(c / n), px), "InstrumentSerif" in n)
                    break
            if clave in _fuentes:
                break
        else:
            raise FileNotFoundError(f"ninguna fuente de {nombres}")
    return _fuentes[clave]


# ---------------- curvas ----------------
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def sal(p):
    return 1 - (1 - clamp(p)) ** 3


def suave(p):
    p = clamp(p)
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def rebote(p):
    p = clamp(p)
    return 1 + 2.70158 * (p - 1) ** 3 + 1.70158 * (p - 1) ** 2


def mezcla(a, b, p):
    return a + (b - a) * p


# ---------------- texto ----------------
def ancho(txt, f, tr):
    return sum(f.getlength(c) for c in txt) + tr * max(0, len(txt) - 1)


def escribe(d, x, y, txt, f, color, tr, gordo=False):
    for c in txt:
        d.text((x, y), c, font=f, fill=color, anchor="lm",
               stroke_width=2 if gordo else 0, stroke_fill=color)
        x += f.getlength(c) + tr
    return x


def linea_texto(trozos, cy, hueco=18, cx=W / 2, derecha=None, halo=None, sombra=(0, 5, 8, 230)):
    """trozos = [(texto, fuente, gordo, color, tracking)] → capa RGBA y (x0, x1)."""
    total = sum(ancho(t, f, tr) for t, f, g, c, tr in trozos) + hueco * (len(trozos) - 1)
    x0 = (derecha - total) if derecha is not None else cx - total / 2
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    x, cajas = x0, []
    for t, f, g, c, tr in trozos:
        x1 = escribe(d, x, cy, t, f, c, tr, g)
        cajas.append((x, x1 - tr, c))
        x = x1 - tr + hueco
    alfa = capa.split()[3]
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if halo:  # resplandor detrás de la palabra clave
        color_clave, color_halo = halo
        for a, b, c in cajas:
            if c == color_clave:
                m = Image.new("L", (W, H), 0)
                m.paste(alfa.crop((int(a) - 4, 0, int(b) + 4, H)), (int(a) - 4, 0))
                h = Image.new("RGBA", (W, H), color_halo)
                h.putalpha(m.filter(ImageFilter.GaussianBlur(14)).point(lambda v: min(255, int(v * 1.6))))
                out.alpha_composite(h)
    dx, dy, bl, op = sombra
    s = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    sa = Image.new("L", (W, H), 0)
    sa.paste(alfa, (dx, dy))
    s.putalpha(sa.filter(ImageFilter.GaussianBlur(bl)).point(lambda v: min(255, int(v * op / 128))))
    out.alpha_composite(s)
    out.alpha_composite(capa)
    return out, (x0, x0 + total)


def con_alfa(capa, a):
    if a >= 1:
        return capa
    c = capa.copy()
    c.putalpha(c.split()[3].point(lambda v: int(v * a)))
    return c


class Tierlist:
    def __init__(self, plan, trabajo):
        self.p, self.dir = plan, trabajo
        self.e, self.g = plan["estilo"], plan["geometria"]
        self.x0, self.y0, self.x1, self.y1 = self.g["tabla"]
        self.col, self.fila, self.mini = self.g["etiqueta"], self.g["fila"], self.g["mini"]
        self.avisos = []
        self.titulo, self.caja_titulo = self._titulo()
        self.filas = self._filas()
        self.tabla = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for k, (img, y) in enumerate(self.filas):
            self.tabla.alpha_composite(img, (self.x0, int(y)))
        ImageDraw.Draw(self.tabla).rectangle((self.x0, self.y0, self.x1, self.y1), outline=self.e["tabla"]["linea"], width=2)
        self.fotos = {}
        for el in plan["elementos"]:
            ruta = (trabajo / el["imagen"]).resolve()
            self.fotos[el["id"]] = ImageOps.exif_transpose(Image.open(ruta)).convert("RGB")
        self._recortes = {}
        self.subs = self._grupos()
        self._cache_sub = {}
        self.pildoras = (self._pildora(False), self._pildora(True)) if plan.get("seguir") else None
        self._comprobar()

    # ----- título -----
    def _titulo(self):
        T = self.e["titulo"]
        Z = self.e["zona"]
        ancho_max = Z["x1"] - Z["x0"]
        lineas = self.p["titulo"]["lineas"]
        capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        y = T["y0"]
        cajas = []
        for k, txt in enumerate(lineas[:2]):
            est = T["linea1"] if k == 0 else T["linea2"]
            px = est["px"]
            while True:
                f, gordo = fuente(est["fuentes"], px)
                trozos = []
                for palabra in txt.split():
                    clave = palabra.startswith("*") and palabra.endswith("*")
                    trozos.append((palabra.strip("*"), f, gordo, est.get("clave", est["color"]) if clave else est["color"], est["tracking"]))
                total = sum(ancho(t, ff, tr) for t, ff, g, c, tr in trozos) + 18 * (len(trozos) - 1)
                if total <= ancho_max or px <= T["px_min"]:
                    break
                px -= 2
            if total > ancho_max:
                self.avisos.append(f"el título «{txt}» no cabe: acórtalo")
            cy = y + px * 0.55
            lay, caja = linea_texto(trozos, cy, hueco=int(px * 0.34),
                                    halo=(est.get("clave"), est.get("halo")) if est.get("halo") else None)
            capa.alpha_composite(lay)
            cajas.append((caja[0], cy - px * 0.45, caja[1], cy + px * 0.45))
            y += T["interlinea"][0] if k == 0 else 0
        self.cajas_lineas = list(cajas)
        parte = self.p["titulo"].get("parte")
        if parte and len(cajas) > 1:
            est = T["parte"]
            f, gordo = fuente(est["fuentes"], est["px"])
            cy = cajas[-1][3] + est["px"] * 0.35
            lay, caja = linea_texto([(parte, f, gordo, est["color"], est["tracking"])], cy, derecha=cajas[-1][2] + 6)
            capa.alpha_composite(lay)
            cajas.append((caja[0], cy - est["px"] * 0.45, caja[1], cy + est["px"] * 0.45))
        caja = (min(c[0] for c in cajas), min(c[1] for c in cajas), max(c[2] for c in cajas), max(c[3] for c in cajas))
        return capa, caja

    # ----- filas de la tabla -----
    def _filas(self):
        t = self.e["tabla"]
        out = []
        f, gordo = fuente(t["fuentes"], t["px"])
        for k, nv in enumerate(self.p["niveles"]):
            y = self.y0 + k * self.fila
            h = int(round(self.y0 + (k + 1) * self.fila) - round(y))
            img = Image.new("RGBA", (self.x1 - self.x0, h), t["fondo"])
            d = ImageDraw.Draw(img)
            d.rectangle((0, 0, self.col, h), fill=nv["color"])
            d.line((0, h - 1, img.width, h - 1), fill=t["linea"], width=2)
            lineas = self._partir(nv["texto"].upper(), f, self.col - 24)
            alto = t["px"] * 1.18
            yy = h / 2 - alto * (len(lineas) - 1) / 2
            for ln in lineas:
                if ancho(ln, f, 0.5) > self.col - 16:
                    self.avisos.append(f"la etiqueta «{ln}» no cabe en {self.col} px: acórtala")
                escribe(d, (self.col - ancho(ln, f, 0.5)) / 2, yy, ln, f, t["tinta"], 0.5, gordo)
                yy += alto
            out.append((img, round(y)))
        return out

    @staticmethod
    def _partir(txt, f, maximo):
        palabras, lineas = txt.split(), []
        for p in palabras:
            if lineas and ancho(lineas[-1] + " " + p, f, 0.5) <= maximo:
                lineas[-1] += " " + p
            else:
                lineas.append(p)
        return lineas

    # ----- fotos -----
    def hueco(self, nivel, pos):
        m = self.e["tabla"]["margen_mini"]
        x = self.x0 + self.col + m + pos * (self.mini + m)
        y = self.y0 + nivel * self.fila + m
        return (x, y, x + self.mini, y + self.mini)

    def _foto(self, el, w, h):
        k = (el["id"], w, h)
        if k not in self._recortes:
            if len(self._recortes) > 40:
                self._recortes.clear()
            self._recortes[k] = ImageOps.fit(self.fotos[el["id"]], (w, h), Image.LANCZOS,
                                             centering=tuple(el.get("foco", [0.5, 0.5]))).convert("RGBA")
        return self._recortes[k]

    def _pega(self, lienzo, el, r, alfa=1.0, borde=False):
        x0, y0, x1, y1 = r
        w, h = max(2, int(round(x1 - x0))), max(2, int(round(y1 - y0)))
        im = self._foto(el, w, h)
        if borde:  # marco fino y sombra mientras está grande o en movimiento
            som = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
            ImageDraw.Draw(som).rectangle((20, 26, 20 + w, 26 + h), fill=(0, 0, 0, int(150 * alfa)))
            lienzo.alpha_composite(som.filter(ImageFilter.GaussianBlur(10)), (int(round(x0)) - 20, int(round(y0)) - 20))
        lienzo.alpha_composite(con_alfa(im, alfa), (int(round(x0)), int(round(y0))))

    def _elementos(self, lienzo, t):
        a = self.e["animacion"]
        quietos, moviendo = [], []
        for el in self.p["elementos"]:
            if t < el["entra"]:
                continue
            g = el["grande"]
            pasos = el["pasos"]
            if t < pasos[0]["t"]:
                p = sal((t - el["entra"]) / a["entrada"])
                dy = (1 - p) * a["subida"]
                esc = mezcla(0.9, 1.0, p)
                cx, cy = (g[0] + g[2]) / 2, (g[1] + g[3]) / 2 + dy
                w, h = (g[2] - g[0]) * esc, (g[3] - g[1]) * esc
                moviendo.append((el, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), p))
                continue
            r, activo = tuple(g), False
            for ps in pasos:
                if t < ps["t"]:
                    break
                dest = self.hueco(ps["nivel"], ps["pos"])
                p = suave((t - ps["t"]) / a["guardado"])
                activo = activo or p < 1
                r = tuple(mezcla(r[i], dest[i], p) for i in range(4))
            (moviendo if activo else quietos).append((el, r, 1.0))
        for el, r, al in quietos:
            self._pega(lienzo, el, r, al)
        for el, r, al in moviendo:
            self._pega(lienzo, el, r, al, borde=True)

    # ----- subtítulos -----
    def _grupos(self):
        s = self.e["subtitulos"]
        pal = json.loads((self.dir / self.p["palabras"]).read_text(encoding="utf-8"))
        for i, txt in self.p.get("correcciones", {}).items():
            pal[int(i)]["w"] = txt
        for i, (a, b) in self.p.get("tiempos", {}).items():
            pal[int(i)]["start"], pal[int(i)]["end"] = a, b
        no_cierran = set(s["no_cierran"])
        MAXP, MAXL = s["max_palabras"], s["max_letras"]
        grupos, act = [], []

        def txt(ws):
            return " ".join(x["w"] for x in ws)

        def cierra(fin_frase=False):
            if not act:
                return
            # no acabar en «y», «la», «más»…: si queda una palabra con contenido, la de enlace pasa al siguiente
            pasa = []
            while len(act) > 1 and act[-1]["w"] in no_cierran and any(x["w"] not in no_cierran for x in act[:-1]):
                pasa.insert(0, act.pop())
            grupos.append({"txt": txt(act), "t0": act[0]["start"], "t1": act[-1]["end"], "fin": fin_frase and not pasa})
            act.clear()
            act.extend(pasa)

        for w in pal:
            limpio = re.sub(r"[.,;:!?¡¿\"…]", "", w["w"]).strip().lower()
            if not limpio:
                continue
            nueva = {"w": limpio, "start": w["start"], "end": w["end"]}
            if act:
                lleno = len(act) >= MAXP or len(txt(act + [nueva])) > MAXL
                # si el grupo acabaría en palabra de enlace, se deja pasar a una palabra más para cerrar con contenido
                estira = (act[-1]["w"] in no_cierran and len(act) <= MAXP and len(txt(act + [nueva])) <= MAXL + 5)
                if lleno and not estira:
                    cierra()
            act.append(nueva)
            if re.search(r"[.,;:!?…]$", w["w"]):
                cierra(fin_frase=True)
            elif len(act) > MAXP:
                cierra()
        cierra(fin_frase=True)
        if act:
            grupos.append({"txt": txt(act), "t0": act[0]["start"], "t1": act[-1]["end"], "fin": True})
        # nada de destellos: un subtítulo de menos de 0,35 s se une al siguiente o al anterior,
        # sin saltarse un punto ni pasar de MAXP+1 palabras
        cabe = lambda a, b: len((a + " " + b).split()) <= MAXP + 1 and len(a + " " + b) <= MAXL + 5
        i = 0
        while i < len(grupos):
            g = grupos[i]
            if g["t1"] - g["t0"] < 0.35:
                sig = grupos[i + 1] if i + 1 < len(grupos) else None
                ant = grupos[i - 1] if i > 0 else None
                if sig and not g["fin"] and cabe(g["txt"], sig["txt"]) and sig["t0"] - g["t1"] < 0.3:
                    grupos[i + 1] = {"txt": g["txt"] + " " + sig["txt"], "t0": g["t0"], "t1": sig["t1"], "fin": sig["fin"]}
                    grupos.pop(i)
                    continue
                if ant and not ant["fin"] and cabe(ant["txt"], g["txt"]) and g["t0"] - ant["t1"] < 0.3:
                    grupos[i - 1] = {"txt": ant["txt"] + " " + g["txt"], "t0": ant["t0"], "t1": g["t1"], "fin": g["fin"]}
                    grupos.pop(i)
                    continue
            i += 1
        for i, g in enumerate(grupos):
            sig = grupos[i + 1]["t0"] if i + 1 < len(grupos) else g["t1"] + 0.5
            g["t1"] = min(sig, g["t1"] + s["aguante"])
        return grupos

    def _sub(self, lienzo, t):
        s = self.e["subtitulos"]
        for g in self.subs:
            if g["t0"] <= t < g["t1"]:
                if g["txt"] not in self._cache_sub:
                    f, gordo = fuente(s["fuentes"], s["px"])
                    lay, (a, b) = linea_texto([(g["txt"], f, gordo, s["color"], s["tracking"])], self.g["sub_y"], sombra=(0, 4, 7, 255))
                    Z = self.e["zona"]
                    if a < Z["x0"] or b > Z["x1"]:
                        self.avisos.append(f"subtítulo fuera de la zona: «{g['txt']}»")
                    self._cache_sub[g["txt"]] = lay
                lienzo.alpha_composite(self._cache_sub[g["txt"]])
                return

    # ----- píldora «Follow» -----
    def _caja_pildora(self):
        sg = self.e["seguir"]
        cy = self.g["sub_y"] + sg["bajo_sub"]
        return (W // 2 - sg["ancho"] // 2, cy - sg["alto"] // 2, W // 2 + sg["ancho"] // 2, cy + sg["alto"] // 2)

    def _pildora(self, siguiendo):
        sg, p = self.p["seguir"], self.e["seguir"]
        x0, y0, x1, y1 = self._caja_pildora()
        capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        som = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(som).rounded_rectangle((x0, y0 + 6, x1, y1 + 6), radius=(y1 - y0) // 2, fill=(0, 0, 0, 90))
        capa.alpha_composite(som.filter(ImageFilter.GaussianBlur(10)))
        d = ImageDraw.Draw(capa)
        d.rounded_rectangle((x0, y0, x1, y1), radius=(y1 - y0) // 2, fill="#FFFFFF")
        r = (y1 - y0) // 2 - 10
        cx, cy = x0 + 12 + r, (y0 + y1) // 2
        ruta = (self.dir / sg["avatar"]).resolve()
        if ruta.exists():
            av = ImageOps.fit(Image.open(ruta).convert("RGB"), (2 * r, 2 * r), Image.LANCZOS)
            m = Image.new("L", (8 * r, 8 * r), 0)
            ImageDraw.Draw(m).ellipse((0, 0, 8 * r - 1, 8 * r - 1), fill=255)
            capa.paste(av, (cx - r, cy - r), m.resize((2 * r, 2 * r), Image.LANCZOS))
        else:
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#DDDDDD")
            self.avisos.append(f"no hay avatar en {ruta}")
        d.ellipse((cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3), outline=p["aro"], width=3)
        f, gordo = fuente(p["fuentes"], p["px"])
        escribe(d, cx + r + 18, cy, sg["usuario"], f, "#111111", -0.3, gordo)
        fb, _ = fuente(p["fuentes"], p["px_boton"])
        bx0, by0, bx1, by1 = x1 - 16 - p["boton_ancho"], cy - 22, x1 - 16, cy + 22
        if siguiendo:
            d.rounded_rectangle((bx0, by0, bx1, by1), radius=22, fill="#FFFFFF", outline="#9AA3AD", width=2)
            d.text(((bx0 + bx1) / 2, cy), "Following", font=fb, fill="#5B6570", anchor="mm")
        else:
            d.rounded_rectangle((bx0, by0, bx1, by1), radius=22, fill=p["boton"])
            d.text(((bx0 + bx1) / 2, cy), "Follow", font=fb, fill="#FFFFFF", anchor="mm")
        if cx + r + 18 + ancho(sg["usuario"], f, -0.3) > bx0 - 10:
            self.avisos.append("el usuario no cabe en la píldora: acórtalo o ensancha seguir.ancho")
        return capa

    def _seguir(self, lienzo, t):
        sg = self.p.get("seguir")
        if not sg or t < sg["entra"]:
            return
        capa = self.pildoras[1] if t >= sg["entra"] + sg["pulsa"] else self.pildoras[0]
        x0, y0, x1, y1 = self._caja_pildora()
        caja = (x0 - 30, y0 - 20, x1 + 30, y1 + 40)
        trozo = capa.crop(caja)
        p = (t - sg["entra"]) / 0.35
        esc = max(0.05, rebote(p)) if p < 1 else 1.0
        dp = t - (sg["entra"] + sg["pulsa"])
        if 0 <= dp < 0.2:
            esc *= 1 - 0.05 * math.sin(math.pi * dp / 0.2)
        if esc != 1.0:
            trozo = trozo.resize((max(2, int(trozo.width * esc)), max(2, int(trozo.height * esc))), Image.LANCZOS)
        cx, cy = (caja[0] + caja[2]) // 2, (caja[1] + caja[3]) // 2
        lienzo.alpha_composite(trozo, (cx - trozo.width // 2, cy - trozo.height // 2))

    # ----- entrada, destello -----
    def _intro(self, lienzo, t):
        a = self.e["animacion"]["intro"]
        p = sal(t / (a * 0.6))
        lienzo.alpha_composite(con_alfa(self.titulo, p), (0, int((1 - p) * -24)) if p < 1 else (0, 0))
        n = len(self.filas)
        for k, (img, y) in enumerate(self.filas):
            q = sal((t - k * a * 0.08) / (a * 0.6))
            if q <= 0:
                continue
            lienzo.alpha_composite(con_alfa(img, q), (self.x0 + int((1 - q) * -60), int(y)))
        if t >= a * 0.08 * (n - 1) + a * 0.6:
            ImageDraw.Draw(lienzo).rectangle((self.x0, self.y0, self.x1, self.y1), outline=self.e["tabla"]["linea"], width=2)

    def _destello(self, lienzo, t):
        d = self.e["destello"]
        fin = self.p["tabla_fin"]
        t0, t1 = fin - d["antes"], fin + d["despues"]
        if not (t0 < t < t1):
            return
        p = clamp((t - t0) / (fin - t0) if t < fin else 1 - (t - fin) / (t1 - fin))
        if p < 0.6:
            q = p / 0.6
            col = (int(mezcla(200, 255, q)), int(mezcla(30, 140, q)), int(mezcla(30, 20, q)))
        else:
            q = (p - 0.6) / 0.4
            col = (255, int(mezcla(140, 250, q)), int(mezcla(20, 215, q)))
        lienzo.alpha_composite(Image.new("RGBA", (W, H), col + (int(250 * p ** 1.6),)))

    def fotograma(self, t):
        lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if t < self.p["tabla_fin"]:
            if t < self.e["animacion"]["intro"]:
                self._intro(lienzo, t)
            else:
                lienzo.alpha_composite(self.titulo)
                lienzo.alpha_composite(self.tabla)
            self._elementos(lienzo, t)
        self._sub(lienzo, t)
        self._seguir(lienzo, t)
        self._destello(lienzo, t)
        return lienzo

    # ----- comprobaciones (nada se pisa, todo en zona) -----
    def _comprobar(self):
        Z, g = self.e["zona"], self.g
        tx0, ty0, tx1, ty1 = self.caja_titulo
        if tx0 < Z["x0"] or tx1 > Z["x1"] or ty0 < Z["y0"]:
            self.avisos.append(f"el título se sale de la zona segura ({tx0:.0f}-{tx1:.0f} × {ty0:.0f})")
        abajo = self.cajas_lineas[-1][3]  # «pt.2» va al lado de la cabeza: no cuenta
        if g.get("frente") and abajo > g["frente"] + 40:
            self.avisos.append(f"el título baja hasta y={abajo:.0f} y la cara empieza en y≈{g['frente']}: puede tapar la frente")
        s = self.e["subtitulos"]
        if g["sub_y"] - s["px"] * 0.5 < g["barbilla"]:
            self.avisos.append("el subtítulo toca la barbilla")
        if self.y1 > Z["y1"] or self.x1 > Z["x1"] or self.x0 < Z["x0"]:
            self.avisos.append("la tabla se sale de la zona segura")
        if self.p.get("seguir"):
            x0, y0, x1, y1 = self._caja_pildora()
            if y0 < g["sub_y"] + s["px"] * 0.6:
                self.avisos.append("la píldora pisa el subtítulo")


def leer_plan(trabajo):
    return json.loads((trabajo / "tierlist-plan.json").read_text(encoding="utf-8"))


def fotograma_video(video, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                          "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (W, H), raw).convert("RGBA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trabajo", required=True)
    ap.add_argument("--salida")
    ap.add_argument("--fotos", help="segundos separados por comas: solo fotogramas de prueba")
    a = ap.parse_args()
    trabajo = Path(a.trabajo).resolve()
    plan = leer_plan(trabajo)
    tl = Tierlist(plan, trabajo)
    video = Path(plan["video"])
    fps = plan.get("fps", 30)

    if a.fotos:
        carpeta = trabajo / "tierlist-pruebas"
        carpeta.mkdir(exist_ok=True)
        tiempos = [float(x) for x in a.fotos.split(",")]
        mini = []
        for t in tiempos:
            f = fotograma_video(video, t)
            f.alpha_composite(tl.fotograma(t))
            f = f.convert("RGB")
            f.save(carpeta / f"t_{t:06.2f}.jpg", quality=90)
            mini.append(f.resize((360, 640)))
        hoja = Image.new("RGB", (360 * min(6, len(mini)), 640 * math.ceil(len(mini) / 6)), "black")
        for i, m in enumerate(mini):
            hoja.paste(m, ((i % 6) * 360, (i // 6) * 640))
        hoja.save(carpeta / "_hoja.jpg", quality=88)
        print("Pruebas en", carpeta)
    else:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                                   capture_output=True, text=True).stdout.strip())
        n = int(dur * fps)
        sfx = plan.get("sfx", [])
        entradas = ["-i", str(video), "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-"]
        archivos = sorted({s["archivo"] for s in sfx})
        for f in archivos:
            entradas += ["-i", f]
        filtro = [f"[0:v]fps={fps},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[b]",
                  "[b][1:v]overlay=shortest=1:format=auto[v]"]
        mezcla_a = ["[0:a]"]
        for k, f in enumerate(archivos):
            ev = [s for s in sfx if s["archivo"] == f]
            filtro.append(f"[{k + 2}:a]asplit={len(ev)}" + "".join(f"[s{k}_{j}]" for j in range(len(ev))))
            for j, s in enumerate(ev):
                ms = int(max(0, s["t"]) * 1000)
                filtro.append(f"[s{k}_{j}]adelay={ms}|{ms},volume={s['vol']}[e{k}_{j}]")
                mezcla_a.append(f"[e{k}_{j}]")
        if len(mezcla_a) > 1:
            filtro.append("".join(mezcla_a) + f"amix=inputs={len(mezcla_a)}:normalize=0:duration=first[m]")
            filtro.append("[m]loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        else:
            filtro.append("[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        cmd = ["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(filtro),
               "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", a.salida]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            pr.stdin.write(tl.fotograma(i / fps).tobytes())
            if i % 300 == 0:
                print(f"  {i}/{n}", flush=True)
        pr.stdin.close()
        pr.wait()
        if pr.returncode:
            sys.exit("ffmpeg ha fallado")
        print("OK", a.salida)
    for av in dict.fromkeys(tl.avisos):
        print("  [aviso]", av)


if __name__ == "__main__":
    main()
