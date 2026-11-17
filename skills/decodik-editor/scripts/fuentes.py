"""Letras de los subtítulos y textos. Las 3 de DECODIK: Figtree, Inter y Helvetica Now Display.

Figtree e Inter tienen licencia SIL Open Font License 1.1 (ver CREDITOS.md): se descargan de su
repositorio oficial la primera vez y se guardan en ~/.cache/decodik/fuentes/ junto a su licencia.
Helvetica Now Display es de pago (Monotype): nunca se descarga ni entra al repo. Se usa solo si el
equipo la tiene (instalada o en ~/.cache/decodik/fuentes/); si no, Inter Display Black.
El repo no incluye ninguna letra. Solo biblioteca estándar.
"""

from __future__ import annotations

import io
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

CARPETA = Path.home() / ".cache" / "decodik" / "fuentes"

INTER_ZIP = "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip"
FIGTREE = "https://raw.githubusercontent.com/erikdkennedy/figtree/master/fonts/ttf/{}"

# archivo → de dónde sale
ORIGEN = {
    **{f: ("inter", f"extras/ttf/{f}") for f in (
        "Inter-Medium.ttf", "Inter-SemiBold.ttf", "Inter-Bold.ttf",
        "InterDisplay-Medium.ttf", "InterDisplay-SemiBold.ttf", "InterDisplay-Bold.ttf",
        "InterDisplay-BoldItalic.ttf", "InterDisplay-ExtraBold.ttf", "InterDisplay-Black.ttf",
        "InterDisplay-BlackItalic.ttf")},
    **{f: ("figtree", FIGTREE.format(f)) for f in (
        "Figtree-Medium.ttf", "Figtree-SemiBold.ttf", "Figtree-Bold.ttf", "Figtree-ExtraBold.ttf",
        "Figtree-Black.ttf", "Figtree-BlackItalic.ttf")},
}
LICENCIAS = {
    "inter": ("Inter-OFL.txt", None),  # viene dentro del zip (LICENSE.txt)
    "figtree": ("Figtree-OFL.txt", "https://raw.githubusercontent.com/erikdkennedy/figtree/master/OFL.txt"),
}

# Textos grandes (gancho, cifras, CTA, estilo condensada): Helvetica Now Display ExtraBlack si el
# equipo la tiene; si no, Inter Display Black, la libre más parecida.
HELVETICA = ("HelveticaNowDisplay ExtraBlack", ("HelveticaNowDisplay-ExtBlk.ttf", "HelveticaNowDisplay-ExtBlk.otf"))
INTER_GRANDE = ("Inter Display Black", "InterDisplay-Black.ttf")


def _carpetas_del_sistema() -> list[Path]:
    casa = Path.home()
    return [p for p in (
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
        Path(os.environ.get("LOCALAPPDATA", casa / "AppData/Local")) / "Microsoft/Windows/Fonts",
        casa / "Library/Fonts", Path("/Library/Fonts"), Path("/System/Library/Fonts"),
        casa / ".fonts", casa / ".local/share/fonts", Path("/usr/share/fonts"), Path("/usr/local/share/fonts"),
    ) if p.is_dir()]


def grande() -> tuple[str, str]:
    """(nombre, archivo) de la letra de los textos grandes.

    Si el equipo tiene Helvetica Now Display ExtraBlack instalada, se copia a la carpeta de letras
    (copia local, para que ffmpeg la encuentre) y se usa. Si no, Inter Display Black."""
    nombre, archivos = HELVETICA
    for a in archivos:
        if (CARPETA / a).exists():
            return nombre, a
    for carpeta in _carpetas_del_sistema():
        for a in archivos:
            for p in (carpeta / a, *carpeta.glob(f"*/{a}")):
                if p.is_file():
                    try:
                        CARPETA.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(p, CARPETA / a)
                        return nombre, a
                    except OSError:
                        pass
    return INTER_GRANDE


def asegurar(archivos: list[str]) -> Path:
    """Descarga las letras que falten de `archivos` y devuelve la carpeta. Sale con 3 si no hay red."""
    CARPETA.mkdir(parents=True, exist_ok=True)
    faltan = [a for a in archivos if not (CARPETA / a).exists()]
    if not faltan:
        return CARPETA
    try:
        de_inter = [a for a in faltan if ORIGEN[a][0] == "inter"]
        if de_inter:
            print("  … Descargando la letra Inter (licencia OFL, ~34 MB, solo la primera vez).")
            with urllib.request.urlopen(INTER_ZIP, timeout=300) as r:
                z = zipfile.ZipFile(io.BytesIO(r.read()))
            # Se guardan todos los grosores de la lista, no solo los que faltan: así no se baja otra vez.
            for a, (src, ruta) in ORIGEN.items():
                if src == "inter" and not (CARPETA / a).exists():
                    (CARPETA / a).write_bytes(z.read(ruta))
            (CARPETA / LICENCIAS["inter"][0]).write_bytes(z.read("LICENSE.txt"))
        for a in faltan:
            src, url = ORIGEN[a]
            if src != "inter" and not (CARPETA / a).exists():
                urllib.request.urlretrieve(url, CARPETA / a)
                nombre, url_lic = LICENCIAS[src]
                if not (CARPETA / nombre).exists():
                    urllib.request.urlretrieve(url_lic, CARPETA / nombre)
    except (OSError, KeyError, zipfile.BadZipFile) as e:
        print(f"No se pudieron descargar las letras ({e}). Revisa la conexión y vuelve a intentarlo.")
        sys.exit(3)
    return CARPETA
