"""Pasada de subtítulos: frases.txt + palabras.json + estilo → subtitulos.json, .ass y .srt

Uso:
  python subtitulos.py --palabras 06_trabajo/palabras.json --frases 06_trabajo/frases.txt
                       --estilo <SKILL>/estilos/minimal.json --out 06_trabajo/subtitulos [--ancho 1080 --alto 1920]
  python subtitulos.py --palabras 06_trabajo/palabras.json --solo-srt --out 07_entrega/video.srt

frases.txt: una frase por línea, trozos separados con | y la palabra clave entre *asteriscos*.
En los estilos con tachado (Neón lima), ~palabra~ se tacha en rojo.
"""
import argparse
import re
from pathlib import Path

from comun import SKILL, aviso, escribir_json, leer_json, normalizar_palabra

COLA = 0.3


def t_srt(t):
    h, r = divmod(max(t, 0), 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}".replace(",1000", ",999")


def t_ass(t):
    h, r = divmod(max(t, 0), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def color_ass(hexa, alfa=0):
    h = hexa.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alfa:02X}{b}{g}{r}".upper()


def leer_frases(ruta):
    trozos = []
    for n, linea in enumerate(Path(ruta).read_text(encoding="utf-8").splitlines()):
        linea = linea.strip()
        if not linea:
            continue
        variante = None
        m = re.match(r"\[(\w+)\]\s*", linea)  # [lento], [golpe]…: entrada del bloque (estilos con bloques)
        if m:
            variante, linea = m.group(1).lower(), linea[m.end():]
        for i, trozo in enumerate(linea.split("|")):
            tokens = []
            for tok in trozo.split():
                clave = "*" in tok
                tachado = "~" in tok  # ~palabra~: se tacha (solo estilos con tachado)
                tokens.append({"texto": tok.replace("*", "").replace("~", ""), "clave": clave, "tachado": tachado})
            if tokens:
                trozos.append({"frase": n, "tokens": tokens, "fin_frase": False, "variante": variante})
        if trozos:
            trozos[-1]["fin_frase"] = True
    return trozos


def alinear(trozos, palabras):
    """Asigna a cada token la palabra de palabras.json correspondiente (en orden)."""
    norm = [normalizar_palabra(p["w"]) for p in palabras]
    i, avisos = 0, []
    for t in trozos:
        for tok in t["tokens"]:
            objetivo = normalizar_palabra(tok["texto"])
            if not objetivo:
                tok["idx"] = None
                continue
            encontrado = None
            for j in range(i, min(i + 6, len(palabras))):
                if norm[j] == objetivo or (len(objetivo) > 3 and (norm[j].startswith(objetivo[:4]))):
                    encontrado = j
                    break
            if encontrado is None:
                avisos.append(f"«{tok['texto']}» no coincide con la transcripción cerca de «{palabras[min(i, len(palabras)-1)]['w']}»")
                tok["idx"] = i if i < len(palabras) else None
                i += 1
            else:
                tok["idx"] = encontrado
                i = encontrado + 1
    return avisos


def tiempos(trozos, palabras, minima):
    for t in trozos:
        idx = [x["idx"] for x in t["tokens"] if x.get("idx") is not None]
        t["start"] = palabras[min(idx)]["start"] if idx else None
        t["end_voz"] = palabras[max(idx)]["end"] if idx else None
    validos = [t for t in trozos if t["start"] is not None]
    for k, t in enumerate(validos):
        sig = validos[k + 1]["start"] if k + 1 < len(validos) else None
        fin = t["end_voz"] + COLA
        if sig is not None:
            fin = max(min(fin, sig), min(t["start"] + minima, sig))
        else:
            fin = max(fin, t["start"] + minima)
        t["end"] = round(fin, 3)
        t["start"] = round(t["start"], 3)
    return validos


def auto_trozos(palabras, maximo=3):
    trozos, actual = [], []
    for k, p in enumerate(palabras):
        actual.append({"texto": p["w"], "clave": False, "idx": k})
        pausa = k + 1 < len(palabras) and palabras[k + 1]["start"] - p["end"] > 0.35
        if len(actual) >= maximo or re.search(r"[.,;:?!]$", p["w"]) or pausa:
            trozos.append({"tokens": actual, "fin_frase": True})
            actual = []
    if actual:
        trozos.append({"tokens": actual, "fin_frase": True})
    return trozos


PUNTUACION = ".,;:!?¡¿…\"«»"


def quitar_puntuacion(validos):
    """Estilos con "puntuacion": false (Minimal): fuera puntos, comas, interrogaciones…
    Se conservan los signos dentro de la palabra («1,5», «TikTok's») y los trozos que
    quedarían vacíos."""
    for t in validos:
        for tok in t["tokens"]:
            limpio = tok["texto"].strip(PUNTUACION)
            if limpio:
                tok["texto"] = limpio


def escribir_srt(validos, ruta):
    lineas = []
    for n, t in enumerate(validos, 1):
        texto = " ".join(x["texto"] for x in t["tokens"])
        lineas += [str(n), f"{t_srt(t['start'])} --> {t_srt(t['end'])}", texto, ""]
    Path(ruta).write_text("\n".join(lineas), encoding="utf-8")


def escribir_ass(validos, estilo, ruta, ancho, alto):
    s = estilo["subtitulos"]
    k = alto / (estilo.get("lienzo", {}).get("alto") or 1920)
    fs, cfs = round(s["tamano"] * k), round(s["clave_tamano"] * k)
    y = round(s["posicion_y"] * k)
    caja = s.get("clave_caja")
    sombra_alfa = 0x60
    estilos = [
        f"Style: Base,{s['fuente']},{fs},{color_ass(s['color'])},{color_ass(s['color'])},"
        f"{color_ass(s.get('contorno', '#000000'))},{color_ass('#000000', sombra_alfa)},0,0,0,0,100,100,0,0,1,"
        f"{round(s.get('grosor_contorno', 0) * k)},{round(s.get('sombra', 0) * k)},5,60,60,0,1",
        f"Style: Clave,{s['clave_fuente']},{cfs},{color_ass(s['clave_color'])},{color_ass(s['clave_color'])},"
        f"{color_ass(caja or s.get('contorno', '#000000'))},{color_ass(caja or '#000000', 0 if caja else sombra_alfa)},"
        f"0,0,0,0,100,100,0,0,{3 if caja else 1},{round((14 if caja else s.get('grosor_contorno', 0)) * k)},"
        f"{0 if caja else round(s.get('sombra', 0) * k)},5,60,60,0,1",
    ]
    golpe = "escala" in s.get("entrada", "")
    eventos = []
    for t in validos:
        partes = []
        for tok in t["tokens"]:
            txt = tok["texto"].upper() if s.get("mayusculas") else tok["texto"]
            txt = txt.replace("{", "(").replace("}", ")")
            if tok["clave"]:
                anim = r"\fscx115\fscy115\t(0,120,\fscx100\fscy100)" if golpe else ""
                partes.append(f"{{\\rClave{anim}}}{txt}{{\\rBase}}")
            else:
                partes.append(txt)
        texto = " ".join(partes)
        eventos.append(f"Dialogue: 0,{t_ass(t['start'])},{t_ass(t['end'])},Base,,0,0,0,,{{\\pos({round(s.get('centro_x', 540) * k)},{y})}}{texto}")
    cab = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {ancho}\nPlayResY: {alto}\nWrapStyle: 2\n"
           "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
           "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
           "MarginL, MarginR, MarginV, Encoding\n" + "\n".join(estilos) +
           "\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    Path(ruta).write_text(cab + "\n".join(eventos) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--palabras", required=True)
    ap.add_argument("--frases")
    ap.add_argument("--estilo", default=str(SKILL / "estilos" / "minimal.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--solo-srt", action="store_true")
    ap.add_argument("--ancho", type=int, default=1080)
    ap.add_argument("--alto", type=int, default=1920)
    a = ap.parse_args()

    palabras = leer_json(a.palabras)
    estilo = leer_json(a.estilo)
    minima = estilo["subtitulos"].get("duracion_minima_s", 0.4)

    if a.solo_srt or not a.frases:
        trozos = auto_trozos(palabras, estilo["subtitulos"].get("palabras_max", 3))
        validos = tiempos(trozos, palabras, minima)
        if not estilo["subtitulos"].get("puntuacion", True):
            quitar_puntuacion(validos)
        destino = Path(a.out)
        if destino.suffix != ".srt":
            destino.mkdir(parents=True, exist_ok=True)
            destino = destino / "subtitulos.srt"
        destino.parent.mkdir(parents=True, exist_ok=True)
        escribir_srt(validos, destino)
        aviso(f"Subtítulos .srt: {destino} ({len(validos)} trozos)")
        return

    trozos = leer_frases(a.frases)
    sub = estilo["subtitulos"]
    con_clave = sub.get("palabra_clave", True)
    if not con_clave:  # estilos sin palabra clave (Minimal): se ignoran los *asteriscos*
        for t in trozos:
            for tok in t["tokens"]:
                tok["clave"] = False
    avisos = alinear(trozos, palabras)
    maximo = sub.get("palabras_max", 3)
    for t in trozos:
        if len(t["tokens"]) > maximo:
            avisos.append(f"«{' '.join(x['texto'] for x in t['tokens'])}» tiene más de {maximo} palabras: pártelo con |")
    validos = tiempos(trozos, palabras, minima)
    if not sub.get("puntuacion", True):
        quitar_puntuacion(validos)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    escribir_json(out / "subtitulos.json", [
        {"start": t["start"], "end": t["end"], "fin_frase": t["fin_frase"],
         "texto": " ".join(x["texto"] for x in t["tokens"]),
         "clave": [x["texto"] for x in t["tokens"] if x["clave"]],
         "palabras": [{"texto": x["texto"], "clave": x["clave"],
                       "start": palabras[x["idx"]]["start"] if x.get("idx") is not None else t["start"]}
                      for x in t["tokens"]]}
        for t in validos])
    escribir_srt(validos, out / "subtitulos.srt")
    if sub.get("motor") == "bloques":  # Neón lima y similares: bloques animados fotograma a fotograma
        from subtitulos_bloques import escribir_ass_bloques
        nb, nev, fam, resumen, avisos_b = escribir_ass_bloques(validos, palabras, estilo, out / "subtitulos.ass",
                                                              a.ancho, a.alto)
        aviso(f"Bloques animados: {nb} bloques, {nev} eventos, fuente {fam}.")
        for linea in resumen:
            print("   " + linea)
        avisos += avisos_b
    else:
        escribir_ass(validos, estilo, out / "subtitulos.ass", a.ancho, a.alto)
    claves = [x["texto"] for t in validos for x in t["tokens"] if x["clave"]]
    if con_clave:
        aviso(f"{len(validos)} trozos. Palabras clave ({len(claves)}): {', '.join(claves)}")
    else:
        aviso(f"{len(validos)} trozos (estilo sin palabra clave).")
    for av in avisos:
        aviso("⚠️ " + av)


if __name__ == "__main__":
    main()
