"""Formato «Mi historia · B-roll encima con subtítulos» · monta el vídeo a partir del storyboard aprobado.

Uso:
  python construir_historia.py --trabajo 06_trabajo [--storyboard storyboard-historia.json]
Después:
  python quemar_subtitulos.py --video 06_trabajo/historia_base.mp4 --ass 06_trabajo/subtitulos/subtitulos.ass --out 06_trabajo/historia_subs.mp4 [--fuentes <carpeta de la fuente>]
  python mezclar.py --video 06_trabajo/historia_subs.mp4 --voz 06_trabajo/voz_cortada.wav --out 07_entrega/<tema>.mp4

Cada plano dura hasta el siguiente (al fotograma exacto, 30 fps) y se monta así:
- camara: la toma cortada, tal cual.
- broll «completo»: el clip desde «in», a pantalla completa (recorte 9:16 centrado).
- broll «recuadro» (clips horizontales): el clip a lo ancho, en la parte de arriba (y = 22 %), sobre una copia suya
  desenfocada y oscurecida; así el subtítulo (a la altura del pecho) queda debajo, sobre el fondo, sin tapar el clip.
- foto: a pantalla completa con un zoom lento; si es horizontal (más ancha que 3:4), en recuadro sobre su fondo.
- «in»: "auto" coge el tramo más activo del clip y «modo»: "auto" decide recuadro o completo (ver tramos.py).
Los clips HDR del iPhone se pasan a SDR. Cortes secos. La voz sigue siempre por debajo (la pone mezclar.py).
"""
import argparse
import subprocess
from pathlib import Path

from comun import aviso, codificador, error, filtro_sdr, herramienta, leer_json, sondear
from tramos import resolver

FPS = 30
W, H = 1080, 1920
Y_RECUADRO = 0.22


def ff(args):
    r = subprocess.run([herramienta("ffmpeg"), "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        error(r.stderr[-800:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trabajo", required=True)
    ap.add_argument("--storyboard", default="storyboard-historia.json")
    a = ap.parse_args()
    tr = Path(a.trabajo)
    proyecto = tr.parent
    sb = leer_json(tr / a.storyboard)
    video = tr / "cortado.mp4"
    total = round(sondear(video)["duracion"] * FPS)
    planos = resolver(sb["planos"], proyecto, total / FPS)   # tramo más activo y recuadro/completo según orientación
    seg_dir = tr / "historia_planos"
    seg_dir.mkdir(exist_ok=True)
    enc = codificador()
    lista = []
    for k, p in enumerate(planos):
        f0 = round(p["t0"] * FPS)
        f1 = round(planos[k + 1]["t0"] * FPS) if k + 1 < len(planos) else total
        n = f1 - f0
        if n <= 0:
            continue
        out = seg_dir / f"p{k + 1:02d}.mp4"
        comun_salida = ["-frames:v", str(n), "-an", "-pix_fmt", "yuv420p", *enc, str(out)]
        cubrir = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
        if p["tipo"] == "camara":
            ff(["-ss", f"{f0 / FPS:.3f}", "-i", str(video), "-vf", f"fps={FPS},{cubrir}", *comun_salida])
        elif p["tipo"] == "broll":
            src = proyecto / p["src"]
            sdr = ",".join(filtro_sdr(sondear(src)))
            pre = (sdr + ",") if sdr else ""
            # tpad: si el clip se quedara corto, congela su último fotograma en vez de dejar negro
            relleno = "tpad=stop_mode=clone:stop_duration=10"
            if p["modo_usado"] == "recuadro":
                fc = (f"[0:v]{pre}fps={FPS},{relleno},split[a][b];"
                      f"[a]{cubrir},gblur=sigma=40,eq=brightness=-0.18:saturation=0.8[f];"
                      f"[b]scale={W}:-2,setsar=1[r];[f][r]overlay=0:{round(H * Y_RECUADRO)}")
                ff(["-ss", f"{p['in_usado']:.3f}", "-i", str(src), "-filter_complex", fc, *comun_salida])
            else:
                ff(["-ss", f"{p['in_usado']:.3f}", "-i", str(src), "-vf", f"{pre}fps={FPS},{relleno},{cubrir}", *comun_salida])
        else:   # foto con zoom lento; si es horizontal, en recuadro sobre su fondo desenfocado (nunca recortada)
            src = proyecto / p["src"]
            z = f"zoompan=z='1+0.06*on/{max(n - 1, 1)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1"
            if p["modo_usado"] == "recuadro":
                hf = round(W * 9 / 16 / 2) * 2   # alto del recuadro (aprox. 16:9 a lo ancho; la foto se ajusta dentro)
                fc = (f"[0:v]split[a][b];[a]{cubrir},gblur=sigma=40,eq=brightness=-0.18:saturation=0.8,"
                      f"zoompan=z=1:d=1:s={W}x{H}:fps={FPS}[f];"
                      f"[b]scale={W * 2}:-2,setsar=1,{z}:s={W}x{hf}:fps={FPS}[r];"
                      f"[f][r]overlay=0:{round(H * Y_RECUADRO)}")
                # la foto se escala a lo ancho conservando proporción: se calcula su alto real
                info = sondear(src)
                hr = round(W * info["alto"] / info["ancho"] / 2) * 2 if info.get("ancho") else hf
                fc = fc.replace(f"s={W}x{hf}", f"s={W}x{hr}")
                ff(["-loop", "1", "-i", str(src), "-filter_complex", fc, *comun_salida])
            else:
                zoom = (f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
                        f"{z}:s={W}x{H}:fps={FPS},setsar=1")
                ff(["-loop", "1", "-i", str(src), "-vf", zoom, *comun_salida])
        lista.append(out)
        aviso(f"plano {k + 1:02d} · {p['tipo']:6s} · {n / FPS:4.1f} s")
    concat = seg_dir / "lista.txt"
    concat.write_text("".join(f"file '{x.as_posix()}'\n" for x in lista), encoding="utf-8")
    base = tr / "historia_base.mp4"
    ff(["-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(base)])
    d = sondear(base)["duracion"]
    aviso(f"Base montada: {base} ({d:.2f} s; la toma dura {total / FPS:.2f} s)")


if __name__ == "__main__":
    main()
