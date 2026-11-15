# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy>=1.26", "opencv-python-headless>=4.9,<5"]
# ///
"""Recursos en pantalla: fotos, capturas o clips de 03_recursos/ cuando el talento los nombra.

Uso:
    uv run recursos.py <carpeta del vídeo>

Lee 06_entrega/trabajo/recursos.json (lo propone Claude y lo aprueba el talento):
    {"recursos": [
      {"archivo": "podio.jpg",  "en": "oro#1",      "modo": "tarjeta",  "dura": 2.0},
      {"archivo": "entreno.mov", "en": "periodista", "modo": "completo", "dura": 2.0}
    ]}

modo «completo»: el recurso ocupa toda la pantalla mientras sigue la voz (corte a B-roll).
modo «tarjeta»:  el recurso aparece en una tarjeta con esquinas redondeadas, entrando con un
                 deslizamiento y un fundido. REGLA: nunca tapa la cara del talento: se detecta la
                 cara en esos segundos y la tarjeta va debajo o encima de ella; si no cabe
                 legible, el recurso pasa a pantalla completa.
"en": palabra de la transcripción en que aparece (admite «palabra#2» y varias palabras).
"dura": segundos (por defecto 2). Los clips se usan sin su sonido; la voz del talento sigue.

Escribe 06_entrega/trabajo/recursos-plan.json (lo usa render.py) y prepara las tarjetas de
imagen en 06_entrega/trabajo/recursos/. Solo se usan archivos de 03_recursos/: material del
talento o con permiso. Códigos: 0 bien · 2 falta un archivo o una palabra.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import color  # noqa: E402
from subtitulos import ALTO, ANCHO, palabras_en_corte  # noqa: E402
from textos import momento  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

IMAGENES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp"}
VIDEOS = {".mp4", ".mov", ".m4v", ".mkv", ".webm"}
# Tarjeta: como mucho 820×440 px, con su parte de arriba al 38 % de la altura (sobre el pecho,
# entre la cara y los subtítulos, que van al 66 %).
TARJETA_ANCHO, TARJETA_ALTO = 820, 440
TARJETA_Y = round(ALTO * 0.38)
RADIO = 28
DURA = 2.0

def ejecutar(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def preparar_imagen(origen: Path, destino: Path, modo_color: str, completo: bool = False,
                    caja: tuple[int, int] = (TARJETA_ANCHO, TARJETA_ALTO)) -> tuple[int, int]:
    """Escala la imagen a la tarjeta, redondea las esquinas (con transparencia) y, si el vídeo es
    HDR, la convierte a BT.2020 + HLG con el blanco en el blanco de referencia (como los textos,
    ver color.py). Se guarda como PNG de 16 bits con alfa. La cuenta se hace con numpy: el filtro
    geq de ffmpeg trabaja en 8 bits y satura la curva HLG."""
    import numpy as np

    r = ejecutar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                  "-of", "csv=p=0", str(origen)])
    w, h = (int(x) for x in r.stdout.strip().split(",")[:2])
    if completo:
        # Pantalla completa: cubre los 1080×1920 y se recorta el centro, sin esquinas redondeadas.
        tw, th = ANCHO, ALTO
        escalado = f"scale={tw}:{th}:force_original_aspect_ratio=increase:flags=lanczos,crop={tw}:{th}"
    else:
        escala = min(caja[0] / w, caja[1] / h)
        tw, th = max(2, round(w * escala / 2) * 2), max(2, round(h * escala / 2) * 2)
        escalado = f"scale={tw}:{th}:flags=lanczos"
    lectura = subprocess.run(["ffmpeg", "-v", "error", "-i", str(origen), "-frames:v", "1",
                              "-vf", f"{escalado},format=rgba64le", "-f", "rawvideo", "-"],
                             capture_output=True)
    if lectura.returncode != 0:
        raise RuntimeError(f"no se pudo leer {origen.name}")
    px = np.frombuffer(lectura.stdout, dtype="<u2").reshape(th, tw, 4).astype(np.float64) / 65535.0
    rgb, alfa = px[..., :3], px[..., 3]

    if modo_color == "hdr":
        lineal = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
        m = np.array([[0.6274, 0.3293, 0.0433], [0.0691, 0.9195, 0.0114], [0.0164, 0.0880, 0.8956]])
        e = np.clip(0.2647 * (lineal @ m.T), 0.0, 1.0)
        a, b, c = 0.17883277, 0.28466892, 0.55991073
        rgb = np.where(e <= 1 / 12, np.sqrt(3 * e), a * np.log(np.maximum(12 * e - b, 1e-12)) + c)

    if not completo:
        # Esquinas redondeadas (con un píxel de suavizado en el borde).
        yy, xx = np.mgrid[0:th, 0:tw] + 0.5
        dx = np.maximum(np.abs(xx - tw / 2) - (tw / 2 - RADIO), 0)
        dy = np.maximum(np.abs(yy - th / 2) - (th / 2 - RADIO), 0)
        alfa = alfa * np.clip(RADIO - np.hypot(dx, dy) + 0.5, 0.0, 1.0)

    salida = np.dstack([np.clip(rgb, 0, 1), alfa])
    datos = (salida * 65535.0 + 0.5).astype("<u2").tobytes()
    escritura = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba64le",
                                "-s", f"{tw}x{th}", "-i", "-", "-frames:v", "1", str(destino)], input=datos,
                               capture_output=True)
    if escritura.returncode != 0:
        raise RuntimeError(f"no se pudo guardar la tarjeta de {origen.name}")
    return tw, th


# ---------- la cara no se tapa nunca ----------

# Zona útil para una tarjeta: por debajo de la barra de arriba de TikTok/Reels y por encima de
# los subtítulos (base al 66 % de la altura; se reservan ~110 px para el texto).
ZONA_ARRIBA = round(ALTO * 0.08)
ZONA_ABAJO = round(ALTO * 0.66) - 110
SEPARACION = 30          # px libres entre la cara y la tarjeta
TARJETA_MIN_ALTO = 200   # por debajo de esto la tarjeta no se lee: pasa a pantalla completa
MUESTRAS = 5             # fotogramas que se miran en el tiempo de cada tarjeta


def fotograma_gris(cortes: dict, brutos: Path, t: float):
    """Fotograma del vídeo cortado en el segundo t (sacado del bruto), en gris y a 540×960."""
    import numpy as np

    for s in cortes["segmentos"]:
        if s["salida_inicio"] <= t < s["salida_fin"]:
            t_bruto = s["inicio"] + (t - s["salida_inicio"])
            r = subprocess.run(
                ["ffmpeg", "-v", "error", "-ss", f"{t_bruto:.3f}", "-i", str(brutos / s["clip"]), "-frames:v", "1",
                 "-vf", "scale=540:960:force_original_aspect_ratio=increase,crop=540:960,format=gray",
                 "-f", "rawvideo", "-"], capture_output=True)
            if r.returncode == 0 and len(r.stdout) == 540 * 960:
                return np.frombuffer(r.stdout, dtype=np.uint8).reshape(960, 540)
    return None


def zona_de_la_cara(cortes: dict, brutos: Path, ini: float, fin: float) -> tuple[int, int] | None:
    """Franja vertical (arriba, abajo) en px de 1920 que ocupa la cara mientras dura la tarjeta,
    con margen para el pelo y la barbilla. None si no se ve ninguna cara."""
    import cv2

    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    arriba, abajo = None, None
    for i in range(MUESTRAS):
        t = ini + (fin - ini) * (i + 0.5) / MUESTRAS
        gris = fotograma_gris(cortes, brutos, t)
        if gris is None:
            continue
        caras = detector.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        if len(caras) == 0:
            continue
        x, y, w, h = max(caras, key=lambda c: c[2] * c[3])   # la cara más grande es la del talento
        sup, inf = (y - 0.35 * h) * 2, (y + 1.2 * h) * 2      # pelo y barbilla; ×2 para pasar a 1920
        arriba = sup if arriba is None else min(arriba, sup)
        abajo = inf if abajo is None else max(abajo, inf)
    if arriba is None:
        return None
    return max(0, round(arriba)), min(ALTO, round(abajo))


def hueco_para_tarjeta(cara: tuple[int, int] | None) -> tuple[int, int] | None:
    """El trozo de pantalla libre más alto (debajo o encima de la cara) para la tarjeta."""
    if cara is None:
        # Sin cara a la vista (p. ej. un plano sin el talento): se usa la posición de siempre,
        # pero suponiendo una cara en la zona habitual para no taparla si el detector falló.
        cara = (round(ALTO * 0.12), round(ALTO * 0.45))
    debajo = (cara[1] + SEPARACION, ZONA_ABAJO)
    encima = (ZONA_ARRIBA, cara[0] - SEPARACION)
    mejor = max(debajo, encima, key=lambda z: z[1] - z[0])
    return mejor if mejor[1] - mejor[0] >= TARJETA_MIN_ALTO else None


def main() -> int:
    p = argparse.ArgumentParser(description="Recursos en pantalla (B-roll y tarjetas) anclados a palabras.")
    p.add_argument("carpeta", type=Path, help="carpeta del vídeo")
    args = p.parse_args()

    video = args.carpeta.resolve()
    trabajo = video / "06_entrega" / "trabajo"
    plan_f = trabajo / "recursos-plan.json"
    origen = trabajo / "recursos.json"
    if not origen.exists():
        plan_f.unlink(missing_ok=True)
        print("No hay recursos.json: el vídeo sale sin recursos en pantalla.")
        return 0
    cortes = json.loads((trabajo / "cortes.json").read_text(encoding="utf-8"))
    palabras = palabras_en_corte(json.loads((trabajo / "transcripcion.json").read_text(encoding="utf-8")), cortes)
    duracion = cortes["segmentos"][-1]["salida_fin"]
    modo_color = cortes.get("color", {}).get("modo", "sdr")
    carpeta_tarjetas = trabajo / "recursos"
    carpeta_tarjetas.mkdir(exist_ok=True)

    plan, errores = [], 0
    for k, r in enumerate(json.loads(origen.read_text(encoding="utf-8")).get("recursos", [])):
        archivo = video / "03_recursos" / r["archivo"]
        if not archivo.exists():
            print(f"  ✗ No está {archivo}. Los recursos tienen que estar en 03_recursos/.")
            errores += 1
            continue
        cuando = momento(palabras, r["en"])
        if cuando is None:
            print(f"  ✗ No encuentro «{r['en']}» en la transcripción del vídeo cortado.")
            errores += 1
            continue
        modo = r.get("modo", "tarjeta")
        fin = min(cuando + float(r.get("dura", DURA)), duracion)
        tipo = "imagen" if archivo.suffix.lower() in IMAGENES else "video" if archivo.suffix.lower() in VIDEOS else None
        if tipo is None:
            print(f"  ✗ {archivo.name}: formato no admitido (usa jpg, png, mp4 o mov).")
            errores += 1
            continue
        entrada = {"archivo": str(archivo), "modo": modo, "tipo": tipo, "inicio": round(cuando, 3), "fin": round(fin, 3)}
        if tipo == "video":
            entrada["color"] = color.datos_color(archivo)
        if tipo == "video":
            hdr_recurso = color.es_hdr(entrada["color"])
            if hdr_recurso != (modo_color == "hdr") or (hdr_recurso and entrada["color"]["transferencia"] != cortes["color"]["transferencia"]):
                print(f"  ✗ {archivo.name}: su color ({entrada['color']['transferencia']}) no es el del vídeo "
                      f"({cortes['color']['transferencia']}). De momento solo se mezclan clips grabados igual "
                      "(HDR con HDR o normal con normal); usa una foto o una captura de ese momento.")
                errores += 1
                continue
        if modo == "tarjeta":
            # Regla: un recurso nunca tapa la cara del talento. La tarjeta va en el hueco libre
            # más alto (debajo o encima de la cara); si no cabe legible, pasa a pantalla completa.
            hueco = hueco_para_tarjeta(zona_de_la_cara(cortes, video / "02_brutos", cuando, fin))
            if hueco is None:
                modo = entrada["modo"] = "completo"
                print(f"  · {archivo.name}: no cabe una tarjeta sin tapar la cara; va a pantalla completa.")
            else:
                caja = (TARJETA_ANCHO, min(TARJETA_ALTO, hueco[1] - hueco[0]))
        if tipo == "imagen":
            destino = carpeta_tarjetas / f"{modo}-{k:02d}.png"
            tw, th = preparar_imagen(archivo, destino, modo_color, completo=(modo == "completo"),
                                     caja=caja if modo == "tarjeta" else (TARJETA_ANCHO, TARJETA_ALTO))
            entrada.update({"preparado": str(destino), "ancho": tw, "alto": th})
        elif modo == "tarjeta":
            r_v = ejecutar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", str(archivo)])
            vw, vh = (int(x) for x in r_v.stdout.strip().split(",")[:2])
            esc = min(caja[0] / vw, caja[1] / vh)
            entrada.update({"ancho": round(vw * esc / 2) * 2, "alto": round(vh * esc / 2) * 2})
        if modo == "tarjeta":
            # Centrada en vertical dentro del hueco.
            entrada["y"] = hueco[0] + (hueco[1] - hueco[0] - entrada["alto"]) // 2
        plan.append(entrada)
        sitio = f" (y={entrada['y']}–{entrada['y'] + entrada['alto']} px, cara libre)" if modo == "tarjeta" else ""
        print(f"  · {modo} {cuando:.1f}–{fin:.1f} s: {archivo.name}{sitio}")

    # Dos recursos a la vez se tapan: se avisa (el segundo se queda, por orden de tiempo).
    plan.sort(key=lambda e: e["inicio"])
    for a, b in zip(plan, plan[1:]):
        if b["inicio"] < a["fin"] - 0.05:
            print(f"  ! {Path(a['archivo']).name} y {Path(b['archivo']).name} se solapan: acorta «dura» o cambia «en».")
    plan_f.write_text(json.dumps({"color": modo_color, "recursos": plan, "tarjeta_y": TARJETA_Y,
                                  "ancho": ANCHO, "alto": ALTO}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(plan)} recursos en pantalla · {plan_f}")
    return 2 if errores else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as e:
        print(f"No se pudieron preparar los recursos: {e}")
        sys.exit(1)
