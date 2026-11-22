"""Pasada de color · aplica un look de cine (LUT .cube) + textura (grano, viñeta, halación suave).

Uso:
  python color.py --entrada <vídeo o imagen> --salida <archivo> [--lut decodik-cine | ruta.cube]
                  [--log-apple] [--intensidad 1.0] [--grano 0.05] [--vineta 0.35] [--halacion 0.25]
  python color.py --crear-luts     (regenera los .cube de {SKILL}/color/)
--log-apple: la toma está grabada en Apple Log (iPhone); primero la pasa a imagen normal (Rec.709).
Para comparar: --prueba 3.0 saca antes/después de ese segundo en <salida>-antes.jpg / -despues.jpg.
"""
import argparse
from pathlib import Path

import numpy as np

from comun import SKILL, aviso, codificador, ffmpeg

CARPETA = SKILL / "color"


def suave(x, a):
    """Curva en S suave (contraste) centrada en 0,5."""
    return 0.5 + (x - 0.5) * (1 + a) / (1 + a * np.abs(2 * x - 1))


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def crear_lut(nombre, fn, n=33):
    r = np.linspace(0, 1, n)
    b, g, rr = np.meshgrid(r, r, r, indexing="ij")
    rgb = np.stack([rr, g, b], -1).reshape(-1, 3)
    out = np.clip(fn(rgb), 0, 1)
    ruta = CARPETA / f"{nombre}.cube"
    with open(ruta, "w") as f:
        f.write(f'TITLE "{nombre} · Decodik"\nLUT_3D_SIZE {n}\n')
        for v in out:
            f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
    return ruta


def look_cine(rgb, sombras="#254B57", luces="#F3D9B1", contraste=0.35, saturacion=0.88, negros=0.035):
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
    x = suave(rgb, contraste)
    x = negros + x * (1 - negros * 1.4)                       # negros levantados, blancos suaves
    x = np.power(np.clip(x, 0, 1), 0.9)                         # medios un poco más abiertos
    l2 = x @ np.array([0.2126, 0.7152, 0.0722])
    x = l2[:, None] + (x - l2[:, None]) * saturacion          # saturación contenida
    s, h = hex2rgb(sombras), hex2rgb(luces)
    ws = np.clip(1 - lum * 2.2, 0, 1)[:, None] * 0.18         # sombras hacia petróleo
    wh = np.clip(lum * 1.8 - 0.8, 0, 1)[:, None] * 0.16       # luces hacia crema cálido
    objetivo = x @ np.array([0.2126, 0.7152, 0.0722])          # luminancia tras la curva
    x = x * (1 - ws) + (x * 0.4 + s * 0.6) * ws
    x = x * (1 - wh) + (x * 0.55 + h * 0.45) * wh
    actual = x @ np.array([0.2126, 0.7152, 0.0722])
    x = x * (objetivo / np.maximum(actual, 1e-4))[:, None]     # el tinte no oscurece ni aclara
    return x


def crear_luts():
    CARPETA.mkdir(exist_ok=True)
    crear_lut("decodik-cine", look_cine)
    crear_lut("decodik-cine-suave", lambda c: look_cine(c, contraste=0.2, saturacion=0.94, negros=0.02))
    crear_lut("decodik-noche", lambda c: look_cine(c, sombras="#021020", luces="#7EDEE3", contraste=0.45, saturacion=0.8, negros=0.045))
    aviso(f"LUTs creados en {CARPETA}: decodik-cine, decodik-cine-suave, decodik-noche")


def ruta_filtro(p):
    """Ruta para un filtro de ffmpeg: en Windows el «:» de «C:» separa opciones, hay que escaparlo."""
    return Path(p).as_posix().replace(":", r"\:")


def cadena(a):
    # Todo en RGB: las mezclas (intensidad, halación) en YUV tiñen de rosa la piel
    f = ["format=gbrp"]
    if a.log_apple:
        lut_log = CARPETA / "AppleLogToRec709.cube"
        if not lut_log.exists():
            raise SystemExit(f"Falta {lut_log}: descarga el LUT oficial «Apple Log to Rec.709» de developer.apple.com y ponlo en esa carpeta.")
        f.append(f"lut3d='{ruta_filtro(lut_log)}'")
    lut = Path(a.lut) if a.lut.endswith(".cube") else CARPETA / f"{a.lut}.cube"
    if not lut.exists():
        crear_luts()
    if a.intensidad >= 0.999:
        f.append(f"lut3d='{ruta_filtro(lut)}'")
    else:
        f.append(f"split[o][l];[l]lut3d='{ruta_filtro(lut)}'[g];[o][g]blend=all_expr='A*(1-{a.intensidad})+B*{a.intensidad}'")
    if a.halacion > 0:
        f.append(f"split[b][h];[h]curves=all='0/0 0.7/0 1/1',gblur=sigma=18,colorchannelmixer=rr=1:gg=0.55:bb=0.35[h2];[b][h2]blend=all_mode=screen:all_opacity={a.halacion}")
    if a.vineta > 0:
        f.append(f"vignette=angle={0.15 + a.vineta * 0.4:.2f}:mode=forward")
    if a.grano > 0:
        f.append(f"noise=alls={int(a.grano * 100)}:allf=t")
    f.append("format=yuv420p")
    return ",".join(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada")
    ap.add_argument("--salida")
    ap.add_argument("--lut", default="decodik-cine")
    ap.add_argument("--log-apple", action="store_true")
    ap.add_argument("--intensidad", type=float, default=1.0)
    ap.add_argument("--grano", type=float, default=0.05)
    ap.add_argument("--vineta", type=float, default=0.3)
    ap.add_argument("--halacion", type=float, default=0.25)
    ap.add_argument("--prueba", type=float)
    ap.add_argument("--crear-luts", action="store_true")
    a = ap.parse_args()
    if a.crear_luts:
        crear_luts()
        return
    filtro = cadena(a)
    ent, sal = Path(a.entrada), Path(a.salida)
    es_imagen = ent.suffix.lower() in (".png", ".jpg", ".jpeg")
    if a.prueba is not None and not es_imagen:
        base = sal.with_suffix("")
        ffmpeg(["-ss", str(a.prueba), "-i", str(ent), "-frames:v", "1", f"{base}-antes.jpg"])
        ffmpeg(["-ss", str(a.prueba), "-i", str(ent), "-frames:v", "1", "-filter_complex", f"[0:v]{filtro}", f"{base}-despues.jpg"])
        aviso(f"Prueba: {base}-antes.jpg y {base}-despues.jpg")
        return
    if es_imagen:
        ffmpeg(["-i", str(ent), "-filter_complex", f"[0:v]{filtro}", "-frames:v", "1", str(sal)])
    else:
        ffmpeg(["-i", str(ent), "-filter_complex", f"[0:v]{filtro}[v]", "-map", "[v]", "-map", "0:a?", *codificador(), "-c:a", "copy", str(sal)])
    aviso(f"Color aplicado ({a.lut}): {sal}")


if __name__ == "__main__":
    main()
