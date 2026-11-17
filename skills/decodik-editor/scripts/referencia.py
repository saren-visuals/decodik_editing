# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Mira un vídeo (o capturas) de referencia para sacar el estilo de edición que le gusta al talento.

Uso:
    uv run referencia.py <carpeta del vídeo>

Lee lo que haya en 03_recursos/referencia/ (vídeos .mp4/.mov/.m4v/.webm o capturas .jpg/.png/.webp)
y escribe en 06_entrega/trabajo/referencia/:
    hoja-N.jpg        fotogramas en vertical, grandes para que se lean los subtítulos (6 por hoja)
    referencia.json   por cada vídeo: duración, cortes detectados, segundos por plano y ritmo

Con eso Claude rellena 06_entrega/trabajo/estilo.json (ver references/estilo-talento.md): el estilo de
subtítulos más parecido de los 8, los colores, el ritmo de cortes, textos, recursos y encuadre.
Solo mira; no copia nada del vídeo de referencia en el vídeo del talento.
Códigos: 0 bien · 2 no hay nada en 03_recursos/referencia/.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VIDEOS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
IMAGENES = {".jpg", ".jpeg", ".png", ".webp"}
POR_HOJA = 6                 # 3 × 2
ANCHO, ALTO = 540, 960       # cada fotograma, en vertical
FOTOS_POR_VIDEO = 6
UMBRAL_ESCENA = 0.2          # sensibilidad: los cortes «jump cut» del mismo plano puntúan bajo
SEPARACION_MIN = 0.3         # dos cambios más juntos que esto cuentan como un solo corte


def ffprobe_duracion(f: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(f)],
                       capture_output=True, text=True)
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return 0.0


def cortes(f: Path) -> list[float]:
    """Instantes (s) en que cambia de plano, con el detector de escena de ffmpeg."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(f), "-an", "-vf",
                        f"scale=270:-2,select='gt(scene,{UMBRAL_ESCENA})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True)
    instantes: list[float] = []
    for t in (float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)):
        if not instantes or t - instantes[-1] >= SEPARACION_MIN:
            instantes.append(t)
    return instantes


def ritmo(seg_por_plano: float) -> tuple[str, float]:
    """Ritmo en palabras y la pausa máxima que se le pasa a cortar.py."""
    if seg_por_plano < 1.5:
        return "rápido", 0.2
    if seg_por_plano <= 3.0:
        return "medio", 0.3
    return "pausado", 0.45


def fotograma(origen: Path, t: float | None, destino: Path) -> bool:
    """Un fotograma (o una imagen) encajado en 540×960 con bandas de color papel."""
    filtro = (f"scale={ANCHO}:{ALTO}:force_original_aspect_ratio=decrease,"
              f"pad={ANCHO}:{ALTO}:(ow-iw)/2:(oh-ih)/2:color=0xF7F1E8")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    if t is not None:
        cmd += ["-ss", f"{t:.2f}"]
    cmd += ["-i", str(origen), "-frames:v", "1", "-vf", filtro, str(destino)]
    return subprocess.run(cmd).returncode == 0 and destino.exists()


def main() -> int:
    p = argparse.ArgumentParser(description="Fotogramas y ritmo de un vídeo de referencia de estilo.")
    p.add_argument("carpeta", type=Path, help="carpeta del vídeo")
    args = p.parse_args()

    video = args.carpeta.resolve()
    ref = video / "03_recursos" / "referencia"
    archivos = sorted(f for f in ref.glob("*") if f.suffix.lower() in VIDEOS | IMAGENES) if ref.is_dir() else []
    if not archivos:
        print(f"No hay vídeos ni capturas en {ref}.")
        print("Pídele al talento que deje ahí el vídeo que le gusta (o 2-3 capturas) y que diga «listo».")
        return 2

    salida = video / "06_entrega" / "trabajo" / "referencia"
    if salida.exists():
        shutil.rmtree(salida)
    (salida / "fotos").mkdir(parents=True)

    fotos: list[Path] = []
    datos: list[dict] = []
    for f in archivos:
        if f.suffix.lower() in IMAGENES:
            d = salida / "fotos" / f"{len(fotos):02d}.jpg"
            if fotograma(f, None, d):
                fotos.append(d)
            datos.append({"archivo": f.name, "tipo": "captura"})
            continue
        dur = ffprobe_duracion(f)
        if dur <= 0:
            print(f"  ! No se puede leer {f.name}: se salta.")
            continue
        cs = [c for c in cortes(f) if 0.2 < c < dur - 0.2]
        planos = len(cs) + 1
        spp = dur / planos
        palabra, pausa = ritmo(spp)
        datos.append({"archivo": f.name, "tipo": "vídeo", "duracion": round(dur, 1), "cortes": len(cs),
                      "segundos_por_plano": round(spp, 1), "ritmo": palabra, "pausa_max": pausa})
        # Fotogramas repartidos, evitando el primer y el último instante.
        for i in range(FOTOS_POR_VIDEO):
            t = dur * (i + 0.5) / FOTOS_POR_VIDEO
            d = salida / "fotos" / f"{len(fotos):02d}.jpg"
            if fotograma(f, t, d):
                fotos.append(d)
        print(f"  {f.name}: {dur:.0f} s, {len(cs)} cortes → un plano cada {spp:.1f} s (ritmo {palabra}).")

    hojas = 0
    for i in range(0, len(fotos), POR_HOJA):
        grupo = fotos[i:i + POR_HOJA]
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        for g in grupo:
            cmd += ["-i", str(g)]
        while len(grupo) < POR_HOJA:          # rellena huecos para el mosaico 3×2
            cmd += ["-f", "lavfi", "-i", f"color=c=0xF7F1E8:s={ANCHO}x{ALTO}:d=1"]
            grupo = grupo + [None]
        capas = "".join(f"[{k}:v]" for k in range(POR_HOJA))
        pos = "|".join(f"{(k % 3) * ANCHO}_{(k // 3) * ALTO}" for k in range(POR_HOJA))
        hojas += 1
        cmd += ["-filter_complex", f"{capas}xstack=inputs={POR_HOJA}:layout={pos}[h]", "-map", "[h]",
                "-frames:v", "1", str(salida / f"hoja-{hojas}.jpg")]
        subprocess.run(cmd)

    (salida / "referencia.json").write_text(json.dumps({"archivos": datos}, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
    print(f"Listo: {len(fotos)} fotogramas en {hojas} hoja(s) en 06_entrega/trabajo/referencia/.")
    print("Mira las hojas y rellena 06_entrega/trabajo/estilo.json (references/estilo-talento.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
