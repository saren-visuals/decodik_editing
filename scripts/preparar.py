"""Pasada 0 · Prepara la toma: 30 fps, vertical 9:16 y audios para transcribir y mezclar.

Uso:
  python preparar.py --src <toma> --trabajo <proyecto>/06_trabajo [--res 1080|4k]
                     [--rotar 90|180|270] [--recorte 0.5] [--mantener] [--normalizar] [--espejo]
Si la toma es horizontal y no se indica --rotar/--recorte/--mantener, se para y guarda fotograma.jpg.
"""
import argparse
import sys
from pathlib import Path

from comun import FPS, aviso, codificador, escribir_json, ffmpeg, filtro_sdr, sondear


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--trabajo", required=True)
    ap.add_argument("--res", choices=["1080", "4k"], default="1080")
    ap.add_argument("--rotar", type=int, choices=[90, 180, 270])
    ap.add_argument("--recorte", type=float, help="Posición horizontal del recorte 9:16 (0 izquierda, 1 derecha)")
    ap.add_argument("--mantener", action="store_true", help="Mantener horizontal")
    ap.add_argument("--normalizar", action="store_true", help="Subir el volumen de una voz muy baja")
    ap.add_argument("--espejo", action="store_true", help="Voltear horizontalmente (toma en espejo)")
    a = ap.parse_args()

    src, trabajo = Path(a.src), Path(a.trabajo)
    trabajo.mkdir(parents=True, exist_ok=True)
    info = sondear(src)
    if not info["tiene_audio"]:
        aviso("La toma no tiene audio: no se podrá transcribir ni cortar por voz.")
    W, H = (2160, 3840) if a.res == "4k" else (1080, 1920)

    w, h = info["ancho"], info["alto"]
    sdr = filtro_sdr(info)
    if sdr:
        aviso("Toma en HDR: la paso a SDR para que los colores no salgan lavados.")
    filtros = list(sdr)
    if a.rotar:
        filtros.append({90: "transpose=1", 180: "transpose=1,transpose=1", 270: "transpose=2"}[a.rotar])
        if a.rotar in (90, 270):
            w, h = h, w
    if a.espejo:
        filtros.append("hflip")

    horizontal = w > h
    if horizontal and a.recorte is None and not a.mantener and not a.rotar:
        ffmpeg(["-ss", str(min(2.0, info["duracion"] / 2)), "-i", str(src), "-frames:v", "1",
                "-vf", ",".join(sdr + ["scale=960:-2", "format=yuvj420p"]), str(trabajo / "fotograma.jpg")])
        escribir_json(trabajo / "toma-info.json", info)
        aviso(f"La toma es horizontal ({w}×{h}). Mira {trabajo / 'fotograma.jpg'}:")
        aviso("  · si la persona sale tumbada → repite con --rotar 90 (o 270)")
        aviso("  · si sale derecha → repite con --recorte 0.5 (ajusta 0-1 para centrarla)")
        aviso("  · si quiere conservar el horizontal → --mantener")
        sys.exit(3)

    if a.mantener and horizontal:
        W, H = (H, W)
        filtros.append(f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2")
    elif horizontal or a.recorte is not None:
        pos = 0.5 if a.recorte is None else max(0.0, min(1.0, a.recorte))
        filtros.append(f"crop=ih*9/16:ih:(iw-ih*9/16)*{pos}:0")
        filtros.append(f"scale={W}:{H}")
    else:
        filtros.append(f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}")
    filtros += [f"fps={FPS}", "setsar=1", "format=yuv420p"]

    aviso(f"Preparando vídeo {W}×{H} a {FPS} fps (de {info['ancho']}×{info['alto']} a {info['fps']} fps)…")
    ffmpeg(["-i", str(src), "-vf", ",".join(filtros), *codificador(), "-an", str(trabajo / "vertical.mp4")])

    if info["tiene_audio"]:
        af = ["-af", "loudnorm=I=-16:TP=-2"] if a.normalizar else []
        ffmpeg(["-i", str(src), "-vn", *af, "-ac", "1", "-ar", "16000", str(trabajo / "audio16k.wav")])
        ffmpeg(["-i", str(src), "-vn", *af, "-ac", "1", "-ar", "48000", "-c:a", "pcm_s24le", str(trabajo / "audio48k.wav")])

    info.update({"salida": [W, H], "hdr_a_sdr": bool(sdr), "rotar": a.rotar, "recorte": a.recorte, "normalizar": a.normalizar})
    escribir_json(trabajo / "toma-info.json", info)
    aviso(f"Listo: vertical.mp4, audio16k.wav y audio48k.wav en {trabajo}")


if __name__ == "__main__":
    main()
