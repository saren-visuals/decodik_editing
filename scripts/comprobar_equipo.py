"""Comprueba si el ordenador tiene lo necesario para cada nivel y dice cómo instalar lo que falte.

Uso:
  python comprobar_equipo.py --nivel basico|intermedio|avanzado
  python comprobar_equipo.py --nivel avanzado --descargar-modelo
"""
import argparse
import importlib.util
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from comun import SKILL

SO = platform.system()  # Windows, Darwin, Linux
MODELO_URL = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_resnet50_fp32.torchscript"
MODELO = SKILL / "modelos" / "rvm_resnet50_fp32.torchscript"

INSTALAR = {
    "ffmpeg": {"Windows": "winget install --id Gyan.FFmpeg -e", "Darwin": "brew install ffmpeg",
               "Linux": "sudo apt install ffmpeg"},
    "node": {"Windows": "winget install --id OpenJS.NodeJS.LTS -e", "Darwin": "brew install node",
             "Linux": "sudo apt install nodejs npm"},
    "pip_basico": f'"{sys.executable}" -m pip install faster-whisper numpy',
    "hyperframes": "npx --yes hyperframes --version",
    "torch_nvidia": f'"{sys.executable}" -m pip install torch --index-url https://download.pytorch.org/whl/cu128',
    "torch": f'"{sys.executable}" -m pip install torch',
}


def ok(nombre, estado, detalle=""):
    marca = "✅" if estado else "❌"
    print(f"  {marca} {nombre}{(' · ' + detalle) if detalle else ''}")
    return estado


def version(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, shell=(SO == "Windows" and cmd[0] == "npx"))
        return (r.stdout or r.stderr).strip().splitlines()[0] if r.returncode == 0 else None
    except Exception:
        return None


def hay_modulo(nombre):
    return importlib.util.find_spec(nombre) is not None


def gpu_nvidia():
    if not shutil.which("nvidia-smi"):
        return None
    v = version(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nivel", choices=["basico", "intermedio", "avanzado"], default="basico")
    ap.add_argument("--descargar-modelo", action="store_true")
    a = ap.parse_args()

    if a.descargar_modelo:
        MODELO.parent.mkdir(parents=True, exist_ok=True)
        print("Modelo de recorte RobustVideoMatting · licencia GPL-3.0 · repositorio oficial:\n"
              "  https://github.com/PeterL1n/RobustVideoMatting\n"
              "No viene dentro de la skill: se descarga a tu equipo solo para usarlo tú.")
        print(f"Descargando (~100 MB) en {MODELO} …")
        urllib.request.urlretrieve(MODELO_URL, MODELO)
        print("✅ Modelo descargado.")
        return

    faltan = []
    print(f"\nEquipo para el nivel: {a.nivel.upper()}  (sistema: {SO}, Python {platform.python_version()})\n")

    print("Básico")
    if not ok("Python 3.10 o superior", sys.version_info >= (3, 10), platform.python_version()):
        faltan.append(("Python 3.10+", "Descárgalo de https://www.python.org/downloads/"))
    v = version(["ffmpeg", "-version"])
    if not ok("ffmpeg (cortar, montar y exportar)", bool(v), (v or "")[:40]):
        faltan.append(("ffmpeg", INSTALAR["ffmpeg"].get(SO)))
    fw = hay_modulo("faster_whisper")
    np_ = hay_modulo("numpy")
    if not ok("faster-whisper + numpy (escuchar y transcribir)", fw and np_):
        faltan.append(("faster-whisper y numpy", INSTALAR["pip_basico"]))

    gpu = gpu_nvidia()
    ok("Tarjeta NVIDIA (opcional, acelera mucho)", bool(gpu), gpu or "no detectada: irá más lento, pero funciona")

    if a.nivel in ("intermedio", "avanzado"):
        print("\nIntermedio")
        v = version(["node", "--version"])
        mayor = int(v.lstrip("v").split(".")[0]) if v else 0
        if not ok("Node.js 22+ (gráficos animados)", mayor >= 22, v or ""):
            faltan.append(("Node.js 22+", INSTALAR["node"].get(SO)))
        if mayor:
            h = version(["npx", "--yes", "hyperframes", "--version"])
            if not ok("HyperFrames (dibuja gráficos y subtítulos)", bool(h), h or ""):
                faltan.append(("HyperFrames", INSTALAR["hyperframes"]))
        navegador = any(shutil.which(n) for n in ("chrome", "google-chrome", "msedge", "chromium")) or SO in ("Windows", "Darwin")
        ok("Chrome o Edge (lo usa HyperFrames)", navegador)

    if a.nivel == "avanzado":
        print("\nAvanzado")
        t = hay_modulo("torch")
        if not ok("PyTorch (recorte del sujeto)", t):
            faltan.append(("PyTorch", INSTALAR["torch_nvidia"] if gpu else INSTALAR["torch"]))
        if not ok("Modelo de recorte RVM (~100 MB, GPL-3.0)", MODELO.exists()):
            faltan.append(("Modelo de recorte", f'"{sys.executable}" "{Path(__file__)}" --descargar-modelo'))

    perfil = "rápido" if gpu else ("medio" if SO == "Darwin" else "lento")
    print(f"\nPerfil del equipo: {perfil}. Calidad recomendada: {'4K o 1080p' if gpu else '1080p'}.")

    if faltan:
        print("\nFalta instalar (pide permiso al usuario antes de cada uno):")
        for nombre, cmd in faltan:
            print(f"  · {nombre}: {cmd}")
        print("\nTras instalar ffmpeg o Node.js puede hacer falta abrir una sesión nueva de Claude Code.")
        sys.exit(2)
    print("\n✅ Todo listo para este nivel.")


if __name__ == "__main__":
    main()
