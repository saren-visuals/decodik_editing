# -*- coding: utf-8 -*-
"""Formato Tier list · convierte el guion en un plan con tiempos y posiciones.

  python tierlist_plan.py --trabajo 06_trabajo --listar          (palabras con índice y tiempo)
  python tierlist_plan.py --trabajo 06_trabajo --video cortado.mp4 [--barbilla 740]

Lee `06_trabajo/tierlist-guion.json` y `06_trabajo/palabras.json` y escribe
`06_trabajo/tierlist-plan.json`, que es lo que dibuja `construir_tierlist.py`.
- Cada elemento entra cuando se dice `dice` y baja a su nivel cuando se dice el
  `dice` de cada veredicto (se buscan en orden, después del anterior).
- Mide la barbilla para colocar subtítulo y tabla debajo de la cara.
- Calcula dónde se presenta cada foto grande sin pisar las miniaturas.
- Avisa de todo lo que se pisa, se sale de la zona o no se encuentra.
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
PLANTILLA = SKILL / "plantillas" / "tierlist" / "estilo.json"
AVISOS = []


def aviso(msg):
    AVISOS.append(msg)
    print("  [aviso]", msg)


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9ñ]", "", w)


def palabras_corregidas(trabajo, guion):
    pal = json.loads((trabajo / guion.get("palabras", "palabras.json")).read_text(encoding="utf-8"))
    for i, txt in guion.get("correcciones", {}).items():
        pal[int(i)]["w"] = txt
    for i, (t0, t1) in guion.get("tiempos", {}).items():
        pal[int(i)]["start"], pal[int(i)]["end"] = t0, t1
    return pal


def buscar(pal, frase, desde, nombre):
    """Índices [i0, i1] de la frase a partir de la palabra `desde`."""
    objetivo = [norm(x) for x in frase.split() if norm(x)]
    claves = [norm(p["w"]) for p in pal]
    for i in range(desde, len(pal) - len(objetivo) + 1):
        if claves[i:i + len(objetivo)] == objetivo:
            return i, i + len(objetivo) - 1
    aviso(f"no encuentro «{frase}» ({nombre}) a partir de la palabra {desde}: revisa `dice` o las correcciones")
    return None


def medir_barbilla(video):
    """Barbilla (y en 1080×1920) = mediana de la cara detectada en 7 fotogramas."""
    try:
        import cv2
    except ImportError:
        return None, None
    cap = cv2.VideoCapture(str(video))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    h_vid = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1920
    esc = 1920 / h_vid
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    caras = []
    for k in range(1, 8):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * k / 8))
        ok, fr = cap.read()
        if not ok:
            continue
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        fs = det.detectMultiScale(g, 1.1, 6, minSize=(int(g.shape[1] * 0.15),) * 2)
        if len(fs):
            x, y, w, h = max(fs, key=lambda f: f[2] * f[3])
            caras.append((y * esc, h * esc))
    cap.release()
    if not caras:
        return None, None
    caras.sort()
    y, h = caras[len(caras) // 2]
    return int(y + h * 1.12), int(y)  # barbilla, parte alta de la cara (frente)


def colores(n, base):
    if n == len(base):
        return base
    def hx(c):
        return [int(c[i:i + 2], 16) for i in (1, 3, 5)]
    out = []
    for k in range(n):
        p = k * (len(base) - 1) / max(1, n - 1)
        i = min(int(p), len(base) - 2)
        f = p - i
        a, b = hx(base[i]), hx(base[i + 1])
        out.append("#" + "".join(f"{round(a[j] + (b[j] - a[j]) * f):02X}" for j in range(3)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trabajo", required=True)
    ap.add_argument("--video")
    ap.add_argument("--barbilla", type=int)
    ap.add_argument("--listar", action="store_true")
    a = ap.parse_args()
    trabajo = Path(a.trabajo).resolve()
    guion = json.loads((trabajo / "tierlist-guion.json").read_text(encoding="utf-8"))
    pal = palabras_corregidas(trabajo, guion)

    if a.listar:
        frase = []
        for i, p in enumerate(pal):
            frase.append(f"{i}:{p['w']}[{p['start']:.2f}]")
            if re.search(r"[.?!]$", p["w"]) or len(frase) == 12:
                print("  ".join(frase)); frase = []
        if frase:
            print("  ".join(frase))
        return

    est = json.loads(PLANTILLA.read_text(encoding="utf-8"))
    for k, v in guion.get("estilo", {}).items():  # ajustes por vídeo
        est[k] = {**est.get(k, {}), **v} if isinstance(v, dict) else v
    Z = est["zona"]
    video = Path(a.video or guion["video"])
    if not video.is_absolute():
        video = (trabajo / video).resolve()

    # ---------- geometría ----------
    barbilla, frente = (a.barbilla, None) if a.barbilla else medir_barbilla(video)
    if barbilla is None:
        barbilla = guion.get("barbilla", 760)
        aviso(f"no he podido medir la cara: uso barbilla y={barbilla} (pásala con --barbilla)")
    t = est["tabla"]
    n = len(guion["niveles"])
    sub_y = barbilla + est["subtitulos"]["bajo_barbilla"]
    y0 = sub_y + est["subtitulos"]["px"] // 2 + est["hueco_sub"]
    y1 = min(y0 + n * t["fila_ideal"], Z["y1"])
    fila = (y1 - y0) / n
    if fila < t["fila_min"]:
        aviso(f"filas de {fila:.0f} px (mínimo {t['fila_min']}): la cara está baja; usa menos niveles o baja la tabla con estilo.zona.y1")
    x0, x1 = Z["x0"], Z["x1"]
    m = t["margen_mini"]
    mini = int(fila - 2 * m)
    pista0 = x0 + t["ancho_etiqueta"]
    cabe = int((x1 - pista0 - m) // (mini + m))
    geo = {"tabla": [x0, y0, x1, int(y1)], "fila": fila, "etiqueta": t["ancho_etiqueta"], "mini": mini,
           "sub_y": sub_y, "barbilla": barbilla, "frente": frente}

    # ---------- elementos ----------
    niveles_txt = [nv if isinstance(nv, str) else nv["texto"] for nv in guion["niveles"]]
    idx_nivel = {norm(x): k for k, x in enumerate(niveles_txt)}
    cols = colores(n, t["colores"])
    niveles = [{"texto": txt, "color": (nv.get("color") if isinstance(nv, dict) else None) or cols[k]}
               for k, (txt, nv) in enumerate(zip(niveles_txt, guion["niveles"]))]

    anim = est["animacion"]
    elementos, cursor, ultimo_fin = [], 0, -1.0
    ocupacion = {}  # nivel -> {id: pos}
    eventos = []    # (t, id, nivel, pos) para saber qué miniaturas hay en cada momento
    for el in guion["elementos"]:
        r = buscar(pal, el.get("dice", el["id"]), cursor, el["id"])
        if not r:
            continue
        entra = max(0.0, pal[r[0]]["start"] - 0.05)
        cursor = r[1] + 1
        if entra < ultimo_fin:
            aviso(f"{el['id']} entra a {entra:.2f} s y el anterior aún se mueve hasta {ultimo_fin:.2f} s: dos fotos grandes a la vez")
        pasos, c2 = [], cursor
        for v in el.get("veredictos", []):
            k = idx_nivel.get(norm(v["nivel"]))
            if k is None:
                aviso(f"{el['id']}: el nivel «{v['nivel']}» no está en `niveles`")
                continue
            rv = buscar(pal, v["dice"], c2, f"{el['id']} → {v['nivel']}")
            if not rv:
                continue
            c2 = rv[1] + 1
            tv = pal[rv[1]]["start"]
            for occ in ocupacion.values():
                occ.pop(el["id"], None)
            fila_occ = ocupacion.setdefault(k, {})
            pos = max(fila_occ.values(), default=-1) + 1
            if pos >= cabe:
                aviso(f"{el['id']}: no cabe en «{niveles_txt[k]}» ({cabe} por fila)")
            fila_occ[el["id"]] = pos
            pasos.append({"t": round(tv, 3), "nivel": k, "pos": pos})
            eventos.append((tv, el["id"], k, pos))
        if not pasos:
            aviso(f"{el['id']} no tiene veredicto: se quedaría grande en pantalla")
            continue
        cursor = max(cursor, c2)
        ultimo_fin = pasos[-1]["t"] + anim["guardado"]

        # foto grande: en la parte libre de la pista, sin pisar miniaturas ya guardadas
        estado = {}
        for (tv, eid, k, pos) in sorted(eventos):
            if tv <= entra and eid != el["id"]:
                estado[eid] = (k, pos)
        borde = max([pista0 + m + (pos + 1) * (mini + m) for (k, pos) in estado.values()], default=pista0)
        libre0, libre1 = borde + t["aire_grande"], x1 - m
        w = min(t["ancho_grande"], libre1 - libre0)
        if w < t["ancho_grande_min"]:
            aviso(f"{el['id']}: sin sitio para la foto grande ({w:.0f} px): se presenta encima de las miniaturas")
            w = t["ancho_grande"]
            libre0 = pista0 + m
        cx = max(libre0 + w / 2, min((pista0 + x1) / 2, libre1 - w / 2))
        grande = [round(cx - w / 2), y0 + m, round(cx + w / 2), int(y1) - m]
        elementos.append({"id": el["id"], "nombre": el.get("nombre", el["id"]),
                          "imagen": el.get("imagen", f"../03_recursos/tierlist/{el['id']}.jpg"),
                          "foco": el.get("foco", [0.5, 0.5]), "entra": round(entra, 3),
                          "grande": grande, "pasos": pasos})

    # ---------- fin de la tabla ----------
    if guion.get("fin_dice"):
        r = buscar(pal, guion["fin_dice"], cursor, "fin de la tabla")
        tabla_fin = pal[r[0]]["start"] if r else ultimo_fin + 0.6
    else:
        tabla_fin = None
        for i in range(cursor, len(pal)):
            if re.search(r"[.?!]$", pal[i - 1]["w"]):
                tabla_fin = pal[i]["start"]
                break
        tabla_fin = tabla_fin or (ultimo_fin + 0.6)
    tabla_fin = max(tabla_fin, ultimo_fin + 0.3)

    # ---------- CTA ----------
    seguir = None
    sg = guion.get("seguir")
    if sg and sg.get("usuario"):
        r = None
        for frase in [sg.get("dice")] + ["si quieres", "si queres", "seguime", "sigueme", "sígueme"]:
            if frase:
                r = buscar(pal, frase, cursor, "CTA") if frase == sg.get("dice") else _silencioso(pal, frase, cursor)
                if r:
                    break
        if r:
            seguir = {"usuario": sg["usuario"], "avatar": sg.get("avatar", "../04_marca/avatar.png"),
                      "entra": round(pal[r[0]]["start"], 3), "pulsa": sg.get("pulsa", 1.0)}
        else:
            aviso("no encuentro la llamada a seguir: pon `seguir.dice`")

    # ---------- efectos (solo si el usuario los ha dejado) ----------
    sfx = []
    carpeta = trabajo.parent / "05_musica" / "efectos"
    def efecto(*nombres):
        for f in sorted(carpeta.glob("*")) if carpeta.exists() else []:
            if f.suffix.lower() in (".wav", ".mp3", ".m4a", ".aac", ".ogg") and any(x in f.stem.lower() for x in nombres):
                return str(f)
    entrada, guardar = efecto("whoosh", "swoosh", "entrada"), efecto("pop", "clic", "click", "guardar")
    for el in elementos:
        if entrada:
            sfx.append({"t": max(0, el["entra"] - 0.03), "archivo": entrada, "vol": 0.45})
        if guardar:
            for p in el["pasos"]:
                sfx.append({"t": p["t"] + anim["guardado"] - 0.08, "archivo": guardar, "vol": 0.5})
    if entrada:
        sfx.append({"t": tabla_fin - 0.35, "archivo": entrada, "vol": 0.5})

    plan = {"video": str(video), "fps": 30, "palabras": guion.get("palabras", "palabras.json"),
            "correcciones": guion.get("correcciones", {}), "tiempos": guion.get("tiempos", {}),
            "estilo": est, "geometria": geo, "titulo": guion["titulo"], "niveles": niveles,
            "elementos": elementos, "tabla_fin": round(tabla_fin, 3), "seguir": seguir, "sfx": sfx}
    (trabajo / "tierlist-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\nBarbilla y={barbilla} · subtítulo y={sub_y} · tabla {x0}-{x1} × {y0}-{int(y1)} · filas de {fila:.0f} px · miniaturas {mini} px ({cabe} por fila)")
    print(f"{'elemento':<14}{'entra':>7}   veredictos")
    for el in elementos:
        v = ", ".join(f"{p['t']:.2f}s → {niveles_txt[p['nivel']]}" for p in el["pasos"])
        print(f"{el['id']:<14}{el['entra']:>7.2f}   {v}")
    print(f"tabla se va a {tabla_fin:.2f} s" + (f" · CTA a {seguir['entra']:.2f} s" if seguir else ""))
    print(f"efectos: {len(sfx)}" + ("" if sfx else " (no hay en 05_musica/efectos: va sin efectos)"))
    print("OK tierlist-plan.json" + (f" · {len(AVISOS)} avisos" if AVISOS else ""))


def _silencioso(pal, frase, desde):
    objetivo = [norm(x) for x in frase.split() if norm(x)]
    claves = [norm(p["w"]) for p in pal]
    for i in range(desde, len(pal) - len(objetivo) + 1):
        if claves[i:i + len(objetivo)] == objetivo:
            return i, i + len(objetivo) - 1
    return None


if __name__ == "__main__":
    main()
