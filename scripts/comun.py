"""Utilidades compartidas de los scripts de decodik-editor."""
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Windows usa cp1252 en la consola y revienta con ✅ ⚠️ o tildes: forzamos UTF-8.
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SKILL = Path(__file__).resolve().parent.parent
FPS = 30
AUDIO_FADE = 0.012  # 12 ms de fundido en cada empalme


def aviso(msg):
    print(f"[decodik] {msg}", flush=True)


def error(msg, codigo=1):
    print(f"[decodik] ERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(codigo)


def herramienta(nombre):
    ruta = shutil.which(nombre)
    if not ruta:
        error(f"No encuentro '{nombre}'. Ejecuta comprobar_equipo.py para instalarlo.")
    return ruta


def ejecutar(cmd, capturar=False):
    """Ejecuta un comando (lista). Devuelve stdout+stderr si capturar."""
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stderr[-3000:], file=sys.stderr)
        error(f"Falló: {' '.join(str(c) for c in cmd[:6])} …")
    return (r.stdout + r.stderr) if capturar else None


def ffmpeg(args, capturar=False):
    nivel = "info" if capturar else "error"
    return ejecutar([herramienta("ffmpeg"), "-hide_banner", "-y", "-loglevel", nivel, *args], capturar)


def version_ffmpeg():
    """Versión principal de ffmpeg (p. ej. 9). 0 si no se reconoce (compilaciones git)."""
    import re
    out = subprocess.run([herramienta("ffmpeg"), "-hide_banner", "-version"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    m = re.search(r"ffmpeg version n?(\d+)\.", out)
    return int(m.group(1)) if m else 0


def filtro_desde_archivo(ruta):
    """Opción para leer -filter_complex de un archivo: ffmpeg 7+ usa «-/filter_complex»
    (-filter_complex_script se eliminó en la 8); las versiones antiguas, la opción vieja."""
    v = version_ffmpeg()
    if v == 0 or v >= 7:
        return ["-/filter_complex", str(ruta)]
    return ["-filter_complex_script", str(ruta)]


def medir_volumen(ruta):
    """Mide LUFS integrados y pico real con loudnorm. Devuelve el dict de loudnorm."""
    import re
    out = ffmpeg(["-i", str(ruta), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capturar=True)
    bloques = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", out, re.S)
    if not bloques:
        error("No se pudo medir el volumen.")
    return json.loads(bloques[-1])


def sondear(ruta):
    """Devuelve dict con ancho, alto, fps, duracion, rotacion, tiene_audio."""
    out = subprocess.run(
        [herramienta("ffprobe"), "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(ruta)],
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    d = json.loads(out or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not v:
        error(f"'{ruta}' no tiene vídeo o no se puede leer.")
    num, den = (v.get("r_frame_rate") or "30/1").split("/")
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    rot = int(v.get("tags", {}).get("rotate", rot) or rot)
    w, h = int(v["width"]), int(v["height"])
    if abs(rot) % 180 == 90:
        w, h = h, w  # ffmpeg autorrota al decodificar
    return {
        "ancho": w, "alto": h,
        "fps": round(float(num) / float(den or 1), 3),
        "duracion": float(d.get("format", {}).get("duration") or v.get("duration") or 0),
        "rotacion": rot, "tiene_audio": a is not None,
        "hdr": v.get("color_transfer") in ("arib-std-b67", "smpte2084"),
        "transfer": v.get("color_transfer"),
    }


def filtro_sdr(info):
    """Si la toma es HDR (HLG del iPhone o PQ), devuelve el filtro que la pasa a SDR Rec.709
    para que no salga lavada. Lista vacía si ya es SDR."""
    if not info.get("hdr"):
        return []
    filtros = subprocess.run([herramienta("ffmpeg"), "-hide_banner", "-filters"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    if " zscale " not in filtros:
        aviso("La toma es HDR y este ffmpeg no tiene zscale: los colores pueden salir lavados. "
              "Instala la versión 'full' o 'essentials' de gyan.dev, o graba en SDR (Blackmagic Camera: SDR).")
        return []
    pico = "1000" if info.get("transfer") == "smpte2084" else "400"
    return [f"zscale=t=linear:npl={pico}", "format=gbrpf32le", "zscale=p=bt709",
            "tonemap=hable:desat=0", "zscale=t=bt709:m=bt709:r=tv"]


def codificador():
    """Elige el codificador H.264 más rápido disponible."""
    try:
        enc = subprocess.run([herramienta("ffmpeg"), "-hide_banner", "-encoders"],
                             capture_output=True, text=True).stdout
    except Exception:
        enc = ""
    if "h264_nvenc" in enc and _prueba_enc("h264_nvenc"):
        return ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "19", "-b:v", "0"]
    if platform.system() == "Darwin" and "h264_videotoolbox" in enc:
        return ["-c:v", "h264_videotoolbox", "-b:v", "16M"]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"]


def _prueba_enc(nombre):
    r = subprocess.run([herramienta("ffmpeg"), "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                        "color=c=black:s=256x256:d=0.1", "-c:v", nombre, "-f", "null", "-"],
                       capture_output=True)
    return r.returncode == 0


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def escribir_json(ruta, datos):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def a_rejilla(t):
    """Redondea un tiempo a la rejilla de fotogramas (1/30 s)."""
    return round(round(t * FPS) / FPS, 4)


def normalizar_palabra(w):
    import unicodedata
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return "".join(c for c in w if c.isalnum())
