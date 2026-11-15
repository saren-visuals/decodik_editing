# /// script
# requires-python = ">=3.10"
# ///
"""Textos en pantalla del reel: gancho al principio, cifras grandes y CTA al final.

Uso:
    uv run textos.py <carpeta del vídeo> [--color-clave FFD400]

Lee 06_entrega/trabajo/textos.json (lo escribe Claude y lo aprueba el talento), la transcripción
y cortes.json, y escribe 06_entrega/trabajo/textos.ass, que render.py pinta encima de los subtítulos.

textos.json:
    {
     "gancho": {"texto": "No eligió una sola etiqueta", "clave": "una sola"},
     "cifras": [{"texto": "62", "detalle": "créditos", "en": "62"}],
     "cta":    {"texto": "Guárdalo para cuando te pregunten qué eres", "clave": "qué eres"}
    }

- gancho: visible desde el fotograma 0 hasta que acaba la primera frase (entre 2 y 4 s), arriba.
  "hasta": segundos, para fijarlo a mano.
- cifras: aparece grande cuando se dice la palabra de "en" (admite «palabra#2»), ~1,3 s.
- cta: los últimos "segundos" del vídeo (por defecto 2,5 s), arriba, entrando con un fundido.
Cualquiera de los tres se puede omitir. Códigos: 0 bien · 2 falta algo o una cifra no se encuentra.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import color  # noqa: E402
import marca  # noqa: E402
from subtitulos import ALTO, ANCHO, SIGNOS_FIN, norm, palabras_en_corte, t_ass  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Marca DECODIK: Anton (en mayúsculas) para ganchos y textos grandes, Bebas Neue para etiquetas.
LETRA = marca.FUENTES["grande"][0]
LETRA_ETIQUETA = marca.FUENTES["etiqueta"][0]
Y_ARRIBA = round(ALTO * 0.12)    # gancho y CTA: justo por debajo de la barra de arriba de TikTok/Reels, sin tapar los ojos
Y_CIFRA = round(ALTO * 0.58)     # cifra: debajo de la cara, donde van los subtítulos (que se apartan mientras se ve)
GANCHO_MIN, GANCHO_MAX = 2.0, 4.0
CIFRA_DURA = 1.3


def resaltar(texto: str, clave: str | None, c_clave: str, mayus: bool = False) -> str:
    t = texto.upper() if mayus else texto
    if not clave:
        return t
    k = clave.upper() if mayus else clave
    i = t.find(k)
    if i < 0:
        i = t.lower().find(k.lower())
    if i < 0:
        print(f"  ! La palabra clave «{clave}» no está en «{texto}»: se pinta sin resaltar.")
        return t
    return t[:i] + "{\\c" + c_clave + "&}" + t[i:i + len(k)] + "{\\r}" + t[i + len(k):]


def momento(palabras: list[dict], en: str) -> float | None:
    """Segundo del vídeo cortado en que se dice `en` (admite «palabra#n» y varias palabras)."""
    texto, _, n = en.partition("#")
    objetivo = norm(texto).split()
    fichas = [(t, w["inicio"]) for w in palabras for t in norm(w["p"]).split()]
    vez = 0
    for i in range(len(fichas) - len(objetivo) + 1):
        if [f[0] for f in fichas[i:i + len(objetivo)]] == objetivo:
            vez += 1
            if not n or str(vez) == n.strip():
                return fichas[i][1]
    return None


def fin_primera_frase(palabras: list[dict]) -> float:
    for k, w in enumerate(palabras):
        if w["p"].endswith(SIGNOS_FIN) and w["fin"] >= GANCHO_MIN:
            return min(w["fin"] + 0.2, GANCHO_MAX)
        if k + 1 < len(palabras) and palabras[k + 1]["inicio"] - w["fin"] > 0.25 and w["fin"] >= GANCHO_MIN:
            return min(w["fin"] + 0.2, GANCHO_MAX)
    return GANCHO_MAX


def main() -> int:
    p = argparse.ArgumentParser(description="Gancho, cifras grandes y CTA del reel.")
    p.add_argument("carpeta", type=Path, help="carpeta del vídeo")
    p.add_argument("--color-clave", help="color HEX de lo resaltado (por defecto, el de la marca: Amarillo Decodik)")
    args = p.parse_args()

    trabajo = args.carpeta.resolve() / "06_entrega" / "trabajo"
    origen = trabajo / "textos.json"
    if not origen.exists():
        print(f"No hay {origen}: el vídeo sale sin gancho, cifras ni CTA.")
        (trabajo / "textos.ass").unlink(missing_ok=True)
        (trabajo / "textos-huecos.json").unlink(missing_ok=True)
        return 0
    for f in ("transcripcion.json", "cortes.json"):
        if not (trabajo / f).exists():
            print(f"Falta {trabajo / f}. Antes ejecuta transcribir.py y cortar.py.")
            return 2
    textos = json.loads(origen.read_text(encoding="utf-8"))
    cortes = json.loads((trabajo / "cortes.json").read_text(encoding="utf-8"))
    palabras = palabras_en_corte(json.loads((trabajo / "transcripcion.json").read_text(encoding="utf-8")), cortes)
    duracion = cortes["segmentos"][-1]["salida_fin"]
    modo = cortes.get("color", {}).get("modo", "sdr")
    colores = marca.cargar(trabajo)
    claro = color.color_texto(colores["texto"], modo)
    tinta = color.color_texto(colores["contorno"], modo)
    sombra = "&H70" + tinta[4:]
    c_clave = color.color_texto((args.color_clave or colores["clave"]).lstrip("#"), modo)

    estilos = [
        # Arriba, centrado, 2 líneas como mucho.
        f"Style: Arriba,{LETRA},124,{claro},{claro},{tinta},{sombra},0,0,0,0,100,100,1,0,1,3,4,8,90,90,{Y_ARRIBA},1",
        f"Style: Cifra,{LETRA},400,{c_clave},{c_clave},{tinta},{sombra},0,0,0,0,100,100,0,0,1,4,8,5,60,60,0,1",
        f"Style: Detalle,{LETRA_ETIQUETA},84,{claro},{claro},{tinta},{sombra},0,0,0,0,100,100,2,0,1,2,4,5,60,60,0,1",
    ]
    eventos, resumen, errores, huecos = [], [], 0, []

    g = textos.get("gancho")
    if g and g.get("texto"):
        hasta = float(g.get("hasta") or fin_primera_frase(palabras))
        txt = resaltar(g["texto"], g.get("clave"), c_clave, mayus=True)
        # Entra con un pequeño golpe de escala y sale con un fundido corto.
        eventos.append(f"Dialogue: 2,{t_ass(0)},{t_ass(hasta)},Arriba,,0,0,0,,"
                       f"{{\\fad(0,200)\\fscx92\\fscy92\\t(0,140,\\fscx100\\fscy100)}}{txt}")
        resumen.append(f"gancho 0,0–{hasta:.1f} s: «{g['texto']}»")

    for c in textos.get("cifras", []):
        cuando = momento(palabras, c.get("en") or c["texto"])
        if cuando is None:
            print(f"  ✗ No encuentro «{c.get('en') or c['texto']}» en la transcripción del vídeo cortado.")
            errores += 1
            continue
        fin = min(cuando + float(c.get("dura", CIFRA_DURA)), duracion)
        anim = "{\\fad(60,180)\\fscx40\\fscy40\\t(0,120,\\fscx112\\fscy112)\\t(120,220,\\fscx100\\fscy100)}"
        eventos.append(f"Dialogue: 3,{t_ass(cuando)},{t_ass(fin)},Cifra,,0,0,0,,"
                       f"{{\\pos({ANCHO // 2},{Y_CIFRA})}}{anim}{c['texto']}")
        if c.get("detalle"):
            eventos.append(f"Dialogue: 3,{t_ass(cuando)},{t_ass(fin)},Detalle,,0,0,0,,"
                           f"{{\\pos({ANCHO // 2},{Y_CIFRA + 225})\\fad(120,180)}}{c['detalle'].upper()}")
        resumen.append(f"cifra {cuando:.1f} s: «{c['texto']} {c.get('detalle', '')}»".rstrip())
        huecos.append([round(cuando, 3), round(fin, 3)])

    cta = textos.get("cta")
    if cta and cta.get("texto"):
        seg = float(cta.get("segundos", 2.5))
        ini = max(duracion - seg, 0)
        txt = resaltar(cta["texto"], cta.get("clave"), c_clave, mayus=True)
        eventos.append(f"Dialogue: 2,{t_ass(ini)},{t_ass(duracion)},Arriba,,0,0,0,,"
                       f"{{\\fad(250,0)\\move({ANCHO // 2},{Y_ARRIBA + 40},{ANCHO // 2},{Y_ARRIBA},0,250)\\an8}}{txt}")
        resumen.append(f"CTA {ini:.1f}–{duracion:.1f} s: «{cta['texto']}»")

    ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {ANCHO}", f"PlayResY: {ALTO}", "WrapStyle: 0",
           "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
           "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           *estilos, "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
           *eventos]
    (trabajo / "textos.ass").write_text("\n".join(ass) + "\n", encoding="utf-8")
    # Mientras se ve una cifra, el subtítulo se aparta: render.py lee estos huecos.
    (trabajo / "textos-huecos.json").write_text(json.dumps({"sin_subtitulos": huecos}), encoding="utf-8")
    print(f"{len(resumen)} textos en pantalla ({marca.origen(trabajo)}):")
    for r in resumen:
        print(f"  · {r}")
    print(f"  {trabajo / 'textos.ass'}")
    return 2 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
