# /// script
# requires-python = ">=3.10"
# ///
"""Subtítulos del vídeo cortado, en uno de los 8 estilos DECODIK, con la palabra clave resaltada.

Uso:
    uv run subtitulos.py <carpeta del vídeo> [--estilo clave] [--claves claves.json]
                         [--color-clave FFD400] [--max-palabras N] [--sin-video]

Estilos (ver references/estilos-subtitulos.md):
    clave (por defecto) · serif · frase · impacto · caja · condensada · mixta · minimo

Palabras clave: las elige Claude y las escribe en 06_entrega/trabajo/claves.json:
    {"claves": ["olímpica", "Stanford", "62 créditos", "veterinaria#1"]}
«palabra#2» marca solo la 2.ª vez que se dice. Si no hay archivo, se resaltan las cifras y los
nombres propios que se pasaron a transcribir.py con --nombres.

Lee 06_entrega/trabajo/transcripcion.json y cortes.json (de cortar.py) y escribe ahí:
    subtitulos.ass        el estilo que ffmpeg pinta sobre el vídeo
    subtitulos.srt        los bloques sin estilo, para entregar o subir a la red
    subtitulado.mp4       corte.mp4 con los subtítulos pintados, para revisarlo (salvo --sin-video)

Colores y letras de la marca DECODIK por defecto (ver marca.py y references/marca-decodik.md). Las
letras (Figtree, Anton, Bebas Neue, Inter, Inter Display; licencia OFL) se descargan de su repositorio oficial
la primera vez (ver fuentes.py). Códigos: 0 bien · 1 error · 2 falta algo · 3 sin red.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import color  # noqa: E402
import fuentes  # noqa: E402
import marca  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Lienzo del ASS = vídeo final.
ANCHO, ALTO = 1080, 1920
MIN_CUADROS = 4                      # ningún bloque dura menos de 4 cuadros
PAUSA_CORTE = 0.25                   # una pausa así en el vídeo cortado abre bloque nuevo
SIGNOS_FIN = (".", ",", ";", ":", "?", "!", "…")
# Palabras de enlace con las que no debe acabar un bloque.
ENLACES = {"y", "e", "o", "u", "ni", "de", "del", "a", "al", "en", "con", "por", "para", "sin", "que", "el", "la",
           "los", "las", "un", "una", "unos", "unas", "lo", "mi", "tu", "su", "se", "me", "te", "le", "les", "es",
           "como", "pero", "si", "mas", "muy", "and", "the", "of", "to", "in"}

# Los 8 estilos. Base del texto al 66 % de la altura (zona segura de TikTok y Reels: lejos de
# la descripción de abajo y de los botones de la derecha); «minimo» va centrado.
ESTILOS = {
    # Estilo por defecto = estilo de subtítulos de la marca DECODIK: Figtree ExtraBold, Crema,
    # contorno fino Tinta y la palabra clave en Amarillo Decodik.
    "clave": {
        "fuente": "Figtree ExtraBold", "archivos": ["Figtree-ExtraBold.ttf"], "tam": 82,
        "contorno": 3, "sombra": 2, "max": 3, "clave": {"rol": "clave", "escala": 108},
    },
    "serif": {
        "fuente": "Georgia", "archivos": [], "tam": 68, "cursiva": 1, "contorno": 2, "sombra": 3, "max": 4,
        "clave": {"escala": 160, "cursiva": 0, "negrita": 1},
    },
    "frase": {
        "fuente": "Figtree SemiBold", "archivos": ["Figtree-SemiBold.ttf"], "tam": 52, "contorno": 2, "sombra": 2,
        "max": 8, "margen": 150, "clave": None,
    },
    "impacto": {
        "fuente": "Inter Display Black", "archivos": ["InterDisplay-BlackItalic.ttf"], "tam": 92, "cursiva": 1,
        "contorno": 6, "mayus": True, "max": 3, "margen": 110, "clave": {"rol": "acento2"},
    },
    "caja": {
        "fuente": "Figtree", "archivos": ["Figtree-Bold.ttf"], "tam": 58, "negrita": 1, "rol_texto": "texto_caja",
        "rol_caja": "caja", "contorno": 14, "max": 4, "margen": 150, "clave": None,
    },
    "condensada": {
        "fuente": "Anton", "archivos": ["Anton-Regular.ttf"], "tam": 104, "contorno": 3, "sombra": 3,
        "mayus": True, "max": 3, "clave": {"rol": "clave"},
    },
    "mixta": {
        "fuente": "Figtree Medium", "archivos": ["Figtree-Medium.ttf", "Figtree-Black.ttf"], "tam": 54,
        "contorno": 2, "sombra": 2, "max": 8, "margen": 150, "clave": {"fuente": "Figtree Black"},
    },
    "minimo": {
        "fuente": "Figtree Medium", "archivos": ["Figtree-Medium.ttf"], "tam": 40, "contorno": 1, "sombra": 2,
        "max": 10, "margen": 200, "centrado": True, "clave": None,
    },
}
BASE_Y = 0.66


# ---------- tiempos ----------

def palabras_en_corte(transcripcion: dict, cortes: dict) -> list[dict]:
    """Cada palabra que sobrevive al corte, con su tiempo en el vídeo cortado."""
    por_clip = {c["archivo"]: [w for f in c["frases"] for w in f["palabras"]] for c in transcripcion["clips"]}
    # Muletillas y palabras repetidas quitadas por cortar.py: pueden caer dentro de un tramo,
    # pero no se subtitulan.
    quitadas = {(d["clip"], round(d["inicio"], 3)) for d in cortes.get("descartes", [])
                if d["motivo"] in ("muletilla", "palabra repetida")}
    salida = []
    for s in cortes["segmentos"]:
        for w in por_clip.get(s["clip"], []):
            if (s["clip"], round(w["inicio"], 3)) in quitadas:
                continue
            centro = (w["inicio"] + w["fin"]) / 2
            if not (s["inicio"] <= centro < s["fin"]):
                continue
            ini = s["salida_inicio"] + max(w["inicio"], s["inicio"]) - s["inicio"]
            fin = s["salida_inicio"] + min(w["fin"], s["fin"]) - s["inicio"]
            salida.append({"p": w["p"], "inicio": round(ini, 3), "fin": round(max(fin, ini + 0.05), 3)})
    return salida


def bloques(palabras: list[dict], max_palabras: int) -> list[list[dict]]:
    """Agrupa palabras en bloques de como mucho max_palabras palabras visibles (un nombre como
    «Eileen Gu» cuenta como dos). Abre bloque nuevo en puntuación y en pausas. Si un bloque se
    corta solo por llegar al máximo, no termina en palabras de enlace («y», «de», «en lo»…):
    pasan a abrir el bloque siguiente («Eileen Gu» / «y es esquiadora»)."""
    def visibles(ws: list[dict]) -> int:
        return sum(len(w["p"].split()) for w in ws)

    def es_enlace(w: dict) -> bool:
        return norm(w["p"]) in ENLACES and not w["p"].endswith(SIGNOS_FIN)

    def cerrar_por_maximo(actual: list[dict]) -> list[dict]:
        """Cierra el bloque y devuelve las palabras de enlace del final, que abren el siguiente."""
        corte = len(actual)
        while corte > 1 and es_enlace(actual[corte - 1]):
            corte -= 1
        grupos.append(actual[:corte])
        return actual[corte:]

    grupos, actual = [], []
    for i, w in enumerate(palabras):
        if actual and visibles(actual) + len(w["p"].split()) > max_palabras:
            actual = cerrar_por_maximo(actual)
        actual.append(w)
        siguiente = palabras[i + 1] if i + 1 < len(palabras) else None
        frase_termina = (w["p"].endswith(SIGNOS_FIN) or siguiente is None
                         or siguiente["inicio"] - w["fin"] > PAUSA_CORTE)
        if frase_termina:
            grupos.append(actual)
            actual = []
        elif visibles(actual) >= max_palabras:
            actual = cerrar_por_maximo(actual)
    if actual:
        grupos.append(actual)
    return grupos


def limpiar(palabra: str, estilo: str) -> str:
    """Sin puntos ni comas al final (estilo de las redes); se dejan ¿?¡! porque cambian el sentido.
    En «frase», «mixta» y «minimo», que son frases enteras, se deja la puntuación."""
    if estilo in ("frase", "mixta", "minimo"):
        return palabra
    return palabra.rstrip(".,;:…")


# ---------- palabras clave ----------

def norm(texto: str) -> str:
    t = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in t if c.isalnum() or c == " ").strip()


def marcar_claves(palabras: list[dict], claves: list[str]) -> int:
    """Marca w["clave"]=True en las palabras que coinciden con la lista. Una clave puede tener
    varias palabras («62 créditos») y «#n» para quedarse solo con la n-ésima vez que se dice."""
    # Se compara palabra a palabra visible: «Eileen Gu» viene como una sola entrada de la
    # transcripción pero son dos palabras, y la clave puede ser «Eileen Gu» o solo «Gu».
    fichas, de_quien = [], []
    for i, w in enumerate(palabras):
        for t in norm(w["p"]).split():
            fichas.append(t)
            de_quien.append(i)
    marcadas = 0
    for c in claves:
        texto, _, n = c.partition("#")
        objetivo = norm(texto).split()
        if not objetivo:
            continue
        vez = 0
        for i in range(len(fichas) - len(objetivo) + 1):
            if fichas[i:i + len(objetivo)] != objetivo:
                continue
            vez += 1
            if n and str(vez) != n.strip():
                continue
            for j in sorted(set(de_quien[i:i + len(objetivo)])):
                if not palabras[j].get("clave"):
                    palabras[j]["clave"] = True
                    marcadas += 1
    return marcadas


def claves_automaticas(palabras: list[dict], nombres: str) -> list[str]:
    """Sin claves.json: cifras y nombres propios dados a transcribir.py."""
    auto = {w["p"] for w in palabras if re.search(r"\d", w["p"])}
    auto |= {n.strip() for n in nombres.split(",") if n.strip()}
    return sorted(auto)


# ---------- formatos ----------

def t_ass(seg: float) -> str:
    cs = round(seg * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def t_srt(seg: float) -> str:
    ms = round(seg * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def sombra_ass(hexrgb: str, modo: str, alfa: str = "60") -> str:
    """Color de sombra (con transparencia) en formato ASS."""
    return "&H" + alfa + color.color_texto(hexrgb, modo)[4:]


def estilo_ass(nombre: str, e: dict, modo: str, max_override: int | None, colores: dict) -> tuple[str, dict]:
    """Devuelve la línea Style del ASS y los datos del estilo ya resueltos, con los colores de la
    marca (DECODIK por defecto; ver marca.py): nunca blanco ni negro puros."""
    margen = e.get("margen", 120)
    centrado = e.get("centrado", False)
    texto = color.color_texto(colores[e.get("rol_texto", "texto")], modo)
    if "rol_caja" in e:
        # Caja opaca (BorderStyle 3): el color de la caja va en OutlineColour.
        borde = fondo = color.color_texto(colores[e["rol_caja"]], modo)
        estilo_borde = 3
    else:
        borde, fondo, estilo_borde = color.color_texto(colores["contorno"], modo), sombra_ass(colores["contorno"], modo), 1
    linea = (f"Style: {nombre},{e['fuente']},{e['tam']},{texto},{texto},{borde},{fondo},"
             f"{-1 if e.get('negrita') else 0},{-1 if e.get('cursiva') else 0},0,0,"
             f"{e.get('escala_x', 100)},100,{e.get('espaciado', 0)},0,{estilo_borde},"
             f"{e.get('contorno', 0)},{e.get('sombra', 0)},{5 if centrado else 2},{margen},{margen},"
             f"{0 if centrado else round(ALTO * (1 - BASE_Y))},1")
    return linea, {**e, "max": max_override or e["max"]}


def texto_bloque(g: list[dict], nombre: str, e: dict, modo: str, colores: dict, color_clave: str | None) -> str:
    """Texto ASS del bloque, con la palabra clave resaltada según el estilo. Regla de la marca:
    una sola palabra (o grupo seguido de palabras) destacada por subtítulo."""
    clave = e.get("clave")
    partes = []
    estado = "antes"          # antes → dentro (resaltando) → despues (ya hubo una)
    for w in g:
        t = limpiar(w["p"], nombre)
        if e.get("mayus"):
            t = t.upper()
        t = t.replace("{", "(").replace("}", ")")
        es_clave = bool(w.get("clave")) and clave is not None and estado != "despues"
        if estado == "dentro" and not w.get("clave"):
            estado = "despues"
            es_clave = False
        if es_clave:
            estado = "dentro"
            tags = ""
            c = color_clave or (colores[clave["rol"]] if clave.get("rol") else None)
            if c:
                tags += f"\\c{color.color_texto(c, modo)}&"
            if clave.get("escala"):
                tags += f"\\fscx{clave['escala'] * e.get('escala_x', 100) // 100}\\fscy{clave['escala']}"
            if clave.get("fuente"):
                tags += f"\\fn{clave['fuente']}"
            if "cursiva" in clave:
                tags += f"\\i{clave['cursiva']}"
            if "negrita" in clave:
                tags += f"\\b{clave['negrita']}"
            t = "{" + tags + "}" + t + "{\\r}"
        partes.append(t)
    return " ".join(partes)


def escribir(grupos: list[list[dict]], duracion: float, fps: int, trabajo: Path, modo: str,
             nombre: str, e: dict, linea_estilo: str, color_clave: str | None, colores: dict) -> None:
    minimo = MIN_CUADROS / fps
    # Cada bloque se ve desde su primera palabra hasta que empieza el siguiente (o un poco
    # después de su última palabra si hay pausa), y nunca menos de 4 cuadros.
    tiempos = []
    for k, g in enumerate(grupos):
        ini = g[0]["inicio"]
        sig = grupos[k + 1][0]["inicio"] if k + 1 < len(grupos) else duracion
        fin = min(g[-1]["fin"] + 0.25, sig)
        fin = max(fin, min(ini + minimo, sig))
        tiempos.append((ini, fin))

    ass = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {ANCHO}", f"PlayResY: {ALTO}",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        linea_estilo,
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    srt = []
    for k, (g, (ini, fin)) in enumerate(zip(grupos, tiempos), 1):
        srt += [str(k), f"{t_srt(ini)} --> {t_srt(fin)}", " ".join(limpiar(w["p"], nombre) for w in g), ""]
        ass.append(f"Dialogue: 0,{t_ass(ini)},{t_ass(fin)},{nombre},,0,0,0,,{texto_bloque(g, nombre, e, modo, colores, color_clave)}")

    (trabajo / "subtitulos.ass").write_text("\n".join(ass) + "\n", encoding="utf-8")
    (trabajo / "subtitulos.srt").write_text("\n".join(srt), encoding="utf-8")


def ruta_filtro(ruta: Path) -> str:
    """Escapa una ruta de Windows para usarla dentro de un filtro de ffmpeg."""
    return ruta.as_posix().replace(":", "\\:").replace("'", "\\'")


def todas_las_letras() -> list[str]:
    """Todas las letras de los estilos, más la de la hoja de revisión."""
    return sorted({a for e in ESTILOS.values() for a in e["archivos"]}
                  | {"InterDisplay-Bold.ttf", "Anton-Regular.ttf", "BebasNeue-Regular.ttf"})


def main() -> int:
    p = argparse.ArgumentParser(description="Subtítulos en uno de los 8 estilos DECODIK, con palabra clave.")
    p.add_argument("carpeta", type=Path, help="carpeta del vídeo")
    p.add_argument("--estilo", default="clave", choices=list(ESTILOS), help="estilo de subtítulos (por defecto clave)")
    p.add_argument("--claves", type=Path, help="JSON con las palabras clave (por defecto 06_entrega/trabajo/claves.json)")
    p.add_argument("--color-clave", help="color HEX de la palabra clave (por defecto, el de la marca)")
    p.add_argument("--max-palabras", type=int, help="palabras por bloque (por defecto, las del estilo)")
    p.add_argument("--sin-video", action="store_true", help="solo escribe .ass y .srt")
    args = p.parse_args()

    trabajo = args.carpeta.resolve() / "06_entrega" / "trabajo"
    for nombre_f in ("transcripcion.json", "cortes.json"):
        if not (trabajo / nombre_f).exists():
            print(f"Falta {trabajo / nombre_f}. Antes ejecuta transcribir.py y cortar.py.")
            return 2
    transcripcion = json.loads((trabajo / "transcripcion.json").read_text(encoding="utf-8"))
    cortes = json.loads((trabajo / "cortes.json").read_text(encoding="utf-8"))
    if "salida_inicio" not in cortes["segmentos"][0]:
        print("cortes.json es de una versión anterior. Vuelve a ejecutar cortar.py.")
        return 2

    nombre = args.estilo
    modo = cortes.get("color", {}).get("modo", "sdr")
    colores = marca.cargar(trabajo)
    linea, e = estilo_ass(nombre, ESTILOS[nombre], modo, args.max_palabras, colores)
    fps = cortes.get("fps", 30)
    palabras = palabras_en_corte(transcripcion, cortes)

    ruta_claves = args.claves or trabajo / "claves.json"
    if ruta_claves.exists():
        claves = json.loads(ruta_claves.read_text(encoding="utf-8")).get("claves", [])
        origen = ruta_claves.name
    else:
        claves = claves_automaticas(palabras, transcripcion.get("nombres", ""))
        origen = "automáticas: cifras y nombres"
    marcadas = marcar_claves(palabras, claves) if e.get("clave") else 0

    grupos = bloques(palabras, e["max"])
    duracion = cortes["segmentos"][-1]["salida_fin"]
    color_clave = args.color_clave.lstrip("#") if args.color_clave else None
    escribir(grupos, duracion, fps, trabajo, modo, nombre, e, linea, color_clave, colores)
    print(f"Marca: {marca.origen(trabajo)}.")
    print(f"Estilo «{nombre}»: {len(palabras)} palabras en {len(grupos)} bloques "
          f"(máximo {max(sum(len(w['p'].split()) for w in g) for g in grupos)} palabras visibles por bloque).")
    if e.get("clave"):
        print(f"Palabras clave ({origen}): {len(claves)} en la lista, {marcadas} palabras resaltadas.")
    else:
        print("Este estilo no resalta palabras clave.")
    print(f"  {trabajo / 'subtitulos.ass'}")
    print(f"  {trabajo / 'subtitulos.srt'}")

    carpeta_letras = fuentes.asegurar(todas_las_letras())
    (trabajo / "subtitulos.json").write_text(json.dumps({"estilo": nombre}, ensure_ascii=False), encoding="utf-8")
    if not args.sin_video:
        corte = trabajo / "corte.mp4"
        if not corte.exists():
            print("Falta corte.mp4. Ejecuta cortar.py sin --sin-video.")
            return 2
        salida = trabajo / "subtitulado.mp4"
        filtro = f"subtitles='{ruta_filtro(trabajo / 'subtitulos.ass')}':fontsdir='{ruta_filtro(carpeta_letras)}'"
        dec = {"modo": modo, "transferencia": cortes.get("color", {}).get("transferencia", "bt709")}
        r = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(corte), "-vf", filtro,
             *color.codec_cpu(dec, True), *color.etiquetas_salida(dec),
             "-c:a", "copy", "-movflags", "+faststart", str(salida)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if r.returncode != 0:
            print(f"No se pudieron pintar los subtítulos: {r.stderr.strip()[-500:]}")
            return 1
        print(f"  {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
