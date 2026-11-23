"""Exporta un montaje «Mi historia» (storyboard-historia.json + subtítulos) a un BORRADOR DE CAPCUT editable.

Uso (con CapCut CERRADO):
  python exportar_capcut.py --trabajo 06_trabajo --nombre "Mi historia (Decodik)"
        --plantilla "<carpeta de un borrador de CapCut del usuario>"   (se copia; el original no se toca)
        [--plantilla-audio "<borrador con un audio importado>"] [--carpeta-capcut <com.lveditor.draft>]

CapCut no tiene una forma de controlarlo desde fuera: lo que hace este script es escribir el borrador
(draft_content.json, igual que lo guarda CapCut) usando un borrador del propio usuario como plantilla, para que
el formato coincida con su versión. Se registra en root_meta_info.json (con copia de seguridad) y aparece en la
lista de proyectos al abrir CapCut.

Qué queda en el borrador (estructura «superposiciones», por defecto):
- Pista principal: la toma ENTERA, sin cortar, con su sonido.
- Superposición 1: cada B-roll vertical o foto vertical a pantalla completa, en su tramo (tramos.py); y, para los
  HORIZONTALES, una copia escalada a pantalla completa con el efecto «Desenfocar» aplicado al clip (de fondo).
- Superposición 2: el ORIGINAL de cada horizontal, a lo ancho y arriba (y = 22 %), encima de su fondo desenfocado.
  Todo editable en CapCut. Los HDR del iPhone van como copia SDR (03_recursos/capcut/). Sin sonido.
(«--estructura secuencia»: todo seguido en la pista principal, recuadros con el fondo «desenfocar» de CapCut y la
voz en una pista de audio aparte.)
- Pista de texto: un texto por trozo de subtitulos.json con el estilo de la plantilla (fuente, tamaño, sombra,
  posición) y la palabra clave en el color de acento.
Lo que se retoca en CapCut si hace falta: zooms de las fotos (aquí van quietas) y el color de los clips HDR.
"""
import argparse
import copy
import json
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from comun import aviso, codificador, error, filtro_sdr, leer_json, sondear
from tramos import cargar_indice, resolver, _clave

US = 1_000_000
CARPETA = Path.home() / "AppData/Local/CapCut/User Data/Projects/com.lveditor.draft"
ACENTO = [1.0, 0.902, 0.0]    # #FFE600
Y_RECUADRO = 0.22


def nid():
    u = str(uuid.uuid4()).upper()
    return u[:14] + u[14:23].lower() + u[23:]


def indexar(d):
    return {m["id"]: (k, m) for k, v in d["materials"].items() if isinstance(v, list)
            for m in v if isinstance(m, dict) and "id" in m}


def clonar_refs(seg, idx_plantilla, materiales, saltar=("drafts",)):
    nuevos = []
    for r in seg["extra_material_refs"]:
        if r not in idx_plantilla:
            continue
        lista, m = idx_plantilla[r]
        if lista in saltar:
            continue
        c = copy.deepcopy(m)
        c["id"] = nid()
        materiales.setdefault(lista, []).append(c)
        nuevos.append((lista, c))
    seg["extra_material_refs"] = [c["id"] for _, c in nuevos]
    return dict(nuevos)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trabajo", required=True)
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--plantilla", required=True)
    ap.add_argument("--plantilla-audio")
    ap.add_argument("--carpeta-capcut", default=str(CARPETA))
    ap.add_argument("--storyboard", default="storyboard-historia.json")
    ap.add_argument("--estructura", choices=["superposiciones", "secuencia"], default="superposiciones",
                    help="superposiciones: la toma entera en la pista principal y los recursos en una pista encima "
                         "(por defecto); secuencia: todo seguido en la pista principal y la voz aparte")
    a = ap.parse_args()
    tr = Path(a.trabajo).resolve()
    proyecto = tr.parent
    raiz = Path(a.carpeta_capcut)
    plantilla = Path(a.plantilla)
    destino = raiz / a.nombre
    if destino.exists():
        error(f"Ya existe {destino}: elige otro nombre (no piso borradores)")

    sb = leer_json(tr / a.storyboard)
    toma = tr / "cortado.mp4"
    voz = tr / "voz_cortada.wav"
    total = sondear(toma)["duracion"]
    planos = resolver(sb["planos"], proyecto, total)
    subs = leer_json(tr / "subtitulos" / "subtitulos.json")
    indice = cargar_indice(proyecto)

    dp = leer_json(plantilla / "draft_content.json")
    ip = indexar(dp)
    vtrack = next(t for t in dp["tracks"] if t["type"] == "video" and t["segments"])
    vseg_t = vtrack["segments"][0]
    vmat_t = ip[vseg_t["material_id"]][1]
    ttrack = next((t for t in dp["tracks"] if t["type"] == "text" and t["segments"]), None)
    if not ttrack:
        error("La plantilla necesita al menos un texto (subtítulo) para copiar su estilo")
    tseg_t = ttrack["segments"][0]
    tmat_t = ip[tseg_t["material_id"]][1]
    canvas_t = next(m for _, m in ip.values() if m.get("type", "").startswith("canvas"))
    da = leer_json(Path(a.plantilla_audio) / "draft_content.json") if a.plantilla_audio else dp
    ia = indexar(da)
    amat_t = next((m for m in da["materials"].get("audios", []) if m["type"] in ("music", "extract_music")), None)
    aseg_t = next((s for t in da["tracks"] if t["type"] == "audio" for s in t["segments"]
                   if amat_t and s["material_id"] == amat_t["id"]), None)
    if not amat_t and a.estructura == "secuencia":   # en «superposiciones» la voz va en la propia toma
        error("No encuentro un audio importado en la plantilla de audio: pasa --plantilla-audio")

    d = copy.deepcopy(dp)
    d["id"] = nid()
    for k, v in d["materials"].items():
        if isinstance(v, list):
            d["materials"][k] = []
    mats = d["materials"]
    seg_v, seg_t = [], []

    def material_video(src, tipo):
        info = sondear(src) if tipo == "video" else {}
        rec = indice.get(_clave(str(src.relative_to(proyecto)).replace("\\", "/")), {}) if src.is_relative_to(proyecto) else {}
        w, h = rec.get("ancho") or info.get("ancho") or 1080, rec.get("alto") or info.get("alto") or 1920
        m = copy.deepcopy(vmat_t)
        m.update({"id": nid(), "unique_id": uuid.uuid4().hex, "type": tipo, "path": src.as_posix(),
                  "material_name": src.name, "width": w, "height": h,
                  "duration": int(info["duracion"] * US) if tipo == "video" else 10_800_000_000,
                  "has_audio": tipo == "video"})
        mats.setdefault("videos", []).append(m)
        return m, w, h

    superponer = a.estructura == "superposiciones"
    seg_o, seg_o2 = [], []   # superposición 1 (fondos y verticales) y superposición 2 (originales en recuadro)

    def efecto_desenfocar():
        """«Desenfocar» aplicado a UN clip (apply_target_type 0), copiado de un borrador del usuario que ya lo use así."""
        for f in sorted(raiz.glob("*/draft_content.json")):
            try:
                dd = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            for e in dd.get("materials", {}).get("video_effects", []):
                if e.get("name") == "Desenfocar" and e.get("apply_target_type") == 0:
                    return e
        return None
    blur_t = efecto_desenfocar() if superponer else None
    if superponer and blur_t is None:
        aviso("No encuentro «Desenfocar» aplicado a un clip en tus borradores: los fondos irán sin desenfocar")

    def preparar(src, hdr, foto):
        """Los clips HDR del iPhone se pasan a SDR (copia en 03_recursos/capcut/) para que no salgan lavados."""
        if not hdr or foto:
            return src
        dest_dir = proyecto / "03_recursos" / "capcut"
        dest_dir.mkdir(parents=True, exist_ok=True)
        out = dest_dir / (src.stem + "_" + src.suffix.lstrip(".").lower() + "_sdr.mp4")   # con la extensión: hay clips que solo se distinguen por ella
        if not out.exists():
            pre = ",".join(filtro_sdr(sondear(src)))
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", pre, "-an", *codificador(),
                            "-pix_fmt", "yuv420p", str(out)], check=True)
            aviso(f"preparado para CapCut: {out.name}")
        return out

    def segmento_sobre(m, t0, t1, ini, escala, y, render, blur=False):
        s = copy.deepcopy(vseg_t)
        s["id"] = nid()
        clonar_refs(s, ip, mats)
        s.update({"material_id": m["id"], "volume": 0.0, "target_timerange": {"start": t0, "duration": t1 - t0},
                  "source_timerange": {"start": ini, "duration": t1 - t0}, "render_index": render, "track_render_index": render})
        s["clip"]["scale"] = {"x": escala, "y": escala}
        s["clip"]["transform"] = {"x": 0.0, "y": y}
        s["uniform_scale"] = {"on": True, "value": escala}
        if blur and blur_t is not None:
            e = copy.deepcopy(blur_t)
            e.update({"id": nid(), "bind_segment_id": ""})
            mats.setdefault("video_effects", []).append(e)
            s["extra_material_refs"].append(e["id"])
        return s

    if superponer:   # la toma ENTERA, sin cortar, en la pista principal y con su sonido
        s = copy.deepcopy(vseg_t)
        s["id"] = nid()
        clonar_refs(s, ip, mats)
        m, w, h = material_video(toma, "video")
        s.update({"material_id": m["id"], "volume": 1.0, "source_timerange": {"start": 0, "duration": int(total * US)},
                  "target_timerange": {"start": 0, "duration": int(total * US)}})
        s["clip"]["scale"] = {"x": 1.0, "y": 1.0}
        s["clip"]["transform"] = {"x": 0.0, "y": 0.0}
        seg_v.append(s)

    t = 0
    for k, p in enumerate(planos):
        t0 = int(round(p["t0"] * US))
        t1 = int(round((planos[k + 1]["t0"] if k + 1 < len(planos) else total) * US))
        if t1 <= t0:
            continue
        if superponer and p["tipo"] == "camara":
            continue     # se ve la toma de la pista principal
        if superponer:
            src = proyecto / p["src"]
            foto = p["tipo"] == "foto"
            rec = indice.get(_clave(p["src"]), {})
            listo = preparar(src, bool(rec.get("hdr")), foto)
            m, w, h = material_video(listo, "photo" if foto else "video")
            ini = int(round(p.get("in_usado", 0) * US)) if not foto else 0
            ajuste, cubrir = min(1080 / w, 1920 / h), max(1080 / w, 1920 / h)
            if p.get("modo_usado") == "recuadro":
                # debajo: la misma imagen escalada a pantalla completa y con «Desenfocar»
                seg_o.append(segmento_sobre(m, t0, t1, ini, cubrir / ajuste, 0.0, 1, blur=True))
                # encima: el ORIGINAL, a lo ancho y arriba (CapCut: +1 arriba, -1 abajo)
                y = (0.5 - (Y_RECUADRO + (1080 * h / w) / 1920 / 2)) * 2
                seg_o2.append(segmento_sobre(m, t0, t1, ini, (1080 / w) / ajuste, y, 2))
            else:
                seg_o.append(segmento_sobre(m, t0, t1, ini, cubrir / ajuste, 0.0, 1))
            continue
        s = copy.deepcopy(vseg_t)
        s["id"] = nid()
        refs = clonar_refs(s, ip, mats)
        s["volume"] = 0.0
        s["target_timerange"] = {"start": t0, "duration": t1 - t0}
        if p["tipo"] == "camara":
            m, w, h = material_video(toma, "video")
            s["source_timerange"] = {"start": t0, "duration": t1 - t0}
            escala, y = 1.0, 0.0
        else:
            src = proyecto / p["src"]
            m, w, h = material_video(src, "video" if p["tipo"] == "broll" else "photo")
            ini = int(round(p.get("in_usado", 0) * US)) if p["tipo"] == "broll" else 0
            s["source_timerange"] = {"start": ini, "duration": t1 - t0}
            ajuste = min(1080 / w, 1920 / h)
            cubrir = max(1080 / w, 1920 / h)
            if p.get("modo_usado") == "recuadro":
                escala = (1080 / w) / ajuste                     # a lo ancho
                y = (0.5 - (Y_RECUADRO + (1080 * h / w) / 1920 / 2)) * 2   # arriba (CapCut: +1 arriba, -1 abajo)
                lienzo = next((c for c in refs.values() if c.get("type", "").startswith("canvas")), None)
                if lienzo is not None:
                    lienzo.update({"type": "canvas_blur", "blur": 0.375})
            else:
                escala, y = cubrir / ajuste, 0.0
        s["material_id"] = m["id"]
        s["clip"]["scale"] = {"x": escala, "y": escala}
        s["clip"]["transform"] = {"x": 0.0, "y": y}
        s["uniform_scale"] = {"on": True, "value": escala}
        s["hdr_settings"] = {"mode": 1, "intensity": 1.0, "nits": 1000}
        seg_v.append(s)

    def voz_aparte():
        am = copy.deepcopy(amat_t)
        durv = int(total * US)   # la voz sale de la misma toma: dura lo mismo
        am.update({"id": nid(), "type": "music", "name": voz.stem, "path": voz.as_posix(), "duration": durv})
        mats.setdefault("audios", []).append(am)
        sa = copy.deepcopy(aseg_t) if aseg_t else copy.deepcopy(vseg_t)
        sa["id"] = nid()
        clonar_refs(sa, ia, mats)
        sa.update({"material_id": am["id"], "volume": 1.0, "source_timerange": {"start": 0, "duration": durv},
                   "target_timerange": {"start": 0, "duration": durv}, "clip": None, "hdr_settings": None})
        return sa

    # voz (pista aparte solo en «secuencia»)
    sa = None
    if not superponer:
        sa = voz_aparte()

    # subtítulos con el estilo de la plantilla
    estilo = json.loads(tmat_t["content"])["styles"][0]
    for c in subs:
        texto = c["texto"]
        estilos, pos = [], 0
        for w in c["palabras"]:
            i = texto.find(w["texto"], pos)
            if i < 0:
                continue
            if w["clave"]:
                e = copy.deepcopy(estilo)
                e["fill"]["content"]["solid"]["color"] = ACENTO
                e["range"] = [i, i + len(w["texto"])]
                estilos.append(e)
            pos = i + len(w["texto"])
        base = []
        corte = 0
        for e in sorted(estilos, key=lambda e: e["range"][0]):
            if e["range"][0] > corte:
                b = copy.deepcopy(estilo); b["range"] = [corte, e["range"][0]]; base.append(b)
            base.append(e); corte = e["range"][1]
        if corte < len(texto):
            b = copy.deepcopy(estilo); b["range"] = [corte, len(texto)]; base.append(b)
        contenido = json.dumps({"text": texto, "styles": base}, ensure_ascii=False)
        tm = copy.deepcopy(tmat_t)
        tm.update({"id": nid(), "content": contenido, "base_content": contenido, "recognize_text": texto,
                   "recognize_task_id": "", "type": "text",
                   "words": {"start_time": [], "end_time": [], "text": []}})
        mats.setdefault("texts", []).append(tm)
        st = copy.deepcopy(tseg_t)
        st["id"] = nid()
        clonar_refs(st, ip, mats)
        st["material_id"] = tm["id"]
        fin_c = min(c["end"], total)   # el último subtítulo no puede pasar del final del vídeo
        st["target_timerange"] = {"start": int(c["start"] * US), "duration": int((fin_c - c["start"]) * US)}
        seg_t.append(st)

    def pista(tipo, segs, base_pista):
        p = {k: v for k, v in base_pista.items() if k != "segments"}
        p.update({"id": nid(), "type": tipo, "segments": segs})
        return p

    atrack = next((t for t in da["tracks"] if t["type"] == "audio"), {"type": "audio", "flag": 0, "attribute": 0, "name": "", "is_default_name": True})
    if superponer:
        sobre = pista("video", seg_o, vtrack)
        sobre.update({"flag": 2, "attribute": 0})      # superposición 1: fondos desenfocados y verticales
        sobre2 = pista("video", seg_o2, vtrack)
        sobre2.update({"flag": 2, "attribute": 0})     # superposición 2: originales en recuadro
        for s in seg_t:
            s["track_render_index"] = 3
        d["tracks"] = [pista("video", seg_v, vtrack), sobre, sobre2, pista("text", seg_t, ttrack)]
    else:
        d["tracks"] = [pista("video", seg_v, vtrack), pista("text", seg_t, ttrack), pista("audio", [sa], atrack)]
    d["duration"] = int(total * US)
    d["canvas_config"] = {"ratio": "original", "width": 1080, "height": 1920, "background": None}

    # Carpeta del borrador (receta comprobada con CapCut 9.8):
    # - se copia la carpeta ENTERA de la plantilla: CapCut necesita sus archivos internos (Resources, attachment*,
    #   key_value, draft_settings…) y la MISMA línea de tiempo (Timelines/project.json y su id);
    # - se quitan solo draft.extra, las copias template*.tmp y los .bak: guardan el montaje anterior y, si no
    #   coinciden con el nuevo, CapCut se niega a abrirlo;
    # - el montaje nuevo se escribe en draft_content.json y en Timelines/<id>/draft_content.json.
    ahora = int(time.time() * 1_000_000)
    d["id"] = dp["id"]
    shutil.copytree(plantilla, destino, ignore=shutil.ignore_patterns("*.bak", "template*.tmp", "draft.extra", "draft_cover.jpg"))
    texto = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    (destino / "draft_content.json").write_text(texto, encoding="utf-8")
    proj = destino / "Timelines" / "project.json"
    if proj.exists():
        tl = leer_json(proj)["main_timeline_id"]
        (destino / "Timelines" / tl).mkdir(parents=True, exist_ok=True)
        (destino / "Timelines" / tl / "draft_content.json").write_text(texto, encoding="utf-8")
    # portada: el primer fotograma del montaje
    portada = proyecto / "07_entrega" / "portada.jpg"
    if not portada.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(toma), "-frames:v", "1", "-vf", "scale=540:-2", str(portada)])
    if portada.exists():
        shutil.copy2(portada, destino / "draft_cover.jpg")
    meta = leer_json(plantilla / "draft_meta_info.json")
    nuevo_id = nid()
    meta.update({"draft_id": nuevo_id, "draft_name": a.nombre, "draft_fold_path": destino.as_posix(),
                 "draft_root_path": raiz.as_posix(), "tm_duration": int(total * US), "tm_draft_create": ahora,
                 "tm_draft_modified": ahora, "draft_materials": [], "draft_segment_extra_info": []})
    (destino / "draft_meta_info.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    rm = raiz / "root_meta_info.json"
    shutil.copy2(rm, rm.with_suffix(f".json.antes-decodik-{time.strftime('%Y%m%d-%H%M%S')}"))
    r = leer_json(rm)
    plantilla_reg = next((x for x in r["all_draft_store"] if Path(x["draft_fold_path"]).name == plantilla.name), r["all_draft_store"][0])
    reg = copy.deepcopy(plantilla_reg)
    reg.update({"draft_id": nuevo_id, "draft_name": a.nombre, "draft_fold_path": destino.as_posix(),
                "draft_json_file": (destino / "draft_content.json").as_posix(), "draft_cover": (destino / "draft_cover.jpg").as_posix(),
                "tm_draft_create": ahora, "tm_draft_modified": ahora, "tm_duration": int(total * US)})
    r["all_draft_store"].insert(0, reg)
    if isinstance(r.get("draft_ids"), int):
        r["draft_ids"] += 1
    rm.write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
    aviso(f"Borrador de CapCut creado: {destino} ({len(seg_v)} en la pista principal, {len(seg_o)} + {len(seg_o2)} superposiciones, {len(seg_t)} subtítulos). "
          f"Abre CapCut y búscalo como «{a.nombre}».")


if __name__ == "__main__":
    main()
