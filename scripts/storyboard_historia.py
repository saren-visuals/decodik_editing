"""Formato «Mi historia · B-roll encima con subtítulos» · storyboard visual para aprobar antes de montar.

Uso:
  python storyboard_historia.py --trabajo 06_trabajo [--storyboard storyboard-historia.json] [--fuente "Helvetica Now Display"]
Lee el storyboard (lista de planos que se suceden: cámara, B-roll de vídeo o foto), cortado.mp4 y palabras.json.
Genera 06_trabajo/storyboard-historia.html: barra de tiempo por tipo de plano y una tarjeta por plano con su fotograma
real compuesto como saldrá (B-roll a pantalla completa, en recuadro sobre su propio fondo desenfocado, o foto) y
un ejemplo del subtítulo con la fuente elegida.
Comprueba: que ningún cambio de plano cae dentro de una palabra, que cada clip dura lo que tiene que cubrir,
y que ningún plano de B-roll dura menos de 0,8 s.

storyboard-historia.json:
{"titulo": "...", "fuente": "Helvetica Now Display",
 "planos": [{"t0": 0.0, "tipo": "camara|broll|foto", "src": "03_recursos/...", "in": 0.5,
             "modo": "completo|recuadro|foto", "nota": "qué se ve y por qué"}]}
Cada plano dura hasta el t0 del siguiente; el último, hasta el final del vídeo.
"""
import argparse
import html
import json
import subprocess
from pathlib import Path

from comun import aviso, error, herramienta, leer_json, sondear
from tramos import resolver

E = html.escape
ANCHO = 200


def miniatura(src, t, out, modo):
    """Fotograma compuesto en 9:16 como saldrá en el vídeo."""
    ff = herramienta("ffmpeg")
    entrada = ["-ss", f"{t:.2f}", "-i", str(src)] if t is not None else ["-i", str(src)]
    if modo == "recuadro":
        filtro = ("[0:v]split[a][b];[a]scale=360:640:force_original_aspect_ratio=increase,crop=360:640,"
                  "gblur=sigma=18,eq=brightness=-0.12[f];[b]scale=360:-2[r];[f][r]overlay=0:H*0.22")   # recuadro arriba: el subtítulo va debajo, sobre el fondo
    else:
        filtro = "[0:v]scale=360:640:force_original_aspect_ratio=increase,crop=360:640"
    subprocess.run([ff, "-v", "error", "-y", *entrada, "-frames:v", "1", "-filter_complex", filtro, "-q:v", "4", str(out)],
                   check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trabajo", required=True)
    ap.add_argument("--storyboard", default="storyboard-historia.json")
    ap.add_argument("--fuente")
    ap.add_argument("--ajustar", action="store_true",
                    help="mueve cada cambio que cae dentro de una palabra al borde más cercano y guarda el storyboard")
    a = ap.parse_args()
    tr = Path(a.trabajo)
    proyecto = tr.parent
    sb = leer_json(tr / a.storyboard)
    video = tr / "cortado.mp4"
    if not video.exists():
        error("Falta cortado.mp4")
    dur = sondear(video)["duracion"]
    palabras = leer_json(tr / "palabras.json")
    fuente = a.fuente or sb.get("fuente", "Helvetica Now Display")
    planos = sb["planos"]
    if a.ajustar:
        movidos = 0
        for k, p in enumerate(planos[1:], 2):
            for i, w in enumerate(palabras):
                if w["start"] + 0.04 < p["t0"] < w["end"] - 0.04:
                    # si ya se ha dicho más de la mitad de la palabra, el plano empieza en la siguiente
                    nuevo = w["start"] if p["t0"] - w["start"] < (w["end"] - w["start"]) / 2 else                         (palabras[i + 1]["start"] if i + 1 < len(palabras) else w["end"])
                    aviso(f"plano {k}: {p['t0']:.2f} → {nuevo:.2f} s («{w['w']}»)")
                    p["t0"] = round(nuevo - 0.02, 3)
                    movidos += 1
                    break
        (tr / a.storyboard).write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")
        aviso(f"{movidos} cambios ajustados a los bordes de palabra y guardados en {a.storyboard}")
    resolver(planos, proyecto, dur)
    for k, p in enumerate(planos):
        p["t1"] = planos[k + 1]["t0"] if k + 1 < len(planos) else dur

    avisos = []
    dirm = tr / "storyboard-h"
    dirm.mkdir(exist_ok=True)
    tarjetas, barra = [], []
    for k, p in enumerate(planos, 1):
        t0, t1 = p["t0"], p["t1"]
        voz = " ".join(w["w"] for w in palabras if w["start"] >= t0 - 0.05 and w["start"] < t1 - 0.05)
        # ¿el cambio cae dentro de una palabra?
        for w in palabras:
            if w["start"] + 0.08 < t0 < w["end"] - 0.08 and k > 1:
                avisos.append(f"plano {k}: el cambio en {t0:.2f} s cae dentro de «{w['w']}» ({w['start']:.2f}-{w['end']:.2f})")
        img = dirm / f"p{k:02d}.jpg"
        if p["tipo"] == "camara":
            miniatura(video, (t0 + t1) / 2, img, "completo")
        else:
            src = proyecto / p["src"]
            if not src.exists():
                avisos.append(f"plano {k}: no existe {p['src']}")
                continue
            if p["tipo"] == "broll":
                info = sondear(src)
                falta = (t1 - t0) - (info["duracion"] - p["in_usado"])
                if falta > 0.05:
                    avisos.append(f"plano {k}: el clip se acaba {falta:.1f} s antes que el plano (baja «in» o acorta el plano)")
                if t1 - t0 < 0.8:
                    avisos.append(f"plano {k}: {t1 - t0:.1f} s de B-roll es demasiado corto (mínimo 0,8 s)")
                miniatura(src, p["in_usado"] + (t1 - t0) / 2, img, p["modo_usado"])
            else:
                miniatura(src, None, img, p["modo_usado"])
        color = {"camara": "#3a3f4a", "broll": "#FFE600", "foto": "#f0a63a"}[p["tipo"]]
        barra.append(f'<div class="seg" style="flex:{t1 - t0:.2f};background:{color}" title="{k}"></div>')
        muestra = " ".join(voz.split()[:3]).rstrip(".,;:?¿!¡").lower()
        etiqueta = {"camara": "A CÁMARA", "broll": "B-ROLL · " + p.get("modo_usado", "completo").upper(), "foto": "FOTO" + (" · RECUADRO" if p.get("modo_usado") == "recuadro" else "")}[p["tipo"]]
        tarjetas.append(f'''<article class="esc"><div class="pant"><img src="storyboard-h/p{k:02d}.jpg">
          <div class="sub">{E(muestra)}</div></div>
          <div class="info"><div class="cab"><span class="num">{k:02d}</span><span class="tipo t-{p["tipo"]}">{etiqueta}</span>
          <span class="tiempo">{t0:.1f}–{t1:.1f} s · {t1 - t0:.1f} s</span></div>
          <p class="nota">{E(p.get("nota", ""))}</p><p class="voz">«{E(voz)}»</p>
          {f'<p class="src">{E(Path(p["src"]).name)} · {("tramo " + format(p["in_usado"], ".1f") + "–" + format(p["in_usado"] + t1 - t0, ".1f") + " s" + (" (el más activo)" if p.get("in", "auto") == "auto" else "")) if "in_usado" in p else "foto"}</p>' if p.get("src") else ""}</div></article>''')

    n_b = sum(1 for p in planos if p["tipo"] != "camara")
    t_b = sum(p["t1"] - p["t0"] for p in planos if p["tipo"] != "camara")
    for x in avisos:
        aviso("⚠️ " + x)
    pagina = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Storyboard Mi historia</title><style>
@font-face{{font-family:"Sub";src:local("{E(fuente)} ExtraBold"),local("{E(fuente)}");font-weight:800}}
:root{{--bg:#0e0f12;--card:#16181d;--txt:#f2f2f2;--sub:#9aa0aa;--am:#FFE600;--linea:#262932}}
body{{margin:0;background:var(--bg);color:var(--txt);font-family:"{E(fuente)}",system-ui,sans-serif}}
header{{padding:28px 16px 8px;max-width:1100px;margin:auto}} h1{{margin:0;font-size:34px;font-weight:800}} h1 span{{color:var(--am)}}
.meta{{color:var(--sub);margin:6px 0 12px}} .barra{{display:flex;height:14px;border-radius:7px;overflow:hidden;gap:2px}}
.ley{{color:var(--sub);font-size:13px;margin-top:6px}} .ley i{{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 4px 0 10px}}
.avisos{{color:#ff8a8f;font-size:14px}}
main{{max-width:1100px;margin:auto;padding:12px 16px 60px;display:grid;gap:12px}}
.esc{{display:grid;grid-template-columns:{ANCHO}px 1fr;gap:16px;background:var(--card);border:1px solid var(--linea);border-radius:14px;padding:12px}}
.pant{{position:relative;width:{ANCHO}px;aspect-ratio:9/16;border-radius:10px;overflow:hidden;background:#000}} .pant img{{width:100%;height:100%;object-fit:cover;display:block}}
.sub{{position:absolute;left:0;right:0;top:58%;text-align:center;font-family:"Sub","{E(fuente)}",sans-serif;font-weight:800;font-size:15px;color:#fff;
      text-shadow:0 1px 4px rgba(0,0,0,.7)}}
.cab{{display:flex;flex-wrap:wrap;align-items:center;gap:8px}} .num{{font-size:24px;font-weight:800;color:var(--sub)}}
.tipo{{font-size:11px;font-weight:800;border-radius:20px;padding:3px 9px}} .t-camara{{background:#3a3f4a}} .t-broll{{background:var(--am);color:#111}} .t-foto{{background:#f0a63a;color:#111}}
.tiempo{{margin-left:auto;color:var(--sub)}} .nota{{font-size:16px;font-weight:700;margin:8px 0 4px}} .voz{{font-size:14px;color:#cfd2d8;margin:0}} .src{{font-size:12px;color:var(--sub)}}
@media (max-width:640px){{.esc{{grid-template-columns:1fr}} .pant{{margin:auto}}}}
</style></head><body>
<header><h1>STORYBOARD · <span>{E(sb.get("titulo", "").upper())}</span></h1>
<div class="meta">{E(sb.get("formato", "Mi historia"))} · {dur:.0f} s · {len(planos)} planos · {n_b} de B-roll o foto ({t_b / dur * 100:.0f} % del vídeo) · subtítulos en {E(fuente)}</div>
<div class="barra">{"".join(barra)}</div>
<div class="ley"><i style="background:#FFE600"></i>B-roll de vídeo<i style="background:#f0a63a"></i>foto<i style="background:#3a3f4a"></i>a cámara</div>
{"<p class='avisos'>⚠️ " + "<br>⚠️ ".join(E(x) for x in avisos) + "</p>" if avisos else ""}
</header><main>{"".join(tarjetas)}</main></body></html>"""
    (tr / "storyboard-historia.html").write_text(pagina, encoding="utf-8")
    aviso(f"Storyboard: {tr / 'storyboard-historia.html'}  ({len(planos)} planos, {len(avisos)} avisos)")


if __name__ == "__main__":
    main()
