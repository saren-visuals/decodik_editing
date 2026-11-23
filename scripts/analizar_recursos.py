"""Cataloga los recursos de un proyecto y mide la ACTIVIDAD de cada vídeo segundo a segundo.

Uso:
  python analizar_recursos.py --proyecto <carpeta del proyecto>
Lee 03_recursos/ (vídeos, capturas y fotos) y escribe 03_recursos/indice-recursos.json:
  {"videos/IMG_1053.MOV": {"tipo": "video", "ancho": 1080, "alto": 1920, "orientacion": "vertical",
                          "hdr": false, "duracion": 12.4, "actividad": [0.8, 2.1, ...]},   # media cada 0,5 s
   "fotos/IMG_1229.JPG": {"tipo": "foto", "ancho": 816, "alto": 612, "orientacion": "horizontal"}}
«huellas»: miniatura de 8×14 en grises cada 0,5 s (para comprobar que un tramo es un plano estable).
«cortes»: instantes en los que el clip cambia de plano por dentro; el montaje nunca coge un tramo que los cruce
(se vería como una imagen cortada justo en el cambio).
La actividad es la diferencia media entre fotogramas seguidos (cuánto se mueve la imagen): sirve para que el
montaje coja el tramo donde la persona está más activa (la mitad de una subida de cuerda, el golpe, la carrera)
y no siempre el principio del clip, que suele ser el arranque o la cámara colocándose.
Orientación: «vertical» si ancho/alto ≤ 0,75 (va a pantalla completa); si no, «horizontal» (va en recuadro).
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

from comun import aviso, herramienta, sondear

VIDEO = {".mp4", ".mov", ".m4v", ".mkv", ".webm"}
FOTO = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
PASO = 0.5


def tamano_real(ruta):
    """Ancho y alto tal como se ven (con la rotación aplicada): decodifica un fotograma."""
    r = subprocess.run([herramienta("ffprobe"), "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:stream_side_data=rotation:stream_tags=rotate", "-of", "json", str(ruta)],
                       capture_output=True, text=True)
    s = json.loads(r.stdout)["streams"][0]
    w, h = s["width"], s["height"]
    rot = 0
    for sd in s.get("side_data_list", []):
        rot = sd.get("rotation", rot)
    rot = int(s.get("tags", {}).get("rotate", rot) or 0)
    return (h, w) if abs(rot) % 180 == 90 else (w, h)


def actividad(ruta, dur):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "ydif.txt"
        # la ruta del log va relativa (cwd = carpeta temporal) para no pelearse con «C:» dentro del filtro
        subprocess.run([herramienta("ffmpeg"), "-v", "error", "-i", str(Path(ruta).resolve()), "-vf",
                        "fps=10,scale=160:-2,signalstats,metadata=print:key=lavfi.signalstats.YDIF:file=ydif.txt",
                        "-an", "-f", "null", "-"], capture_output=True, cwd=d)
        texto = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    vals = [float(x) for x in re.findall(r"YDIF=([0-9.]+)", texto)]
    if vals:
        vals[0] = vals[1] if len(vals) > 1 else 0.0   # el primer fotograma no tiene anterior: no es movimiento
    n = max(1, int(dur / PASO))
    por = max(1, int(len(vals) / n)) if vals else 1
    return [round(sum(vals[i:i + por]) / max(1, len(vals[i:i + por])), 2) for i in range(0, por * n, por)][:n]


def huellas(ruta, dur):
    """Miniatura de 8×14 en grises cada 0,5 s: sirve para saber si el encuadre del principio y el del final de un
    tramo son el mismo (plano estable) o la cámara se ha ido a otra cosa (barrido, cambio de plano)."""
    r = subprocess.run([herramienta("ffmpeg"), "-v", "error", "-i", str(Path(ruta).resolve()), "-vf",
                        f"fps={1 / PASO},scale=8:14:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True)
    b = r.stdout
    return [list(b[i:i + 112]) for i in range(0, len(b) - 111, 112)][:max(1, int(dur / PASO) + 1)]


def cortes_internos(ruta):
    """Instantes en los que el clip cambia de plano por dentro (cortes o barridos bruscos de cámara)."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        subprocess.run([herramienta("ffmpeg"), "-v", "error", "-i", str(Path(ruta).resolve()), "-vf",
                        "scale=320:-2,select='gt(scene,0.30)',metadata=print:file=cortes.txt", "-an", "-f", "null", "-"],
                       capture_output=True, cwd=d)
        f = Path(d) / "cortes.txt"
        texto = f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""
    return [round(float(x), 2) for x in re.findall(r"pts_time:([0-9.]+)", texto)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proyecto", required=True)
    a = ap.parse_args()
    base = Path(a.proyecto) / "03_recursos"
    indice = {}
    for f in sorted(base.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(base).as_posix()
        ext = f.suffix.lower()
        if ext in VIDEO:
            info = sondear(f)
            w, h = tamano_real(f)
            indice[rel] = {"tipo": "video", "ancho": w, "alto": h, "orientacion": "vertical" if w / h <= 0.75 else "horizontal",
                           "hdr": bool(info.get("hdr")), "duracion": round(info["duracion"], 2),
                           "actividad": actividad(f, info["duracion"]), "cortes": cortes_internos(f),
                           "huellas": huellas(f, info["duracion"])}
            act = indice[rel]["actividad"]
            pico = act.index(max(act)) * PASO if act else 0
            aviso(f"{rel}: {w}×{h} {indice[rel]['orientacion']}, {info['duracion']:.1f} s, más activo hacia {pico:.1f} s, "
                  f"{len(indice[rel]['cortes'])} cortes internos {indice[rel]['cortes'][:6]}")
        elif ext in FOTO:
            w, h = tamano_real(f)
            indice[rel] = {"tipo": "foto", "ancho": w, "alto": h, "orientacion": "vertical" if w / h <= 0.75 else "horizontal"}
    (base / "indice-recursos.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")
    aviso(f"Índice: {base / 'indice-recursos.json'} ({len(indice)} recursos)")


if __name__ == "__main__":
    main()
