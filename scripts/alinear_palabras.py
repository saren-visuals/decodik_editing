# -*- coding: utf-8 -*-
"""Ajusta los tiempos de palabras.json a la voz real del audio.

  python alinear_palabras.py --palabras 06_trabajo/palabras.json --audio 06_trabajo/cortado.mp4 [--dtw whisper_dtw.json]

Con --dtw (salida de whisper.cpp con «-dtw large.v3.turbo -nfa -ojf») rehace
palabras.json con ese texto y esos tiempos, que mantienen mejor el ritmo dentro
de una frase; sin él, usa los tiempos que ya tenga palabras.json.

Whisper acierta el texto pero puede adelantar o retrasar una palabra hasta
0,6 s, y el subtítulo sale antes o después de que se diga. Este paso:
1. mide en el audio los tramos con voz (entre pausas de ≥ 0,12 s);
2. asigna cada palabra, en orden, al tramo más cercano a su tiempo de whisper
   (programación dinámica: nunca desordena y no deja tramos de voz sin palabra);
3. pega la primera palabra de cada tramo al arranque de la voz y coloca las
   demás con el tiempo de whisper (corregido su retraso fijo) dentro del tramo.
Guarda una copia del original como palabras.whisper.json (solo la primera vez).
"""
import argparse, json, re, shutil, subprocess
from pathlib import Path

import numpy as np

PASO = 0.01


def tramos_de_voz(audio):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    hop, win = 160, 400
    n = max(1, (len(a) - win) // hop)
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    db = 20 * np.log10(np.sqrt((a[idx] ** 2).mean(axis=1)) + 1e-6)
    ruido = np.percentile(db, 20)
    voz = db > max(ruido + 12, db.max() - 45)
    # cierra huecos cortos (oclusivas, «p», «t») y quita chasquidos
    tramos, i = [], 0
    while i < len(voz):
        if voz[i]:
            j = i
            while j < len(voz) and voz[j]:
                j += 1
            tramos.append([i * PASO, j * PASO])
            i = j
        else:
            i += 1
    unidos = []
    for t in tramos:
        if unidos and t[0] - unidos[-1][1] < 0.12:
            unidos[-1][1] = t[1]
        else:
            unidos.append(t)
    return [t for t in unidos if t[1] - t[0] >= 0.08]


def silabas(w):
    w = re.sub(r"[^a-záéíóúüñ0-9]", "", w.lower())
    if w.isdigit():
        return 2 * len(w)
    return max(1, len(re.findall(r"[aeiouáéíóúü]+", w)))


def alinear(pal, tramos):
    N, M = len(pal), len(tramos)
    centro = [p["start"] + 0.08 for p in pal]
    largo = [t[1] - t[0] for t in tramos]

    def coste(i, j):
        s, e = tramos[j]
        c = centro[i]
        return 0.0 if s <= c <= e else min(abs(c - s), abs(c - e))

    # penalización por saltarse tramos de voz (voz sin subtítulo)
    pen = np.concatenate([[0], np.cumsum([0.6 * l for l in largo])])
    INF = 1e9
    dp = np.full((N, M), INF)
    de = np.zeros((N, M), int)
    for j in range(M):
        dp[0, j] = coste(0, j) + pen[j]
    for i in range(1, N):
        # la palabra i va en el mismo tramo que la anterior (j) o en uno posterior,
        # pagando los tramos de voz que queden sin palabra entre medias
        mejor, arg = INF, 0  # min sobre j' < j de dp[i-1, j'] - pen[j'+1]
        for j in range(M):
            mismo = dp[i - 1, j]
            salto = mejor + pen[j]
            if mismo <= salto:
                dp[i, j], de[i, j] = mismo + coste(i, j), j
            else:
                dp[i, j], de[i, j] = salto + coste(i, j), arg
            cand = dp[i - 1, j] - pen[j + 1]
            if cand < mejor:
                mejor, arg = cand, j
    j = int(np.argmin(dp[N - 1] + (pen[M] - pen[np.arange(M) + 1])))
    asign = [0] * N
    for i in range(N - 1, -1, -1):
        asign[i] = j
        j = de[i, j]
    # coloca las palabras dentro de su tramo
    out = [dict(p) for p in pal]
    i = 0
    while i < N:
        k = i
        while k + 1 < N and asign[k + 1] == asign[i]:
            k += 1
        s, e = tramos[asign[i]]
        n = k - i + 1
        est = [pal[x]["start"] for x in range(i, k + 1)]
        # escala los tiempos de whisper al tramo (primera palabra = arranque de la voz)
        sil = [silabas(pal[x]["w"]) for x in range(i, k + 1)]
        fin_est = est[-1] + 0.12 * sil[-1] + 0.1
        a, b = est[0], max(fin_est, est[0] + 0.1)
        ts = [s + (t - a) * (e - s) / (b - a) for t in est]
        for q in range(1, n):  # nunca dos palabras a menos de 60 ms
            ts[q] = min(max(ts[q], ts[q - 1] + 0.06), e - 0.06 * (n - q))
        for q, x in enumerate(range(i, k + 1)):
            out[x]["start"] = round(ts[q], 3)
            out[x]["end"] = round(ts[q + 1] if q + 1 < n else e, 3)
        i = k + 1
    return out, asign


def desde_dtw(ruta):
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    pal = []
    for seg in d["transcription"]:
        for tk in seg["tokens"]:
            t = tk["text"]
            if t.startswith("[_"):
                continue
            ini = tk["t_dtw"] / 100 if tk.get("t_dtw", -1) >= 0 else tk["offsets"]["from"] / 1000
            if t.startswith(" ") or not pal:
                pal.append({"w": t.strip(), "start": ini, "end": ini, "p": tk.get("p", 0.9)})
            else:
                pal[-1]["w"] += t
    pal = [p for p in pal if re.sub(r"[^\w]", "", p["w"])]
    for i, p in enumerate(pal):
        p["end"] = pal[i + 1]["start"] if i + 1 < len(pal) else p["start"] + 0.4
    return pal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--palabras", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--dtw")
    a = ap.parse_args()
    ruta = Path(a.palabras)
    copia = ruta.with_name(ruta.stem + ".whisper.json")
    if a.dtw:
        pal = desde_dtw(a.dtw)
        copia.write_text(json.dumps(pal, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        if not copia.exists():
            shutil.copyfile(ruta, copia)
        pal = json.loads(copia.read_text(encoding="utf-8"))  # siempre desde el original de whisper
    tramos = tramos_de_voz(a.audio)
    # retraso fijo de whisper: el que mejor encaja los arranques con la voz
    import copy
    mejor = None
    for b in np.arange(-0.3, 0.61, 0.02):
        prueba = [{**p, "start": p["start"] - b, "end": p["end"] - b} for p in pal]
        _, asg = alinear(prueba, tramos)
        err = sum(abs(prueba[i]["start"] - tramos[asg[i]][0]) for i in range(len(pal)) if i == 0 or asg[i] != asg[i - 1])
        if mejor is None or err < mejor[0]:
            mejor = (err, b)
    b = mejor[1]
    print(f"retraso de whisper corregido: {b:+.2f} s")
    pal = [{**p, "start": p["start"] - b, "end": p["end"] - b} for p in pal]
    out, asign = alinear(pal, tramos)
    usados = len(set(asign))
    movidas = [(o["w"], p["start"], o["start"]) for p, o in zip(pal, out) if abs(o["start"] - p["start"]) > 0.25]
    ruta.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(pal)} palabras en {usados} de {len(tramos)} tramos de voz · {len(movidas)} movidas más de 0,25 s")
    for w, t0, t1 in movidas:
        print(f"  {w:<16}{t0:6.2f} → {t1:6.2f}")
    if usados < len(tramos):
        print(f"  [aviso] {len(tramos) - usados} tramos de voz sin palabra (respiraciones o ruido; si es habla, falta texto)")


if __name__ == "__main__":
    main()
