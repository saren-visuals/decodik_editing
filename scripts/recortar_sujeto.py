"""Avanzado · Recorta al sujeto (mate en escala de grises) con RobustVideoMatting.

Uso:
  python recortar_sujeto.py --src 06_trabajo/cortado.mp4 --out 06_trabajo/mate.mp4 [--prueba 5.0]
Necesita PyTorch y el modelo (comprobar_equipo.py --nivel avanzado --descargar-modelo).
Modelo RVM: licencia GPL-3.0, https://github.com/PeterL1n/RobustVideoMatting
"""
import argparse
import subprocess
import time

import numpy as np

from comun import SKILL, aviso, error, ffmpeg, herramienta, sondear

MODELO = SKILL / "modelos" / "rvm_resnet50_fp32.torchscript"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prueba", type=float, help="Solo genera prueba-mate.jpg en ese segundo")
    a = ap.parse_args()

    import torch
    if not MODELO.exists():
        error("Falta el modelo. Ejecuta: comprobar_equipo.py --nivel avanzado --descargar-modelo")
    disp = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    modelo = torch.jit.load(str(MODELO), map_location=disp).eval()
    if disp == "cuda":
        modelo = torch.jit.freeze(modelo)

    info = sondear(a.src)
    W, H = info["ancho"], info["alto"]
    ratio = 0.25 if H >= 3000 else 0.4
    total = int(info["duracion"] * 30)

    entrada = [herramienta("ffmpeg"), "-v", "error"]
    if a.prueba is not None:
        entrada += ["-ss", str(a.prueba)]
    entrada += ["-i", a.src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    lector = subprocess.Popen(entrada, stdout=subprocess.PIPE)

    if a.prueba is not None:
        cuadro = np.frombuffer(lector.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
        lector.kill()
        with torch.no_grad():
            src = torch.from_numpy(cuadro).to(disp).permute(2, 0, 1)[None].float() / 255
            fgr, pha, *_ = modelo(src, *[None] * 4, ratio)
        alfa = pha[0, 0].cpu().numpy()[..., None]
        tablero = ((np.indices((H, W)).sum(0) // 40) % 2 * 80 + 60).astype(np.float32)[..., None].repeat(3, 2)
        img = (cuadro * alfa + tablero * (1 - alfa)).astype(np.uint8)
        ruta = a.out.replace(".mp4", "") + "-prueba.jpg"
        p = subprocess.Popen([herramienta("ffmpeg"), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-i", "-", "-vf", "scale=540:-2", ruta], stdin=subprocess.PIPE)
        p.communicate(img.tobytes())
        aviso(f"Prueba: {ruta} (busca agujeros o bordes raros)")
        return

    escritor = subprocess.Popen([herramienta("ffmpeg"), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray",
                                 "-s", f"{W}x{H}", "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                                 "-crf", "12", "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
    rec = [None] * 4
    t0, n = time.time(), 0
    with torch.no_grad():
        while True:
            buf = lector.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            src = torch.from_numpy(np.frombuffer(buf, np.uint8).reshape(H, W, 3)).to(disp).permute(2, 0, 1)[None].float() / 255
            fgr, pha, *rec = modelo(src, *rec, ratio)
            escritor.stdin.write((pha[0, 0] * 255).byte().cpu().numpy().tobytes())
            n += 1
            if n == 30:
                fps = n / (time.time() - t0)
                aviso(f"Velocidad: {fps:.1f} fotogramas/s → unos {total / fps / 60:.1f} min en total.")
            elif n % 300 == 0:
                aviso(f"{n}/{total}…")
    escritor.stdin.close()
    escritor.wait()
    aviso(f"Mate listo: {a.out} ({n} fotogramas en {time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
