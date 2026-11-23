"""Pedidos de la landing «Pide tu edición» → proyecto → borrador de CapCut.

La fila del pedido la lee Claude del Google Sheet (conector de Google Sheets) y la guarda en un JSON; este script
hace la parte mecánica. Ver {SKILL}/flujos/pedido.md.

Uso:
  python pedido.py leer --codigo DK-0007 --tabla tabla.json --out pedido.json
        tabla.json = lo que devuelve el conector al leer «Pedidos!A1:Z» ({"values": [[...], ...]} o la lista).
        Guarda la fila (sin la columna «Clave») y la letra de cada columna.
  python pedido.py preparar --pedido pedido.json --raiz "<Decodik>" [--tema "mi historia"] [--material <carpeta o .zip>]
        Crea proyectos/<fecha>_<talento>-<tema>/ (o reutiliza el del mismo pedido), descarga los brutos y el archivo
        de fotos y vídeos de los enlaces de Drive del pedido (deben estar compartidos con «Cualquier persona con el
        enlace») o los copia de --material, y los reparte: vídeos sueltos → 02_tomas, subcarpeta «Archivo» o el
        enlace de archivo → 03_recursos (videos, fotos, capturas), documentos → 01_brief. Imprime un resumen JSON.
  python pedido.py estado --pedido pedido.json --fase en-edicion|borrador-capcut|revisar [--proyecto <ruta>] [--nota "..."]
        Imprime las celdas que hay que escribir en la fila (y las cabeceras que falten) como lista JSON
        [{"range": "Pedidos!C8", "values": [["En edición"]]}, ...]. No escribe nada en el Sheet.
  python pedido.py capcut --proyecto <ruta> --raiz "<Decodik>" [--plantilla <borrador>] [--estructura superposiciones]
        Con CapCut CERRADO: llama a exportar_capcut.py con el nombre «<código> <talento>-<tema>» y comprueba
        que el borrador queda creado y registrado.

Configuración (una vez, fuera de la skill): <Decodik>/_mi-estilo/pedidos.json
  {"sheet_id": "<id del Sheet>", "hoja": "Pedidos", "plantilla_capcut": "<carpeta de un borrador de CapCut>",
   "plantilla_audio": null}
"""
import argparse
import datetime
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from comun import SKILL, aviso, error, escribir_json, leer_json
from crear_proyecto import CARPETAS, LEEME_PROYECTO, slug

# Mismo orden que COLS en landing-edicion/app/Code.gs (las cabeceras que falten se ponen en su sitio).
COLS = [
    "Código", "Fecha", "Estado", "Nombre", "WhatsApp", "Tipo", "Formato", "Objetivo",
    "Plataformas", "Para cuándo", "Idea o guion", "Vídeo de referencia", "Brief de la marca",
    "Enlace de Drive", "Nota para el deportista", "Enlace versión", "Enlace entrega",
    "Respuestas del deportista", "Última actualización", "Clave",
    "Estilo", "Archivo de fotos y vídeos",
    "Edición (interno)", "Proyecto en el ordenador",
]
PRIVADAS = {"Clave"}   # no se copian al proyecto

# fase → (Estado que ve el deportista o None para no tocarlo, «Edición (interno)»)
FASES = {
    "en-edicion": ("En edición", "en edición"),
    "borrador-capcut": (None, "borrador en CapCut"),
    "revisar": (None, "revisar: no se pudo armar solo"),
}

FLUJOS = ["mi-historia", "explicativo-motion", "explicativo-texto", "solo-cortar", "manual"]

VIDEO = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".mts", ".webm", ".3gp"}
FOTO = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".dng", ".tif", ".tiff"}
AUDIO = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
DOC = {".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".pages", ".odt"}
CARPETAS_RECURSOS = {"archivo", "archivos", "recursos", "broll", "b-roll", "fotos", "videos-de-archivo",
                     "fotos-y-videos", "material-de-archivo"}
CAPCUT = Path.home() / "AppData/Local/CapCut/User Data/Projects/com.lveditor.draft"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


# ── utilidades ───────────────────────────────────────────────

def nfc(t):
    return unicodedata.normalize("NFC", t)


def plano(t):
    return slug(t or "")


def letra(n):
    """1 → A, 27 → AA"""
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def config(raiz):
    p = Path(raiz) / "_mi-estilo" / "pedidos.json"
    return leer_json(p) if p.exists() else {}


def formato_edicion(datos):
    """De «Premium + Mi historia · B-roll encima…» saca qué flujo de la skill toca."""
    est = plano(datos.get("Estilo", ""))
    if "mi-historia" in est:
        return "mi-historia"
    if "explicativo-con-motion" in est:
        return "explicativo-motion"
    if "explicativo-con-texto" in est:
        return "explicativo-texto"
    if datos.get("Tipo") == "Solo corte limpio":
        return "solo-cortar"
    return "manual"


# ── leer ─────────────────────────────────────────────────────

def cmd_leer(a):
    t = leer_json(a.tabla)
    filas = t.get("values", t) if isinstance(t, dict) else t
    if not filas:
        error("La tabla está vacía: lee «Pedidos!A1:Z» con el conector")
    cab = [str(c).strip() for c in filas[0]]
    ancho = max(len(f) for f in filas)
    # celdas con datos más allá de la última cabecera (hoja creada con una versión antigua): por posición en COLS
    cab += [COLS[j] if j < len(COLS) and COLS[j] not in cab else "" for j in range(len(cab), ancho)]
    if "Código" not in cab:
        error("La primera fila no tiene la cabecera «Código»: ¿es la hoja «Pedidos»?")
    ic = cab.index("Código")
    codigo = a.codigo.strip().upper()
    if re.fullmatch(r"\d+", codigo):
        codigo = f"DK-{int(codigo):04d}"
    for i, f in enumerate(filas[1:], start=2):
        if len(f) > ic and str(f[ic]).strip().upper() == codigo:
            datos = {c: (str(f[j]).strip() if j < len(f) else "") for j, c in enumerate(cab) if c and c not in PRIVADAS}
            columnas = {c: letra(j + 1) for j, c in enumerate(cab[:len(filas[0])]) if c}
            # columnas que aún no existen: su sitio según COLS si está libre; si no, al final
            usadas = {j for j, c in enumerate(cab[:len(filas[0])]) if c}
            faltan = {}
            for c in COLS:
                if c in columnas:
                    continue
                j = COLS.index(c)
                if j in usadas:
                    j = max(usadas) + 1
                usadas.add(j)
                columnas[c] = letra(j + 1)
                faltan[c] = letra(j + 1)
            out = {"codigo": codigo, "fila": i, "hoja": a.hoja, "datos": datos, "columnas": columnas,
                   "cabeceras_que_faltan": faltan, "flujo": a.flujo or formato_edicion(datos)}
            escribir_json(a.out, out)
            resumen = {k: datos.get(k, "") for k in ("Código", "Estado", "Nombre", "Tipo", "Formato", "Estilo",
                                                    "Enlace de Drive", "Archivo de fotos y vídeos")}
            print(json.dumps({"fila": i, "flujo": out["flujo"], **resumen,
                              "cabeceras_que_faltan": faltan}, ensure_ascii=False, indent=1))
            return
    error(f"No encuentro el pedido {codigo} en la hoja")


# ── estado ───────────────────────────────────────────────────

def cmd_estado(a):
    p = leer_json(a.pedido)
    hoja, fila, col = p.get("hoja", "Pedidos"), p["fila"], p["columnas"]
    visible, interno = FASES[a.fase]
    cambios = []
    for c, l in p.get("cabeceras_que_faltan", {}).items():
        if c in ("Edición (interno)", "Proyecto en el ordenador"):
            cambios.append({"range": f"{hoja}!{l}1", "values": [[c]]})
    if visible:
        cambios.append({"range": f"{hoja}!{col['Estado']}{fila}", "values": [[visible]]})
    texto = interno + (f" · {a.nota}" if a.nota else "")
    cambios.append({"range": f"{hoja}!{col['Edición (interno)']}{fila}", "values": [[texto]]})
    if a.proyecto:
        cambios.append({"range": f"{hoja}!{col['Proyecto en el ordenador']}{fila}", "values": [[str(Path(a.proyecto).resolve())]]})
    print(json.dumps(cambios, ensure_ascii=False, indent=1))


# ── Drive (enlaces públicos, sin cuenta) ─────────────────────

def drive_id(url):
    for pat in (r"/folders/([\w-]{10,})", r"/file/d/([\w-]{10,})", r"/d/([\w-]{10,})", r"[?&]id=([\w-]{10,})"):
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def abrir(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)


def listar_carpeta(fid, ruta=(), vistos=None):
    """[(id, nombre, (subcarpetas...), tipo)] recorriendo subcarpetas. tipo: file | doc | otro-google."""
    vistos = vistos if vistos is not None else set()
    if fid in vistos:
        return []
    vistos.add(fid)
    t = abrir(f"https://drive.google.com/embeddedfolderview?id={fid}").read().decode("utf-8", "replace")
    res = []
    for m in re.finditer(r'<div class="flip-entry" id="entry-([\w-]+)".*?<a href="([^"]+)".*?'
                         r'<div class="flip-entry-title">(.*?)</div>', t, re.S):
        eid, href, nombre = m.group(1), html.unescape(m.group(2)), nfc(html.unescape(m.group(3)).strip())
        if "/folders/" in href:
            res += listar_carpeta(eid, ruta + (nombre,), vistos)
        elif "docs.google.com/document" in href:
            res.append((eid, nombre, ruta, "doc"))
        elif "docs.google.com" in href:
            res.append((eid, nombre, ruta, "otro-google"))
        else:
            res.append((eid, nombre, ruta, "file"))
    return res


def es_carpeta(fid):
    try:
        t = abrir(f"https://drive.google.com/embeddedfolderview?id={fid}", 30).read().decode("utf-8", "replace")
        return "flip-entries" in t
    except urllib.error.HTTPError:
        return False


def descargar(fid, destino, tipo="file"):
    """Descarga un archivo público de Drive a destino (por trozos). Devuelve bytes o lanza RuntimeError."""
    if tipo == "doc":
        url = f"https://docs.google.com/document/d/{fid}/export?format=pdf"
    else:
        url = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
    r = abrir(url, 120)
    ctype = r.headers.get("Content-Type", "")
    if "text/html" in ctype:
        raise RuntimeError("Drive devuelve una página en vez del archivo: el enlace no está compartido con "
                           "«Cualquier persona con el enlace» o Drive pide confirmación")
    total = int(r.headers.get("Content-Length") or 0)
    if destino.exists() and total and destino.stat().st_size == total:
        r.close()
        return total
    parte = destino.with_name(destino.name + ".parte")
    n = 0
    with open(parte, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
            n += len(b)
    if total and n != total:
        raise RuntimeError(f"descarga incompleta ({n} de {total} bytes)")
    parte.replace(destino)
    return n


def nombre_archivo_drive(fid):
    r = abrir(f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t", 60)
    cd = r.headers.get("Content-Disposition", "")
    r.close()
    m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r'filename="([^"]+)"', cd)
    return nfc(urllib.parse.unquote(m.group(1))) if m else f"{fid}"


# ── reparto del material ─────────────────────────────────────

def destino_de(nombre, ruta, de_archivo):
    """Carpeta del proyecto donde va un archivo según su tipo y la subcarpeta de la que viene."""
    ext = Path(nombre).suffix.lower()
    partes = {plano(p) for p in ruta}
    recurso = de_archivo or bool(partes & CARPETAS_RECURSOS)
    n = plano(nombre)
    if ext in VIDEO:
        if "screenrecording" in n.replace("-", "") or "grabacion-de-pantalla" in n or "captura" in n:
            return "03_recursos/capturas"
        return "03_recursos/videos" if recurso else "02_tomas"
    if ext in FOTO:
        if "screenshot" in n or "captura" in n:
            return "03_recursos/capturas"
        return "03_recursos/fotos"
    if ext in AUDIO:
        return "05_musica"
    if ext in DOC:
        return "01_brief"
    return "01_brief/otros"


def sitio_libre(carpeta, nombre, ruta):
    d = carpeta / nombre
    if not d.exists():
        return d
    pref = plano(ruta[-1]) if ruta else "dup"
    return carpeta / f"{pref}_{nombre}"


def traer_enlace(url, proyecto, de_archivo, registro, avisos):
    fid = drive_id(url)
    if not fid or not re.search(r"(drive|docs)\.google\.com", url):
        avisos.append(f"No sé descargar este enlace (no es de Google Drive): {url}. Descárgalo a mano y "
                      f"pásalo con --material.")
        return
    if "/folders/" in url or ("/file/d/" not in url and "/document/" not in url and es_carpeta(fid)):
        try:
            entradas = listar_carpeta(fid)
        except urllib.error.HTTPError as e:
            avisos.append(f"No puedo abrir la carpeta de Drive ({e.code}): ¿está compartida con «Cualquier persona "
                          f"con el enlace»? Descárgala a mano y pásala con --material.")
            return
        if not entradas:
            avisos.append("La carpeta de Drive está vacía o no es pública: descárgala a mano y pásala con --material.")
    else:
        tipo = "doc" if "/document/" in url else "file"
        entradas = [(fid, nombre_archivo_drive(fid) if tipo == "file" else f"{fid}.pdf", (), tipo)]
    for eid, nombre, ruta, tipo in entradas:
        if tipo == "otro-google":
            avisos.append(f"«{'/'.join(ruta + (nombre,))}» es una hoja o presentación de Google: ábrela tú.")
            continue
        if tipo == "doc" and not nombre.lower().endswith(".pdf"):
            nombre += ".pdf"
        carpeta = proyecto / destino_de(nombre, ruta, de_archivo)
        carpeta.mkdir(parents=True, exist_ok=True)
        previo = next((r for r in registro if r.get("drive_id") == eid), None)
        dest = Path(previo["ruta"]) if previo else sitio_libre(carpeta, nombre, ruta)
        if previo and dest.exists():
            continue
        aviso(f"descargando {'/'.join(ruta + (nombre,))}")
        try:
            n = descargar(eid, dest, tipo)
        except (RuntimeError, urllib.error.URLError, TimeoutError) as e:
            avisos.append(f"No se pudo descargar «{nombre}»: {e}")
            continue
        registro.append({"origen": "drive", "drive_id": eid, "nombre": nombre, "subcarpeta": "/".join(ruta),
                         "ruta": str(dest), "bytes": n})


def traer_local(origen, proyecto, de_archivo, registro):
    origen = Path(origen).expanduser()
    if not origen.exists():
        error(f"No existe {origen}")
    tmp = None
    if origen.suffix.lower() == ".zip":
        tmp = Path(tempfile.mkdtemp(prefix="pedido_"))
        with zipfile.ZipFile(origen) as z:
            z.extractall(tmp)
        origen = tmp
    archivos = [origen] if origen.is_file() else sorted(p for p in origen.rglob("*") if p.is_file())
    hechos = {r.get("local") for r in registro}
    for f in archivos:
        if f.name.startswith(".") or f.name.lower() in ("desktop.ini", "thumbs.db"):
            continue
        rel = f.relative_to(origen) if origen.is_dir() else Path(f.name)
        clave = str(rel)
        if clave in hechos:
            continue
        ruta = tuple(nfc(p) for p in rel.parts[:-1])
        carpeta = proyecto / destino_de(nfc(f.name), ruta, de_archivo)
        carpeta.mkdir(parents=True, exist_ok=True)
        dest = sitio_libre(carpeta, nfc(f.name), ruta)
        shutil.copy2(f, dest)   # el original no se toca
        registro.append({"origen": "local", "local": clave, "nombre": f.name, "subcarpeta": "/".join(ruta),
                         "ruta": str(dest), "bytes": dest.stat().st_size})
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)


# ── preparar ─────────────────────────────────────────────────

BRIEF = """# Pedido {codigo}

- **Talento:** {Nombre}
- **Tipo:** {Tipo}
- **Formato de contenido:** {Formato}
- **Estilo:** {Estilo}
- **Objetivo:** {Objetivo}
- **Plataformas:** {Plataformas}
- **Para cuándo:** {Para cuándo}
- **Vídeo de referencia:** {Vídeo de referencia}

## Idea o guion
{Idea o guion}

## Brief de la marca
{Brief de la marca}

## Material
- Brutos: {Enlace de Drive}
- Archivo de fotos y vídeos: {Archivo de fotos y vídeos}
"""


def buscar_proyecto(raiz, codigo):
    for p in sorted((raiz / "proyectos").glob("*/01_brief/pedido.json")):
        try:
            if leer_json(p).get("codigo") == codigo:
                return p.parent.parent
        except (json.JSONDecodeError, OSError):
            pass
    return None


def cmd_preparar(a):
    raiz = Path(a.raiz).expanduser().resolve()
    p = leer_json(a.pedido)
    d, codigo = p["datos"], p["codigo"]
    flujo = a.flujo or p.get("flujo") or formato_edicion(d)
    proyecto = buscar_proyecto(raiz, codigo)
    if not proyecto:
        nombre = d.get("Nombre", "") or "talento"
        talento = "-".join(plano(nombre).split("-")[:2]) or "talento"
        tema = plano(a.tema) if a.tema else (flujo if flujo not in ("manual", "solo-cortar") else plano(d.get("Formato")) or "video")
        hoy = datetime.date.today().isoformat()
        proyecto = raiz / "proyectos" / f"{hoy}_{talento}-{tema}"[:80]
        if proyecto.exists():
            error(f"Ya existe {proyecto} y no es de este pedido: pasa otro --tema")
    for c in CARPETAS:
        (proyecto / c).mkdir(parents=True, exist_ok=True)
    (proyecto / "05_musica" / "efectos").mkdir(exist_ok=True)
    (proyecto / "LEEME.txt").write_text(LEEME_PROYECTO, encoding="utf-8")
    brief = proyecto / "01_brief"
    escribir_json(brief / "pedido.json", {"codigo": codigo, "flujo": flujo, "datos": d})
    (brief / "pedido.md").write_text(BRIEF.format(codigo=codigo, **{c: d.get(c, "") or "—" for c in COLS}),
                                     encoding="utf-8")

    reg_path = brief / "material.json"
    registro = leer_json(reg_path) if reg_path.exists() else []
    avisos = []
    if a.material:
        for m in a.material:
            traer_local(m, proyecto, False, registro)
    if a.archivo_local:
        traer_local(a.archivo_local, proyecto, True, registro)
    if not a.sin_descarga and not a.material:
        if d.get("Enlace de Drive"):
            traer_enlace(d["Enlace de Drive"], proyecto, False, registro, avisos)
        else:
            avisos.append("El pedido no tiene enlace de Drive.")
        arch = d.get("Archivo de fotos y vídeos", "")
        if arch.startswith("https://") and not a.archivo_local:
            traer_enlace(arch, proyecto, True, registro, avisos)
    escribir_json(reg_path, registro)

    tomas = sorted(str(x) for x in (proyecto / "02_tomas").iterdir() if x.suffix.lower() in VIDEO)
    rec = {k: len([x for x in (proyecto / "03_recursos" / k).glob("*") if x.is_file()])
           for k in ("videos", "fotos", "capturas") if (proyecto / "03_recursos" / k).exists()}
    if not tomas:
        avisos.append("No hay ninguna toma (vídeo suelto en la carpeta principal del Drive).")
    if flujo == "mi-historia" and not sum(rec.values()):
        avisos.append("«Mi historia» necesita fotos y vídeos de archivo y no ha llegado ninguno.")
    heic = [r["nombre"] for r in registro if Path(r["nombre"]).suffix.lower() in (".heic", ".heif")]
    if heic:
        avisos.append(f"{len(heic)} fotos HEIC: pásalas a JPG antes de analizar_recursos.py.")

    pj = proyecto / "proyecto.json"
    pr = leer_json(pj) if pj.exists() else {
        "nombre": f"{d.get('Nombre', '')} · {flujo}", "fecha": datetime.date.today().isoformat(),
        "caso": {"Vídeo para una marca": "marca", "Solo corte limpio": "cortar"}.get(d.get("Tipo"), "marca-personal"),
        "nivel": "basico", "estilo": None, "formato": "pantalla-completa", "revision": None, "graficos": None,
        "musica": None, "red": None, "resolucion": "1080", "palabra_detras": False, "pasadas_hechas": []}
    pr.update({"pedido": codigo, "flujo_pedido": flujo, "estilo_pedido": d.get("Estilo", ""),
               "toma": tomas[0] if len(tomas) == 1 else pr.get("toma"), "tomas": tomas})
    if flujo == "mi-historia":
        pr["formato"] = "mi-historia"
    escribir_json(pj, pr)
    print(json.dumps({"proyecto": str(proyecto), "codigo": codigo, "flujo": flujo, "tomas": tomas,
                      "recursos": rec, "archivos": len(registro), "avisos": avisos}, ensure_ascii=False, indent=1))


# ── capcut ───────────────────────────────────────────────────

def capcut_abierto():
    if sys.platform != "win32":
        return False
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/NH"], capture_output=True, text=True)
    return "capcut.exe" in r.stdout.lower()


def cmd_capcut(a):
    proyecto = Path(a.proyecto).resolve()
    cfg = config(a.raiz) if a.raiz else {}
    plantilla = a.plantilla or cfg.get("plantilla_capcut")
    if not plantilla:
        error("Falta la plantilla de CapCut: pasa --plantilla o pon «plantilla_capcut» en _mi-estilo/pedidos.json")
    real = Path(a.carpeta_capcut).resolve() == CAPCUT.resolve()
    if real and capcut_abierto():
        error("CapCut está abierto: ciérralo del todo (también de la bandeja) y vuelve a lanzar este paso")
    tr = proyecto / "06_trabajo"
    for f in ("storyboard-historia.json", "cortado.mp4", "subtitulos/subtitulos.json"):
        if not (tr / f).exists():
            error(f"Falta 06_trabajo/{f}: termina antes los pasos del flujo")
    ped = leer_json(proyecto / "01_brief" / "pedido.json")
    d = ped["datos"]
    tema = proyecto.name.split("_", 1)[-1]
    base = f"{ped['codigo']} {tema}"   # solo ASCII en el nombre de la carpeta del borrador
    carpeta = Path(a.carpeta_capcut)
    nombre, n = base, 2
    while (carpeta / nombre).exists():
        nombre, n = f"{base} ({n})", n + 1
    cmd = [sys.executable, str(Path(__file__).with_name("exportar_capcut.py")), "--trabajo", str(tr),
           "--nombre", nombre, "--plantilla", str(plantilla), "--carpeta-capcut", str(carpeta),
           "--estructura", a.estructura]
    if a.plantilla_audio or cfg.get("plantilla_audio"):
        cmd += ["--plantilla-audio", a.plantilla_audio or cfg["plantilla_audio"]]
    r = subprocess.run(cmd)
    if r.returncode:
        error("exportar_capcut.py ha fallado: mira el mensaje de arriba")
    destino = carpeta / nombre
    rm = leer_json(carpeta / "root_meta_info.json")
    registrado = any(Path(x.get("draft_fold_path", "")).name == nombre for x in rm.get("all_draft_store", []))
    ok = destino.joinpath("draft_content.json").exists() and registrado
    pj = proyecto / "proyecto.json"
    pr = leer_json(pj)
    pr["capcut"] = {"borrador": nombre, "carpeta": str(destino), "fecha": time.strftime("%Y-%m-%d %H:%M")}
    escribir_json(pj, pr)
    print(json.dumps({"borrador": nombre, "carpeta": str(destino), "registrado": registrado, "ok": ok},
                     ensure_ascii=False, indent=1))
    if not ok:
        error("El borrador no ha quedado bien registrado en CapCut")


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("leer")
    s.add_argument("--codigo", required=True)
    s.add_argument("--tabla", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--hoja", default="Pedidos")
    s.add_argument("--flujo", choices=FLUJOS, help="Forzar el flujo si el estilo del pedido no lo dice")
    s = sub.add_parser("preparar")
    s.add_argument("--pedido", required=True)
    s.add_argument("--raiz", required=True)
    s.add_argument("--tema")
    s.add_argument("--material", nargs="+", help="Carpeta o .zip con los brutos ya descargados (en vez de Drive)")
    s.add_argument("--archivo-local", help="Carpeta o .zip con las fotos y vídeos de archivo")
    s.add_argument("--sin-descarga", action="store_true")
    s.add_argument("--flujo", choices=FLUJOS)
    s = sub.add_parser("estado")
    s.add_argument("--pedido", required=True)
    s.add_argument("--fase", required=True, choices=list(FASES))
    s.add_argument("--proyecto")
    s.add_argument("--nota")
    s = sub.add_parser("capcut")
    s.add_argument("--proyecto", required=True)
    s.add_argument("--raiz")
    s.add_argument("--plantilla")
    s.add_argument("--plantilla-audio")
    s.add_argument("--estructura", choices=["superposiciones", "secuencia"], default="superposiciones")
    s.add_argument("--carpeta-capcut", default=str(CAPCUT))
    a = ap.parse_args()
    {"leer": cmd_leer, "preparar": cmd_preparar, "estado": cmd_estado, "capcut": cmd_capcut}[a.cmd](a)


if __name__ == "__main__":
    main()
