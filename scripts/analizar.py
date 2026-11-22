"""Propone qué tramos se quedan: quita pausas largas, muletillas y repeticiones.

Uso:
  python analizar.py --palabras 06_trabajo/palabras-bruto.json --audio 06_trabajo/audio48k.wav
                     [--pausa-max 0.4] [--aire 0.08] --out 06_trabajo/propuesta.json
Escribe propuesta.json (tramos + palabras marcadas) y propuesta.md (informe legible).
Claude revisa la propuesta, añade lo que el script no ve y escribe keep.json.
"""
import argparse
from pathlib import Path

from audio import energia_db, leer_mono, umbral_silencio
from comun import a_rejilla, aviso, escribir_json, leer_json, normalizar_palabra

MULETILLAS = {"eh", "ehh", "ehm", "em", "emm", "mm", "mmm", "hmm", "ah", "ahh", "uh", "um", "uhm"}


def recortar_final_estirado(palabras, db, umbral, ventana=0.01):
    """Whisper alarga palabras sobre los silencios: recorta el final al último instante con voz."""
    for p in palabras:
        i0, i1 = int(p["start"] / ventana), int(p["end"] / ventana)
        if i1 - i0 < 30:  # palabras de menos de 0,3 s: se dejan
            continue
        con_voz = [i for i in range(i0, min(i1, len(db))) if db[i] > umbral]
        if con_voz:
            nuevo_fin = (con_voz[-1] + 1) * ventana + 0.04
            if nuevo_fin < p["end"] - 0.15:
                p["end_original"] = p["end"]
                p["end"] = round(nuevo_fin, 3)


def marcar(palabras):
    norm = [normalizar_palabra(p["w"]) for p in palabras]
    for i, p in enumerate(palabras):
        p["quitar"] = None
        if norm[i] in MULETILLAS:
            p["quitar"] = "muletilla"
    # palabra repetida pegada: «que que», «y y»
    for i in range(1, len(palabras)):
        if norm[i] and norm[i] == norm[i - 1] and palabras[i]["start"] - palabras[i - 1]["end"] < 1.0:
            palabras[i - 1]["quitar"] = palabras[i - 1]["quitar"] or "repetida"
    # n-gramas repetidos cerca (arranque en falso): se queda la última versión
    for n in (4, 3, 2):
        for i in range(len(palabras) - n):
            a = norm[i:i + n]
            if not all(a):
                continue
            for j in range(i + n, min(i + n + 12, len(palabras) - n + 1)):
                if norm[j:j + n] == a and palabras[j]["start"] - palabras[i]["start"] < 8:
                    # La coincidencia puede empezar a mitad de la frase repetida («truco está en»
                    # dentro de «el truco está en»). Retrocede mientras las dos versiones sigan
                    # coincidiendo, para no tachar el arranque de la toma buena («el»).
                    b = 0
                    while i - b - 1 >= 0 and j - b - 1 >= i + n and norm[i - b - 1] == norm[j - b - 1]:
                        b += 1
                    for k in range(i - b, j - b):
                        palabras[k]["quitar"] = palabras[k]["quitar"] or f"toma falsa ({n} palabras repetidas)"
                    break
    # restos sueltos entre dos tomas falsas («… directo vale ~y~ si quieres probar…»)
    i = 0
    while i < len(palabras):
        if palabras[i]["quitar"]:
            i += 1
            continue
        f = i
        while f < len(palabras) and not palabras[f]["quitar"]:
            f += 1
        if 0 < i and f < len(palabras) and f - i <= 2 \
                and "toma falsa" in str(palabras[i - 1]["quitar"]) and "toma falsa" in str(palabras[f]["quitar"]):
            for k in range(i, f):
                palabras[k]["quitar"] = "resto de toma falsa"
        i = f


def tramos(palabras, pausa_max, aire, duracion):
    quedan = [p for p in palabras if not p["quitar"]]
    if not quedan:
        return []
    out = []
    ini, fin = quedan[0]["start"], quedan[0]["end"]
    for p in quedan[1:]:
        if p["start"] - fin <= pausa_max and not _hay_quitada_entre(palabras, fin, p["start"]):
            fin = p["end"]
        else:
            out.append([ini, fin])
            ini, fin = p["start"], p["end"]
    out.append([ini, fin])
    res = []
    for s, e in out:
        s, e = max(0.0, s - aire), min(duracion, e + aire)
        if res and s <= res[-1]["end"]:
            res[-1]["end"] = a_rejilla(e)
        else:
            res.append({"start": a_rejilla(s), "end": a_rejilla(e)})
    return res


def partir_por_silencios(tramos, db, umbral, pausa_max, aire, ventana=0.01):
    """Whisper estira palabras por encima de las pausas («en» de 4 s, «subtítulos» con 1 s de
    silencio detrás), así que mirar solo las palabras deja pausas dentro de los tramos.
    Aquí se mira el audio: cualquier silencio de más de `pausa_max` dentro de un tramo se
    reduce a `aire` a cada lado, y se recortan los silencios del principio y del final."""
    salida = []
    for t in tramos:
        i0, i1 = int(t["start"] / ventana), min(len(db), int(t["end"] / ventana))
        seg = db[i0:i1]
        voz = seg > umbral
        # quita «voz» débil y corta (respiraciones, roces): picos que no pasan de umbral+8 dB
        k = 0
        while k < len(voz):
            if voz[k]:
                f = k
                while f < len(voz) and voz[f]:
                    f += 1
                if (f - k) * ventana < 0.25 and seg[k:f].max() < umbral + 8:
                    voz[k:f] = False
                k = f
            else:
                k += 1
        if not voz.any():
            continue
        # regiones con voz, uniendo huecos de hasta pausa_max
        regiones, k = [], 0
        hueco = int(round(pausa_max / ventana))
        while k < len(voz):
            if not voz[k]:
                k += 1
                continue
            ini = fin = k
            while fin < len(voz):
                if voz[fin]:
                    fin += 1
                    continue
                sig = fin
                while sig < len(voz) and not voz[sig]:
                    sig += 1
                if sig < len(voz) and sig - fin <= hueco:
                    fin = sig
                else:
                    break
            regiones.append((ini, fin))
            k = fin
        for a, b in regiones:
            if (b - a) * ventana < 0.05:  # chasquido suelto
                continue
            s = max(t["start"], t["start"] + a * ventana - aire)
            e = min(t["end"], t["start"] + b * ventana + aire)
            if salida and s - salida[-1]["end"] < 0.1:
                salida[-1]["end"] = a_rejilla(max(salida[-1]["end"], e))
            else:
                salida.append({"start": a_rejilla(s), "end": a_rejilla(e)})
    return salida


def _hay_quitada_entre(palabras, t0, t1):
    return any(p["quitar"] and p["start"] >= t0 - 0.01 and p["end"] <= t1 + 0.01 for p in palabras)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--palabras", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--pausa-max", type=float, default=0.4)
    ap.add_argument("--aire", type=float, default=0.08)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    palabras = leer_json(a.palabras)
    muestras = leer_mono(a.audio)
    duracion = len(muestras) / 16000
    db = energia_db(muestras)
    umbral = umbral_silencio(db)

    recortar_final_estirado(palabras, db, umbral)
    marcar(palabras)
    t = tramos(palabras, a.pausa_max, a.aire, duracion)
    t = partir_por_silencios(t, db, umbral, a.pausa_max, a.aire)
    queda = sum(x["end"] - x["start"] for x in t)

    escribir_json(a.out, {"duracion_original": round(duracion, 2), "duracion_propuesta": round(queda, 2),
                          "umbral_silencio_db": round(float(umbral), 1), "tramos": t, "palabras": palabras})

    lineas = [f"# Propuesta de corte\n", f"- Duración: {duracion:.1f} s → {queda:.1f} s ({len(t)} tramos)\n",
              "## Transcripción (~~tachado~~ = se quita)\n"]
    texto = []
    for p in palabras:
        w = p["w"] + ("⚠️" if p["p"] < 0.6 else "")
        texto.append(f"~~{w}~~" if p["quitar"] else w)
    lineas.append(" ".join(texto) + "\n")
    lineas.append("\n## Qué se quita y por qué\n")
    for p in palabras:
        if p["quitar"]:
            lineas.append(f"- {p['start']:.2f}s «{p['w']}» → {p['quitar']}")
    dudosas = [f"«{p['w']}» ({p['start']:.1f}s)" for p in palabras if p["p"] < 0.6]
    if dudosas:
        lineas.append("\n## Palabras dudosas (revisa la ortografía)\n- " + ", ".join(dudosas))
    md = Path(a.out).with_suffix(".md")
    md.write_text("\n".join(lineas), encoding="utf-8")
    aviso(f"Propuesta: {duracion:.1f} s → {queda:.1f} s. Informe en {md}")


if __name__ == "__main__":
    main()
