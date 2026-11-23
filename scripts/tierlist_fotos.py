# -*- coding: utf-8 -*-
"""Formato Tier list · busca, enseña y elige las fotos de cada elemento.

  python tierlist_fotos.py buscar --trabajo 06_trabajo [--n 8] [--solo natacion,boxeo]
  python tierlist_fotos.py hoja   --trabajo 06_trabajo
  python tierlist_fotos.py elegir --trabajo 06_trabajo natacion=3 boxeo=1@0.5,0.3

Lee `tierlist-guion.json` (campo `busqueda` de cada elemento, mejor en inglés).
Fuentes, por orden: Pexels (solo si existe la variable PEXELS_API_KEY),
Openverse (fotos con licencia libre para uso comercial) y Wikimedia Commons.
Los candidatos van a 03_recursos/tierlist/candidatos/<id>/ y la foto elegida a
03_recursos/tierlist/<id>.jpg. Los créditos de cada foto elegida se apuntan en
07_entrega/creditos-fotos.txt (las licencias CC BY piden citar al autor).
"""
import argparse, io, json, os, shutil, sys, time, urllib.parse, urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

SKILL = Path(__file__).resolve().parent.parent
UA = "DecodikEditor/1.2 (video editing tool)"
MAX_BYTES = 20 * 1024 * 1024
LADO_MIN = 700  # lado corto mínimo de una foto útil


def _get(url, cabeceras=None, binario=False, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(cabeceras or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        datos = r.read(MAX_BYTES + 1)
    if len(datos) > MAX_BYTES:
        raise ValueError("archivo demasiado grande")
    return datos if binario else json.loads(datos.decode("utf-8"))


# ---------------- fuentes ----------------
def pexels(q, n):
    clave = os.environ.get("PEXELS_API_KEY")
    if not clave:
        return []
    u = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode({"query": q, "per_page": n * 2})
    out = []
    for p in _get(u, {"Authorization": clave}).get("photos", []):
        out.append({"url": p["src"]["large2x"], "ancho": p["width"], "alto": p["height"],
                    "autor": p.get("photographer", ""), "licencia": "Pexels License",
                    "pagina": p.get("url", ""), "fuente": "pexels"})
    return out


def openverse(q, n):
    u = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
        {"q": q, "license_type": "commercial,modification", "page_size": 20, "mature": "false"})
    out = []
    for r in _get(u).get("results", []):
        w, h = r.get("width") or 0, r.get("height") or 0
        if w and h and min(w, h) < LADO_MIN:
            continue
        lic = (r.get("license") or "").upper()
        if r.get("license_version"):
            lic = f"CC {lic} {r['license_version']}" if lic not in ("CC0", "PDM") else lic
        out.append({"url": r["url"], "ancho": w, "alto": h, "autor": r.get("creator") or "",
                    "licencia": lic, "pagina": r.get("foreign_landing_url", ""), "fuente": "openverse"})
    return out


def commons(q, n):
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": f"filetype:bitmap {q}", "gsrlimit": max(20, n * 3),
        "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 1600})
    paginas = _get(u).get("query", {}).get("pages", {})
    out = []
    for p in sorted(paginas.values(), key=lambda p: p.get("index", 99)):
        ii = (p.get("imageinfo") or [{}])[0]
        if min(ii.get("width", 0), ii.get("height", 0)) < LADO_MIN:
            continue
        md = ii.get("extmetadata", {})
        autor = md.get("Artist", {}).get("value", "")
        autor = autor.split(">")[-2].split("<")[0] if ">" in autor else autor
        out.append({"url": ii.get("thumburl") or ii.get("url"), "ancho": ii.get("width"), "alto": ii.get("height"),
                    "autor": autor.strip(), "licencia": md.get("LicenseShortName", {}).get("value", ""),
                    "pagina": ii.get("descriptionurl", ""), "fuente": "commons"})
    return out


def descargar(c, destino):
    datos = _get(c["url"], binario=True)
    im = Image.open(io.BytesIO(datos))
    im.verify()  # solo imágenes de verdad
    im = Image.open(io.BytesIO(datos))
    im = ImageOps.exif_transpose(im).convert("RGB")
    if min(im.size) < LADO_MIN:
        raise ValueError("demasiado pequeña")
    im.thumbnail((1800, 1800), Image.LANCZOS)
    im.save(destino, quality=92)
    return im.size


def rutas(trabajo):
    trabajo = Path(trabajo).resolve()
    proyecto = trabajo.parent
    return trabajo, proyecto / "03_recursos" / "tierlist", proyecto / "07_entrega"


def leer_guion(trabajo):
    return json.loads((trabajo / "tierlist-guion.json").read_text(encoding="utf-8"))


# ---------------- comandos ----------------
def cmd_buscar(a):
    trabajo, recursos, _ = rutas(a.trabajo)
    guion = leer_guion(trabajo)
    solo = set(a.solo.split(",")) if a.solo else None
    for el in guion["elementos"]:
        if solo and el["id"] not in solo:
            continue
        q = el.get("busqueda") or el.get("nombre") or el["id"]
        carpeta = recursos / "candidatos" / el["id"]
        if carpeta.exists():
            shutil.rmtree(carpeta)
        carpeta.mkdir(parents=True)
        vistos, cands = set(), []
        palabras = q.split()
        consultas = [q] + ([" ".join(palabras[:2])] if len(palabras) > 2 else [])
        for fuente, consulta in [(f, c) for c in consultas for f in (pexels, openverse, commons)]:
            if len(cands) >= a.n * 2:
                break
            try:
                for c in fuente(consulta, a.n):
                    # sin «ND» (no deja recortar) ni «NC» (no deja uso comercial)
                    if any(x in c["licencia"].upper().replace("-", " ").split() for x in ("ND", "NC")):
                        continue
                    if c["url"] and c["url"] not in vistos:
                        vistos.add(c["url"])
                        cands.append(c)
            except Exception as e:  # una fuente caída no para la búsqueda
                print(f"  [aviso] {fuente.__name__}: {e}", file=sys.stderr)
        guardados = []
        for c in cands:
            if len(guardados) >= a.n:
                break
            k = len(guardados) + 1
            try:
                c["tam"] = descargar(c, carpeta / f"{k}.jpg")
                c["n"] = k
                guardados.append(c)
            except Exception as e:
                print(f"  [salto] {c['url'][:70]}… ({e})", file=sys.stderr)
            time.sleep(0.2)
        (carpeta / "info.json").write_text(json.dumps(guardados, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{el['id']:<14} «{q}» → {len(guardados)} fotos")
    cmd_hoja(a)


def cmd_hoja(a):
    trabajo, recursos, _ = rutas(a.trabajo)
    guion = leer_guion(trabajo)
    T, ET = 230, 220
    filas = [el for el in guion["elementos"] if (recursos / "candidatos" / el["id"] / "info.json").exists()]
    cols = max([len(json.loads((recursos / "candidatos" / el["id"] / "info.json").read_text(encoding="utf-8"))) for el in filas] + [1])
    hoja = Image.new("RGB", (ET + cols * (T + 8), len(filas) * (T + 8) + 8), "#151515")
    d = ImageDraw.Draw(hoja)
    f = ImageFont.truetype(str(SKILL / "fonts" / "Figtree-Bold.ttf"), 26)
    fn = ImageFont.truetype(str(SKILL / "fonts" / "Figtree-Black.ttf"), 30)
    for i, el in enumerate(filas):
        y = 8 + i * (T + 8)
        d.text((14, y + T // 2), el["id"], font=f, fill="white", anchor="lm")
        info = json.loads((recursos / "candidatos" / el["id"] / "info.json").read_text(encoding="utf-8"))
        for j, c in enumerate(info):
            im = ImageOps.fit(Image.open(recursos / "candidatos" / el["id"] / f"{c['n']}.jpg"), (T, T), Image.LANCZOS)
            x = ET + j * (T + 8)
            hoja.paste(im, (x, y))
            d.rectangle((x, y, x + 44, y + 40), fill="#000000")
            d.text((x + 22, y + 20), str(c["n"]), font=fn, fill="#F4EE00", anchor="mm")
    salida = recursos / "candidatos" / "_hoja.jpg"
    hoja.save(salida, quality=88)
    print("Hoja de candidatos:", salida)


def cmd_elegir(a):
    trabajo, recursos, entrega = rutas(a.trabajo)
    creditos = entrega / "creditos-fotos.txt"
    previos = {}
    if creditos.exists():
        for ln in creditos.read_text(encoding="utf-8").splitlines():
            if " · " in ln:
                previos[ln.split(" · ")[0]] = ln
    elecciones = {}
    for arg in a.elecciones:
        el, _, resto = arg.partition("=")
        n, _, foco = resto.partition("@")
        info = json.loads((recursos / "candidatos" / el / "info.json").read_text(encoding="utf-8"))
        c = next(x for x in info if x["n"] == int(n))
        shutil.copyfile(recursos / "candidatos" / el / f"{n}.jpg", recursos / f"{el}.jpg")
        previos[el] = f"{el} · {c['autor'] or 'autor desconocido'} · {c['licencia']} · {c['pagina']}"
        elecciones[el] = {"imagen": f"../03_recursos/tierlist/{el}.jpg"}
        if foco:
            elecciones[el]["foco"] = [float(v) for v in foco.split(",")]
        print(f"{el}: foto {n} ({c['licencia']}, {c['fuente']})")
    entrega.mkdir(exist_ok=True)
    creditos.write_text("Créditos de las fotos (pon los CC BY en la descripción del post)\n" +
                        "\n".join(previos[k] for k in sorted(previos)) + "\n", encoding="utf-8")
    # apunta la foto (y el foco) en el guion
    g = leer_guion(trabajo)
    for el in g["elementos"]:
        if el["id"] in elecciones:
            el.update(elecciones[el["id"]])
    (trabajo / "tierlist-guion.json").write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("buscar"); b.add_argument("--trabajo", required=True); b.add_argument("--n", type=int, default=8); b.add_argument("--solo")
    h = sub.add_parser("hoja"); h.add_argument("--trabajo", required=True)
    e = sub.add_parser("elegir"); e.add_argument("--trabajo", required=True); e.add_argument("elecciones", nargs="+")
    a = ap.parse_args()
    {"buscar": cmd_buscar, "hoja": cmd_hoja, "elegir": cmd_elegir}[a.cmd](a)


if __name__ == "__main__":
    main()
