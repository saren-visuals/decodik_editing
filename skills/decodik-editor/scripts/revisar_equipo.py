# /// script
# requires-python = ">=3.10"
# ///
"""Revisa si el equipo tiene lo necesario para editar vídeo con decodik-editor.

Uso:
    uv run revisar_equipo.py                 revisa y dice qué falta
    uv run revisar_equipo.py --whisper       además prepara la transcripción (descarga librerías la primera vez)
    uv run revisar_equipo.py --prueba DIR    además renderiza un MP4 de prueba de 5 s en DIR

Solo usa la biblioteca estándar de Python. Sale con 0 si todo está bien y con 1 si falta algo.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SISTEMA = {"Windows": "windows", "Darwin": "mac"}.get(platform.system(), "linux")

INSTALAR = {
    "ffmpeg": {
        "windows": "winget install Gyan.FFmpeg",
        "mac": "brew install ffmpeg",
        "linux": "sudo apt install ffmpeg",
    },
    "uv": {
        "windows": 'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"',
        "mac": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "linux": "curl -LsSf https://astral.sh/uv/install.sh | sh",
    },
}

# Versión de Python y librerías con las que se transcribe (ver transcribir.py).
WHISPER_PYTHON = "3.12"
WHISPER_PAQUETE = "faster-whisper>=1.1,<2"


def ok(texto: str) -> None:
    print(f"  ✓ {texto}")


def falta(texto: str, arreglo: str | None = None) -> None:
    print(f"  ✗ {texto}")
    if arreglo:
        print(f"      Para arreglarlo: {arreglo}")


def ejecutar(cmd: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def revisar_ffmpeg() -> bool:
    bien = True
    for prog in ("ffmpeg", "ffprobe"):
        if shutil.which(prog) is None:
            falta(f"{prog} no está instalado.", INSTALAR["ffmpeg"][SISTEMA])
            return False
    version = ejecutar(["ffmpeg", "-version"]).stdout.splitlines()[0].split(" Copyright")[0]
    ok(version)

    codificadores = ejecutar(["ffmpeg", "-hide_banner", "-encoders"]).stdout
    if " libx264 " in codificadores:
        ok("Codificador de vídeo H.264 (libx264)")
    else:
        falta("Este ffmpeg no trae libx264 (H.264).", "instala una versión completa: " + INSTALAR["ffmpeg"][SISTEMA])
        bien = False

    filtros = ejecutar(["ffmpeg", "-hide_banner", "-filters"]).stdout
    if " subtitles " in filtros:
        ok("Filtro de subtítulos (libass)")
    else:
        falta("Este ffmpeg no trae el filtro de subtítulos (libass).", "instala una versión completa: " + INSTALAR["ffmpeg"][SISTEMA])
        bien = False
    return bien


def revisar_uv() -> bool:
    if shutil.which("uv") is None:
        falta("uv no está instalado (trae Python y las librerías de transcripción).", INSTALAR["uv"][SISTEMA])
        return False
    ok(ejecutar(["uv", "--version"]).stdout.strip())
    return True


def revisar_gpu() -> None:
    if shutil.which("nvidia-smi"):
        r = ejecutar(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
        if r.returncode == 0 and r.stdout.strip():
            ok(f"Tarjeta gráfica NVIDIA: {r.stdout.strip().splitlines()[0]} (de momento se transcribe con el procesador)")
            return
    print("  · Sin tarjeta gráfica NVIDIA: se transcribe con el procesador (más lento en vídeos largos, funciona igual).")


def preparar_whisper() -> bool:
    print("  … Preparando la transcripción (la primera vez descarga Python y librerías, unos minutos).")
    r = ejecutar(
        ["uv", "run", "--no-project", "--python", WHISPER_PYTHON, "--with", WHISPER_PAQUETE,
         "python", "-c", "import faster_whisper; print(faster_whisper.__version__)"],
        timeout=1800,
    )
    if r.returncode != 0:
        falta("No se pudo preparar la transcripción.", "revisa la conexión a internet y vuelve a intentarlo.")
        print("      Detalle: " + (r.stderr.strip().splitlines() or ["sin detalle"])[-1])
        return False
    ok(f"Transcripción lista (faster-whisper {r.stdout.strip()}). El modelo de voz se descarga en el primer vídeo.")
    return True


def render_prueba(carpeta: Path) -> bool:
    carpeta.mkdir(parents=True, exist_ok=True)
    salida = (carpeta / "prueba-motor.mp4").resolve()
    r = ejecutar([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=30:duration=5",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=5",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
        str(salida),
    ], timeout=300)
    if r.returncode != 0 or not salida.exists():
        falta("No se pudo renderizar el vídeo de prueba.")
        print("      Detalle: " + r.stderr.strip()[-300:])
        return False

    info = json.loads(ejecutar([
        "ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration",
        "-of", "json", str(salida),
    ]).stdout)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    duracion = float(info["format"]["duration"])
    correcto = video["width"] == 1080 and video["height"] == 1920 and abs(duracion - 5) < 0.1 and audio is not None
    texto = (f"{salida} · {video['width']}×{video['height']} · {video['codec_name']} · "
             f"{video['r_frame_rate']} fps · audio {audio['codec_name'] if audio else 'no'} · {duracion:.2f} s")
    (ok if correcto else falta)(f"Vídeo de prueba: {texto}")
    return correcto


def main() -> int:
    p = argparse.ArgumentParser(description="Revisa el equipo para editar vídeo con decodik-editor.")
    p.add_argument("--whisper", action="store_true", help="prepara también la transcripción")
    p.add_argument("--prueba", metavar="CARPETA", type=Path, help="renderiza un MP4 de prueba de 5 s en CARPETA")
    args = p.parse_args()

    print(f"Revisando el equipo ({SISTEMA})…\n")
    print("Vídeo:")
    bien = revisar_ffmpeg()
    print("\nTranscripción:")
    bien = revisar_uv() and bien
    revisar_gpu()
    if args.whisper and shutil.which("uv"):
        bien = preparar_whisper() and bien
    if args.prueba and shutil.which("ffmpeg"):
        print("\nPrueba:")
        bien = render_prueba(args.prueba) and bien

    print("\n" + ("Todo listo para editar." if bien else "Falta algo: instala lo marcado con ✗ y vuelve a ejecutar esta revisión."))
    return 0 if bien else 1


if __name__ == "__main__":
    sys.exit(main())
