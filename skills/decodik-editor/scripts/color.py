"""Color: el vídeo sale con el mismo color con el que se grabó. Nunca se convierte el color de
ningún clip ni recurso (decisión de Santiago): todo entra con sus valores originales.

- Si todos los clips son HDR (los iPhone graban en HLG), sale HDR: HEVC 10 bits con las mismas
  etiquetas de color. No se convierte nada.
- Si todos son SDR (la mayoría de Android, cámaras), sale SDR: H.264 8 bits, BT.709.
- Si se mezclan, el vídeo sale con la etiqueta de la mayoría y los otros entran sin convertir (se avisa).

Lo usan cortar.py, subtitulos.py y render.py. Solo biblioteca estándar y ffprobe.
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

HDR_TRANSFERENCIAS = ("arib-std-b67", "smpte2084")  # HLG y PQ



def datos_color(ruta: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=color_transfer,color_primaries,color_space", "-of", "default=nw=1", str(ruta)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    d = dict(l.split("=", 1) for l in r.stdout.strip().splitlines() if "=" in l)
    return {"transferencia": d.get("color_transfer", "unknown"),
            "primarios": d.get("color_primaries", "unknown"),
            "matriz": d.get("color_space", "unknown")}


def es_hdr(datos: dict) -> bool:
    return datos["transferencia"] in HDR_TRANSFERENCIAS


def decidir(clips: list[Path]) -> dict:
    """Decide con qué etiqueta de color sale el vídeo. NUNCA se convierte el color de ningún clip
    (decisión de Santiago): todos entran con sus valores originales.
    - Todos HDR del mismo tipo → sale HDR (HEVC 10 bits) con esas etiquetas.
    - Todos SDR → sale SDR (H.264, BT.709).
    - Mezclados → sale con la etiqueta de la mayoría (en duración no se mira: en número de clips);
      los otros entran sin convertir y se avisa de que pueden verse algo distintos."""
    por_clip = {str(c): datos_color(c) for c in clips}
    hdr = [c for c, d in por_clip.items() if es_hdr(d)]
    tipos = {por_clip[c]["transferencia"] for c in hdr}
    if hdr and len(hdr) * 2 >= len(por_clip):
        transferencia = max(tipos, key=lambda t: sum(1 for c in hdr if por_clip[c]["transferencia"] == t))
        aviso = ("" if len(hdr) == len(por_clip) and len(tipos) == 1 else
                 "Hay clips con color distinto (HDR y normal, o dos tipos de HDR). No se convierten: el vídeo "
                 "sale en HDR y los otros clips pueden verse algo distintos.")
        return {"modo": "hdr", "transferencia": transferencia, "por_clip": por_clip, "aviso": aviso}
    aviso = ("Hay clips HDR y normales mezclados. No se convierten: el vídeo sale en color normal y los clips "
             "HDR pueden verse algo distintos.") if hdr else ""
    return {"modo": "sdr", "transferencia": "bt709", "por_clip": por_clip, "aviso": aviso}


def filtro_clip(clip: Path, decision: dict, fps: int) -> str:
    """Filtro de vídeo de un clip: solo tamaño vertical 1080×1920 y etiquetas de salida. El color
    del clip no se toca (sus valores entran tal cual)."""
    base = "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1," + f"fps={fps}"
    if decision["modo"] == "hdr":
        return base + (f",format=yuv420p10le,setparams=color_primaries=bt2020:color_trc={decision['transferencia']}"
                       ":colorspace=bt2020nc:range=tv")
    return base + ",format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"


def etiquetas_salida(decision: dict) -> list[str]:
    if decision["modo"] == "hdr":
        return ["-pix_fmt", "yuv420p10le", "-color_primaries", "bt2020",
                "-color_trc", decision["transferencia"], "-colorspace", "bt2020nc", "-color_range", "tv"]
    return ["-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-colorspace", "bt709", "-color_range", "tv"]


def codec_cpu(decision: dict, rapido: bool = False) -> list[str]:
    if decision["modo"] == "hdr":
        t = decision["transferencia"]
        return ["-c:v", "libx265", "-preset", "fast" if rapido else "medium", "-crf", "22" if rapido else "18",
                "-x265-params", f"colorprim=bt2020:transfer={t}:colormatrix=bt2020nc:range=limited:log-level=error",
                "-tag:v", "hvc1"]
    return ["-c:v", "libx264", "-preset", "veryfast" if rapido else "medium", "-crf", "23" if rapido else "18"]


def _srgb_a_lineal(v: float) -> float:
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def _hlg(e: float) -> float:
    """Curva HLG (ITU-R BT.2100): luz de escena lineal 0-1 → señal 0-1."""
    a, b, c = 0.17883277, 0.28466892, 0.55991073
    return math.sqrt(3 * e) if e <= 1 / 12 else a * math.log(12 * e - b) + c


# Paso de colores BT.709 (sRGB) a BT.2020, en luz lineal.
_709_A_2020 = ((0.6274, 0.3293, 0.0433), (0.0691, 0.9195, 0.0114), (0.0164, 0.0880, 0.8956))
# Luz lineal de escena que la curva HLG convierte en el blanco de referencia (75 % de señal).
_BLANCO_LINEAL = 0.2647


def color_texto(hexrgb: str, decision_modo: str) -> str:
    """Color de texto para ASS (&HAABBGGRR).

    En SDR se usa tal cual. En HDR (HLG) el vídeo va en gama BT.2020 con curva HLG, así que el
    color sRGB se convierte para que se vea igual: a luz lineal, a primarios BT.2020, escalado al
    blanco de referencia (el blanco queda al 75 % de la señal, no al 100 %) y con la curva HLG."""
    r, g, b = (int(hexrgb[i:i + 2], 16) / 255 for i in (0, 2, 4))
    if decision_modo == "hdr":
        lin = [_srgb_a_lineal(x) for x in (r, g, b)]
        r, g, b = (_hlg(min(1.0, _BLANCO_LINEAL * sum(m * x for m, x in zip(fila, lin)))) for fila in _709_A_2020)
    r, g, b = (round(max(0.0, min(1.0, x)) * 255) for x in (r, g, b))
    return f"&H00{b:02X}{g:02X}{r:02X}"


def filtro_vista_previa(modo: str, transferencia: str) -> str:
    """Solo para mirar fotogramas (hoja de revisión): un PNG no guarda HDR, así que para verlo
    en pantalla se pasa a SDR. El vídeo entregado no se toca."""
    if modo != "hdr":
        return "null"
    return (f"zscale=tin={transferencia}:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,"
            "zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=rgb24")

