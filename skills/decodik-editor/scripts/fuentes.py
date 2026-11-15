"""Letras de los subtítulos y textos: se descargan de su repositorio oficial la primera vez.

Todas tienen licencia SIL Open Font License 1.1 (ver CREDITOS.md). Se guardan en
~/.cache/decodik/fuentes/ junto a su licencia. El repo no incluye ninguna.
Solo biblioteca estándar.
"""

from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

CARPETA = Path.home() / ".cache" / "decodik" / "fuentes"

INTER_ZIP = "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip"
FIGTREE = "https://raw.githubusercontent.com/erikdkennedy/figtree/master/fonts/ttf/{}"
GOOGLE = "https://raw.githubusercontent.com/google/fonts/main/ofl/{}"

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
    # Marca DECODIK: Anton para ganchos y textos grandes, Bebas Neue para etiquetas.
    "Anton-Regular.ttf": ("anton", GOOGLE.format("anton/Anton-Regular.ttf")),
    "BebasNeue-Regular.ttf": ("bebasneue", GOOGLE.format("bebasneue/BebasNeue-Regular.ttf")),
}
LICENCIAS = {
    "inter": ("Inter-OFL.txt", None),  # viene dentro del zip (LICENSE.txt)
    "figtree": ("Figtree-OFL.txt", "https://raw.githubusercontent.com/erikdkennedy/figtree/master/OFL.txt"),
    "anton": ("Anton-OFL.txt", GOOGLE.format("anton/OFL.txt")),
    "bebasneue": ("BebasNeue-OFL.txt", GOOGLE.format("bebasneue/OFL.txt")),
}


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
