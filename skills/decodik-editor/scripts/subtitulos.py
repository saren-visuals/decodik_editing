# /// script
# requires-python = ">=3.10"
# ///
"""Subtítulos del vídeo cortado: bloques de 1 a 4 palabras con la palabra que suena resaltada.

Uso:
    uv run subtitulos.py <carpeta del talento> [--max-palabras 4] [--color-activa FFD400] [--sin-video]

Lee 06_entrega/trabajo/transcripcion.json y cortes.json (de cortar.py), pasa el tiempo de cada
palabra al vídeo cortado y escribe en 06_entrega/trabajo/:

    subtitulos.ass        estilo «nativo + palabra a palabra» que ffmpeg pinta sobre el vídeo
    subtitulos.srt        bloques sin estilo, para entregar o subir a la red
    subtitulado.mp4       corte.mp4 con los subtítulos pintados, para revisarlo (salvo --sin-video)

La letra (Montserrat ExtraBold, licencia OFL) se descarga de su repositorio oficial la primera
vez y se guarda en ~/.cache/decodik/fuentes/. Códigos: 0 bien · 1 error · 2 falta algo · 3 sin red.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import color  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Lienzo del ASS = vídeo final.
ANCHO, ALTO = 1080, 1920
# Zona segura de TikTok/Reels: se evita el 20 % de abajo (descripción y música) y la franja
# derecha de botones. El texto va centrado con su base a ~66 % de la altura.
MARGEN_LATERAL = 130
BASE_Y = 0.66
TAMANO = 78
CONTORNO = 7
MIN_CUADROS = 4                      # ningún bloque dura menos de 4 cuadros
PAUSA_CORTE = 0.25                   # una pausa así en el vídeo cortado abre bloque nuevo
SIGNOS_FIN = (".", ",", ";", ":", "?", "!", "…")
FUENTE = {
    "familia": "Montserrat ExtraBold",
    "archivo": "Montserrat-ExtraBold.ttf",
    "url": "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-ExtraBold.ttf",
    "licencia_url": "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/OFL.txt",
}


def carpeta_fuentes() -> Path:
    return Path.home() / ".cache" / "decodik" / "fuentes"


def asegurar_fuente() -> Path:
    destino = carpeta_fuentes()
    destino.mkdir(parents=True, exist_ok=True)
    ttf = destino / FUENTE["archivo"]
    if not ttf.exists():
        print(f"  … Descargando la letra {FUENTE['familia']} (licencia OFL, solo la primera vez).")
        try:
            urllib.request.urlretrieve(FUENTE["url"], ttf)
            urllib.request.urlretrieve(FUENTE["licencia_url"], destino / "Montserrat-OFL.txt")
        except OSError as e:
            ttf.unlink(missing_ok=True)
            print(f"No se pudo descargar la letra ({e}). Revisa la conexión y vuelve a intentarlo.")
            sys.exit(3)
    return destino


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
    «Eileen Gu» cuenta como dos). Abre bloque nuevo en puntuación y en pausas."""
    def visibles(ws: list[dict]) -> int:
        return sum(len(w["p"].split()) for w in ws)

    grupos, actual = [], []
    for i, w in enumerate(palabras):
        if actual and visibles(actual) + len(w["p"].split()) > max_palabras:
            grupos.append(actual)
            actual = []
        actual.append(w)
        siguiente = palabras[i + 1] if i + 1 < len(palabras) else None
        cierra = (
            visibles(actual) >= max_palabras
            or w["p"].endswith(SIGNOS_FIN)
            or siguiente is None
            or siguiente["inicio"] - w["fin"] > PAUSA_CORTE
        )
        if cierra:
            grupos.append(actual)
            actual = []
    return grupos


def limpiar(palabra: str) -> str:
    """Estilo nativo: sin puntos ni comas al final; se dejan ¿?¡! porque cambian el sentido."""
    return palabra.rstrip(".,;:…")


# ---------- formatos ----------

def t_ass(seg: float) -> str:
    cs = round(seg * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def t_srt(seg: float) -> str:
    ms = round(seg * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def escribir(grupos: list[list[dict]], duracion: float, fps: int, activa: str, trabajo: Path, modo: str) -> None:
    """modo = "hdr" o "sdr" (de cortes.json): en HDR el texto se pone al blanco de referencia."""
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

    margen_v = round(ALTO * (1 - BASE_Y))
    blanco = color.color_texto("FFFFFF", modo)
    ass = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {ANCHO}", f"PlayResY: {ALTO}",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Nativo,{FUENTE['familia']},{TAMANO},{blanco},{blanco},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,"
        f"{CONTORNO},0,2,{MARGEN_LATERAL},{MARGEN_LATERAL},{margen_v},1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    srt = []
    c_activa = color.color_texto(activa, modo)
    for k, (g, (ini, fin)) in enumerate(zip(grupos, tiempos), 1):
        textos = [limpiar(w["p"]) for w in g]
        srt += [str(k), f"{t_srt(ini)} --> {t_srt(fin)}", " ".join(textos), ""]
        # Un evento por palabra: el bloque entero, con la palabra que suena en el color activo.
        for j, w in enumerate(g):
            w_ini = ini if j == 0 else w["inicio"]
            w_fin = g[j + 1]["inicio"] if j + 1 < len(g) else fin
            if w_fin - w_ini <= 0:
                continue
            partes = [(f"{{\\c{c_activa}&}}{t}{{\\c{blanco}&}}" if i == j else t) for i, t in enumerate(textos)]
            ass.append(f"Dialogue: 0,{t_ass(w_ini)},{t_ass(w_fin)},Nativo,,0,0,0,,{' '.join(partes)}")

    (trabajo / "subtitulos.ass").write_text("\n".join(ass) + "\n", encoding="utf-8")
    (trabajo / "subtitulos.srt").write_text("\n".join(srt), encoding="utf-8")


def ruta_filtro(ruta: Path) -> str:
    """Escapa una ruta de Windows para usarla dentro de un filtro de ffmpeg."""
    return ruta.as_posix().replace(":", "\\:").replace("'", "\\'")


def main() -> int:
    p = argparse.ArgumentParser(description="Subtítulos nativos palabra a palabra para el vídeo cortado.")
    p.add_argument("carpeta", type=Path, help="carpeta del talento")
    p.add_argument("--max-palabras", type=int, default=4, choices=range(1, 5), help="palabras por bloque (1-4)")
    p.add_argument("--color-activa", default="FFD400", help="color HEX de la palabra que suena (por defecto FFD400)")
    p.add_argument("--sin-video", action="store_true", help="solo escribe .ass y .srt")
    args = p.parse_args()

    trabajo = args.carpeta.resolve() / "06_entrega" / "trabajo"
    for nombre in ("transcripcion.json", "cortes.json"):
        if not (trabajo / nombre).exists():
            print(f"Falta {trabajo / nombre}. Antes ejecuta transcribir.py y cortar.py.")
            return 2
    transcripcion = json.loads((trabajo / "transcripcion.json").read_text(encoding="utf-8"))
    cortes = json.loads((trabajo / "cortes.json").read_text(encoding="utf-8"))
    if "salida_inicio" not in cortes["segmentos"][0]:
        print("cortes.json es de una versión anterior. Vuelve a ejecutar cortar.py.")
        return 2

    fps = cortes.get("fps", 30)
    palabras = palabras_en_corte(transcripcion, cortes)
    grupos = bloques(palabras, args.max_palabras)
    duracion = cortes["segmentos"][-1]["salida_fin"]
    modo = cortes.get("color", {}).get("modo", "sdr")
    escribir(grupos, duracion, fps, args.color_activa.lstrip("#"), trabajo, modo)
    print(f"{len(palabras)} palabras en {len(grupos)} bloques "
          f"(máximo {max(sum(len(w['p'].split()) for w in g) for g in grupos)} palabras visibles por bloque).")
    print(f"  {trabajo / 'subtitulos.ass'}")
    print(f"  {trabajo / 'subtitulos.srt'}")

    if not args.sin_video:
        fuentes = asegurar_fuente()
        corte = trabajo / "corte.mp4"
        if not corte.exists():
            print("Falta corte.mp4. Ejecuta cortar.py sin --sin-video.")
            return 2
        salida = trabajo / "subtitulado.mp4"
        filtro = f"subtitles='{ruta_filtro(trabajo / 'subtitulos.ass')}':fontsdir='{ruta_filtro(fuentes)}'"
        r = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(corte), "-vf", filtro,
             *color.codec_cpu({"modo": modo, "transferencia": cortes.get("color", {}).get("transferencia", "bt709")}, True),
             *color.etiquetas_salida({"modo": modo, "transferencia": cortes.get("color", {}).get("transferencia", "bt709")}),
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
