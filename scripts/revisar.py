"""Control de calidad técnico: formato, volumen y hoja de contacto con la zona segura dibujada.

Uso:
  python revisar.py --video 07_entrega/<tema>.mp4 [--red instagram|tiktok|shorts|todas]
"""
import argparse
from pathlib import Path

from comun import aviso, ffmpeg, medir_volumen, sondear

ZONAS = {"instagram": (220, 380, 140, 60), "tiktok": (160, 440, 160, 60),
         "shorts": (180, 400, 140, 60), "todas": (288, 672, 192, 120)}  # todas = banda común (hyperframes check)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--red", default="todas", choices=list(ZONAS))
    a = ap.parse_args()

    v = Path(a.video)
    info = sondear(v)
    problemas = []
    vertical = info["alto"] > info["ancho"]
    if vertical and (info["ancho"], info["alto"]) not in ((1080, 1920), (2160, 3840)):
        problemas.append(f"resolución {info['ancho']}×{info['alto']} (esperado 1080×1920)")
    if abs(info["fps"] - 30) > 0.1:
        problemas.append(f"{info['fps']} fps (esperado 30)")
    if not info["tiene_audio"]:
        problemas.append("no tiene audio")

    if info["tiene_audio"]:
        m = medir_volumen(v)
        lufs, pico = float(m["input_i"]), float(m["input_tp"])
        if abs(lufs + 14) > 1:
            problemas.append(f"volumen {lufs:.1f} LUFS (objetivo −14)")
        if pico > -1:
            problemas.append(f"pico {pico:.1f} dB (debe ser < −1)")
    else:
        lufs = pico = None

    # Hoja de contacto: 12 fotogramas, 4×3, con la zona segura en menta
    k = info["alto"] / 1920 if vertical else 1
    ar, ab, de, iz = (round(x * k) for x in ZONAS[a.red])
    W, H = info["ancho"], info["alto"]
    caja = (f"drawbox=x={iz}:y={ar}:w={W - iz - de}:h={H - ar - ab}:color=0x5DD7B9@0.9:t={max(4, round(6 * k))}"
            if vertical else "null")
    paso = max(info["duracion"] / 12, 0.1)
    hoja = v.parent / "hoja-de-contacto.jpg"
    ffmpeg(["-i", str(v), "-vf", f"fps=1/{paso:.3f},{caja},scale=270:-2,tile=4x3:padding=6:color=0x021020",
            "-frames:v", "1", str(hoja)])

    aviso(f"{v.name}: {info['ancho']}×{info['alto']}, {info['fps']} fps, {info['duracion']:.1f} s"
          + (f", {lufs:.1f} LUFS, pico {pico:.1f} dB" if lufs is not None else ""))
    aviso(f"Hoja de contacto (zona segura de {a.red} en menta): {hoja}")
    if problemas:
        aviso("⚠️ Revisar: " + "; ".join(problemas))
    else:
        aviso("✅ Técnicamente correcto. Falta la revisión visual (control-calidad.md).")


if __name__ == "__main__":
    main()
