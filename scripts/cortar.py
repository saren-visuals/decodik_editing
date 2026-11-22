"""Pasada 1 · Corta la toma según keep.json y recalcula los tiempos de las palabras.

Uso:
  python cortar.py --trabajo 06_trabajo --keep 06_trabajo/keep.json [--correcciones 06_trabajo/correcciones.json]
                   [--palabras 06_trabajo/palabras-bruto.json] [--aire 0.08]
keep.json: [{"start": 0.0, "end": 3.2}, ...]  (o el propuesta.json entero)
Genera: cortado.mp4, voz_cortada.wav, preview.mp4, palabras.json, cortes.json
Al final vuelve a transcribir voz_cortada.wav (usa vocab.txt) para comprobar que no falta ninguna
palabra y sacar tiempos exactos para los subtítulos. --sin-verificar lo salta.
"""
import argparse
from pathlib import Path

from audio import energia_db, leer_mono, punto_mas_silencioso
from comun import (AUDIO_FADE, a_rejilla, aviso, codificador, escribir_json, ffmpeg, filtro_desde_archivo, leer_json,
                   normalizar_palabra)


def ajustar(tramos, db, aire):
    """Lleva cada borde al punto más silencioso cercano, sin entrar en la palabra ni en el tramo vecino."""
    tramos = sorted(tramos, key=lambda x: x["start"])
    out = []
    for k, t in enumerate(tramos):
        prev_fin = out[-1]["end"] if out else 0.0
        sig_ini = tramos[k + 1]["start"] if k + 1 < len(tramos) else t["end"] + aire
        s = punto_mas_silencioso(db, max(prev_fin, t["start"] - 0.04), t["start"] + 0.02)
        e = punto_mas_silencioso(db, t["end"] - 0.02, min(sig_ini, t["end"] + 0.04))
        s, e = a_rejilla(max(prev_fin, s)), a_rejilla(e)
        if out and s < out[-1]["end"]:
            s = out[-1]["end"]
        if e - s >= 2 / 30:
            out.append({"start": s, "end": e})
    return out


def corregir(w, correcciones):
    """Aplica {"mal": "bien"} sin importar mayúsculas ni la puntuación pegada («moletillas.»)."""
    if not correcciones:
        return w
    nucleo = w.rstrip(".,;:!?¿¡…")
    cola = w[len(nucleo):]
    bajas = {k.lower(): v for k, v in correcciones.items()}
    nuevo = correcciones.get(nucleo) or bajas.get(nucleo.lower())
    if not nuevo:
        return w
    if nucleo[:1].isupper() and nuevo[:1].islower():
        nuevo = nuevo[:1].upper() + nuevo[1:]
    return nuevo + cola


def verificar_con_audio(tr, esperadas, correcciones):
    """Vuelve a transcribir el audio ya cortado: da tiempos exactos para los subtítulos y dice
    qué palabras faltan de verdad (Whisper a veces fecha mal la última palabra de una frase y
    parecía perdida sin estarlo). Devuelve (palabras, perdidas, nuevas) o None si no hay Whisper."""
    import difflib

    try:
        from transcribir import transcribir
    except Exception:
        return None
    vocab_f = tr / "vocab.txt"
    vocab = vocab_f.read_text(encoding="utf-8") if vocab_f.exists() else ""
    aviso("Compruebo el corte escuchándolo otra vez…")
    try:
        oidas = transcribir(str(tr / "voz_cortada.wav"), vocab=vocab)
    except Exception as e:
        aviso(f"No pude volver a transcribir ({e}); uso los tiempos calculados.")
        return None
    a = [normalizar_palabra(p["w"]) for p in esperadas]
    b = [normalizar_palabra(p["w"]) for p in oidas]
    perdidas, nuevas = [], []
    def texto_revisado(i, j):
        # palabra de la transcripción revisada (tildes, «el» y no «la») con la puntuación
        # y mayúscula de la nueva escucha, que conoce dónde acaba cada frase en el corte
        nueva = oidas[j]["w"]
        nucleo_n = nueva.rstrip(".,;:!?…")
        nucleo_e = esperadas[i]["w"].strip(".,;:!?¿¡…")
        if nucleo_n[:1].isupper():
            nucleo_e = nucleo_e[:1].upper() + nucleo_e[1:]
        return nucleo_e + nueva[len(nucleo_n):]

    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            for i, j in zip(range(i1, i2), range(j1, j2)):
                oidas[j]["w"] = texto_revisado(i, j)
        else:
            if op in ("delete", "replace"):
                perdidas += esperadas[i1:i2]
            if op in ("insert", "replace"):
                nuevas += oidas[j1:j2]
    for p in oidas:
        p["w"] = corregir(p["w"], correcciones)
    return oidas, perdidas, nuevas


def recalcular(palabras, tramos, correcciones):
    nuevas, perdidas, offset, mapa = [], [], 0.0, []
    for t in tramos:
        mapa.append((t["start"], t["end"], offset))
        offset += t["end"] - t["start"]
    for p in palabras:
        if p.get("quitar"):
            continue
        dur = max(p["end"] - p["start"], 0.01)
        mejor, solape = None, 0.0
        for s, e, off in mapa:
            o = min(e, p["end"]) - max(s, p["start"])
            if o > solape:
                mejor, solape = (s, e, off), o
        if mejor and solape >= min(0.15, 0.5 * dur):
            s, e, off = mejor
            w = corregir(p["w"], correcciones)
            nuevas.append({"w": w, "start": round(off + max(p["start"], s) - s, 3),
                           "end": round(off + min(p["end"], e) - s, 3), "p": p.get("p", 1)})
        else:
            perdidas.append(p)
    return nuevas, perdidas, offset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trabajo", required=True)
    ap.add_argument("--keep", required=True)
    ap.add_argument("--correcciones")
    ap.add_argument("--palabras")
    ap.add_argument("--aire", type=float, default=0.08)
    ap.add_argument("--sin-verificar", action="store_true",
                    help="no vuelve a transcribir el corte (más rápido, tiempos menos exactos)")
    a = ap.parse_args()

    tr = Path(a.trabajo)
    keep = leer_json(a.keep)
    if isinstance(keep, dict):
        keep = keep["tramos"]
    corr = leer_json(a.correcciones) if a.correcciones and Path(a.correcciones).exists() else {}
    ruta_pal = Path(a.palabras) if a.palabras else (tr / "propuesta.json" if (tr / "propuesta.json").exists() else tr / "palabras-bruto.json")
    palabras = leer_json(ruta_pal)
    if isinstance(palabras, dict):
        palabras = palabras["palabras"]

    db = energia_db(leer_mono(tr / "audio48k.wav"))
    tramos = ajustar(keep, db, a.aire)
    escribir_json(tr / "cortes.json", tramos)

    # filtro: trim/atrim + fundidos de 12 ms + concat
    partes, etiquetas = [], []
    for i, t in enumerate(tramos):
        d = t["end"] - t["start"]
        partes.append(f"[0:v]trim=start={t['start']}:end={t['end']},setpts=PTS-STARTPTS[v{i}];")
        partes.append(f"[1:a]atrim=start={t['start']}:end={t['end']},asetpts=PTS-STARTPTS,"
                      f"afade=t=in:d={AUDIO_FADE},afade=t=out:st={max(0, d - AUDIO_FADE):.4f}:d={AUDIO_FADE}[a{i}];")
        etiquetas.append(f"[v{i}][a{i}]")
    partes.append(f"{''.join(etiquetas)}concat=n={len(tramos)}:v=1:a=1[v][a]")
    script = tr / "filtro_corte.txt"
    script.write_text("".join(partes), encoding="utf-8")

    aviso(f"Cortando {len(tramos)} tramos…")
    ffmpeg(["-i", str(tr / "vertical.mp4"), "-i", str(tr / "audio48k.wav"), *filtro_desde_archivo(script),
            "-map", "[v]", "-map", "[a]", *codificador(), "-c:a", "pcm_s24le", "-f", "matroska", str(tr / "cortado.mkv")])
    ffmpeg(["-i", str(tr / "cortado.mkv"), "-map", "0:a", "-c:a", "pcm_s24le", str(tr / "voz_cortada.wav")])
    ffmpeg(["-i", str(tr / "cortado.mkv"), "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
            str(tr / "cortado.mp4")])
    ffmpeg(["-i", str(tr / "cortado.mp4"), "-vf", "scale=540:-2", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "28", "-c:a", "aac", "-b:a", "96k", str(tr / "preview.mp4")])
    (tr / "cortado.mkv").unlink(missing_ok=True)

    nuevas, perdidas, dur = recalcular(palabras, tramos, corr)
    esperadas = [p for p in palabras if not p.get("quitar")]
    verif = None if a.sin_verificar else verificar_con_audio(tr, esperadas, corr)
    if verif:
        oidas, perdidas, extra = verif
        escribir_json(tr / "palabras.json", oidas)
        aviso(f"Duración final: {dur:.1f} s. Palabras en el corte: {len(oidas)} "
              f"(esperadas {len(esperadas)}). palabras.json sale del audio cortado.")
        if extra:
            aviso("ℹ️ Se oyen palabras que no estaban en la propuesta (revisa si son restos de una toma falsa): "
                  + ", ".join(f"«{p['w']}» en {p['start']:.2f}s del corte" for p in extra))
    else:
        escribir_json(tr / "palabras.json", nuevas)
        aviso(f"Duración final: {dur:.1f} s. Palabras: {len(nuevas)} de {len(esperadas)} que debían quedarse.")
    if perdidas:
        aviso("⚠️ Estas palabras no se oyen en el corte. Si no las quitaste a propósito, amplía su tramo en keep.json y repite:")
        for p in perdidas:
            aviso(f"   «{p['w']}» en {p['start']:.2f}s del original")
    else:
        aviso("✅ No se ha perdido ninguna palabra.")

if __name__ == "__main__":
    main()
