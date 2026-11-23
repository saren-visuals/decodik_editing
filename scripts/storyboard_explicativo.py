"""Formato «Explicativo con texto · pantalla dividida» · storyboard visual para aprobar antes de construir.

Uso:
  python storyboard_explicativo.py --trabajo 06_trabajo [--estilo <estilo.json>] [--aire 40]
Lee 06_trabajo/storyboard.json (formato en referencias/formato-explicativo-texto.md) y 06_trabajo/cortado.mp4.
Genera 06_trabajo/storyboard-explicativo.html (se abre sin internet), storyboard-explicativo.md y cabeza.json
(parte más alta de la cabeza en cada escena B, para encuadrar a la persona pegada a la costura).
"""
import argparse
import html
import shutil
import subprocess
from pathlib import Path

import numpy as np

from bocetos_motion import fondo_premium, panel_svg
from comun import aviso, error, escribir_json, herramienta, leer_json

SKILL = Path(__file__).resolve().parent.parent
E = html.escape
ANCHO = 220


def fotograma(video, t, out, filtro="scale=440:-1"):
    subprocess.run([herramienta("ffmpeg"), "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                    "-vf", filtro, "-q:v", "4", str(out)], check=True)


def cabeza(video, t0, t1):
    """Fila más alta con pelo oscuro sobre el fondo, en la banda central, en 5 instantes de la escena."""
    tops = []
    for t in np.linspace(t0 + 0.2, max(t0 + 0.3, t1 - 0.2), 5):
        r = subprocess.run([herramienta("ffmpeg"), "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                            "-vf", "scale=1080:1920", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
        if len(r.stdout) != 1080 * 1920:
            continue
        a = np.frombuffer(r.stdout, np.uint8).reshape(1920, 1080)[:, 250:830]
        filas = np.where((a < 60).sum(1) > 25)[0]
        if len(filas):
            tops.append(int(filas[0]))
    return min(tops) if tops else 300


def panel(s, fondo):
    ac = s.get("acento")
    if s.get("comparativa"):
        g = s.get("ganadora", len(s["comparativa"]) - 1)
        etiqueta = f'<small>{E(s.get("linea", ""))}</small>'
        fichas = "".join(f'<div class="ficha{" on" if k == g else ""}"><i>{k + 1:02d}</i><b>{E(x)}</b>{etiqueta if k == g else ""}</div>'
                         for k, x in enumerate(s["comparativa"]))
        return f'<div class="comp2">{fichas}</div>'
    hero = E(s.get("hero", ""))
    if ac == "ultima" and " " in s.get("hero", "") and not s.get("lineas"):
        a, b = s["hero"].rsplit(" ", 1)
        hero = f'{E(a)} <em>{E(b)}</em>'
    cls = {"negativo": "hero neg", "hero": "hero am"}.get(ac, "hero")
    extra = ""
    if s.get("producto"):
        extra += '<div class="bote"><span>producto</span></div>'
    if s.get("siluetas"):
        n = int(s["siluetas"])
        extra += '<div class="sil">' + "".join(f'<span class="{"on" if k == n * 2 // 3 else ""}"></span>' for k in range(n)) + "</div>"
    num = f'<div class="num-f">{E(s["n"].split()[1])}</div>' if s["n"].upper().startswith("FICHA") and len(s["n"].split()) > 1 else ""
    sub = '<div class="sub-l"></div>' if ac in ("subrayado", "trazo") else ""
    ls = s.get("lineas", [])
    lineas = "".join(f'<div class="ln{" am" if ac == "ultima" and k == len(ls) - 1 else ""}">{E(x)}</div>' for k, x in enumerate(ls))
    linea = f'<div class="linea">{E(s["linea"])}</div>' if s.get("linea") else ""
    return f'{extra}{num}{linea}<div class="{cls}">{hero}</div>{sub}{lineas}'



def cortes_salida(tr):
    """Instantes (en el vídeo cortado) en los que cambia de toma: final acumulado de cada tramo de cortes.json."""
    f = tr / "cortes.json"
    if not f.exists():
        return []
    tramos, out, acc = leer_json(f), [], 0.0
    for t in tramos[:-1]:
        acc += t["end"] - t["start"]
        out.append(round(acc, 3))
    return out


def pegar_a_cortes(escenas, cortes, tol=0.25):
    """Cada cambio de escena (A↔B o B↔B) tiene que caer en un corte de toma: si hay uno a menos de `tol` s,
    lo pega ahí; si no, devuelve un aviso (el encuadre cambiaría con la persona hablando, en mitad de la toma)."""
    avisos = []
    if not cortes:
        return avisos
    for i, s in enumerate(escenas):
        if i == 0:
            continue
        c = min(cortes, key=lambda x: abs(x - s["t0"]))
        if abs(c - s["t0"]) <= tol:
            s["t0"] = c
        else:
            avisos.append(f"escena {i + 1} ({s['n']}): el cambio en {s['t0']:.2f} s cae en mitad de una toma "
                          f"(corte más cercano en {c:.2f} s). Muévelo a un corte o une las escenas.")
    return avisos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trabajo", required=True)
    ap.add_argument("--estilo")
    ap.add_argument("--storyboard", default="storyboard.json", help="JSON dentro de --trabajo")
    ap.add_argument("--salida", default="storyboard-explicativo", help="nombre del .html y .md de salida")
    ap.add_argument("--aire", type=int, default=40, help="px (lienzo 1080x1920) entre la costura y el pelo")
    a = ap.parse_args()
    tr = Path(a.trabajo)
    sb = leer_json(tr / a.storyboard)
    video = tr / "cortado.mp4"
    if not video.exists():
        error("Falta cortado.mp4: haz antes el corte.")
    acento, negativo = "#FFE600", "#E50914"
    if a.estilo:
        e = leer_json(Path(a.estilo))
        acento = e.get("subtitulos", {}).get("clave_color", acento)
        negativo = e.get("graficos", {}).get("colores_por_dato", {}).get("negativo", negativo) if isinstance(e.get("graficos"), dict) else negativo
    img_dir = tr / "storyboard"; img_dir.mkdir(exist_ok=True)
    for f in ("Anton-Regular.ttf", "Figtree-Bold.ttf", "Figtree-Black.ttf"):
        shutil.copy2(SKILL / "fonts" / f, img_dir / f)
    S = ANCHO / 1080
    escenas = sb["escenas"]
    for x in pegar_a_cortes(escenas, cortes_salida(tr)):
        aviso("⚠️ " + x)
    cab, tarjetas = {}, []
    md = [f"# Storyboard · {sb.get('titulo', '')}", "Formato: **Explicativo con texto · pantalla dividida** · 1080×1920 · 30 fps", "",
          "| # | Tiempo | Voz | Comp. | Qué entra y en qué palabra | Sonido |", "|---|---|---|---|---|---|"]
    for i, s in enumerate(escenas, 1):
        mid = s["t0"] + min(1.4, (s["t1"] - s["t0"]) / 2)
        fotograma(video, mid, img_dir / f"e{i:02d}.jpg")
        img = f"storyboard/e{i:02d}.jpg"
        if s["comp"] == "B":
            cab[i] = cabeza(video, s["t0"], s["t1"])
            if s.get("keyframes"):
                arriba = (f'<div class="panel svg">{panel_svg(s["keyframes"][-1]["elementos"], acento, negativo, titulo=s["keyframes"][-1].get("titulo", s.get("kicker")))}</div>')
            else:
                arriba = (f'<div class="panel"><svg class="bgp" viewBox="0 0 1080 960" preserveAspectRatio="xMidYMid slice">'
                          f'{fondo_premium(acento, f"t{i}")}</svg>{panel(s, "")}</div>')
            pant = (f'<div class="pant">{arriba}'
                    f'<div class="talento" style="background-image:url({img});background-position:center {-(cab[i] - a.aire) * S:.1f}px"></div>'
                    f'<div class="costura"></div></div>')
        else:
            z = " zoom" if s.get("zoom") else ""
            cta = f'<div class="cta">COMENTA <em>«{E(s["cta"])}»</em></div>' if s.get("cta") else ""
            pant = f'<div class="pant"><div class="full{z}" style="background-image:url({img})"></div>{cta}</div>'
        pasos = "".join(f'<li><b>{t:.1f} s</b> · «{E(p)}» → {E(q)}</li>' for t, p, q in s.get("motion", [])) or \
            ("<li>A cámara, sin gráfico" + (" · plano más cerrado (zoom 1,12)" if s.get("zoom") else "") + "</li>")
        tira = ""
        if s.get("keyframes"):
            figs, avs = "", []
            for k in s["keyframes"]:
                svg, av = panel_svg(k["elementos"], acento, negativo, devolver_avisos=True, guia=True, titulo=k.get("titulo", s.get("kicker")))
                avs += [f'{k["t"]:.1f} s: {x}' for x in av]
                figs += f'<figure>{svg}<figcaption><b>{k["t"]:.1f} s</b> «{E(k.get("palabra", ""))}»</figcaption></figure>'
            tira = '<div class="tira">' + figs + "</div>"
            if avs:
                tira += '<p class="aviso">⚠️ ' + "<br>⚠️ ".join(E(x) for x in avs) + "</p>"
                for x in avs:
                    aviso(f"⚠️ Escena {i} ({s['n']}) · {x}")
        etiqueta = "PANTALLA DIVIDIDA" if s["comp"] == "B" else "A CÁMARA"
        tarjetas.append(f'''<article class="esc">{pant}<div class="info"><div class="cab"><span class="num">{i:02d}</span>
          <span class="nom">{E(s["n"])}</span><span class="comp c{s["comp"]}">{etiqueta}</span><span class="tiempo">{s["t0"]:.1f}–{s["t1"]:.1f} s</span></div>
          <p class="voz">«{E(s.get("voz", ""))}»</p><ul>{pasos}</ul>{tira}<p class="son">Sonido: {E(s.get("sonido", "—"))}</p></div></article>''')
        mot = "; ".join(f'en «{p}» ({t:.1f}) {q}' for t, p, q in s.get("motion", [])) or "— (a cámara)"
        md.append(f'| {i} · {s["n"]} | {s["t0"]:.1f}–{s["t1"]:.1f} | «{s.get("voz", "")}» | {s["comp"]} | {mot} | {s.get("sonido", "—")} |')

    # reglas del formato que el script puede comprobar
    seguidas, peor = 0, 0
    for s in escenas:
        seguidas = seguidas + 1 if s["comp"] == "B" else 0
        peor = max(peor, seguidas)
    if peor > 3:
        aviso(f"⚠️ Hay {peor} escenas B seguidas (máximo 3): mete una a cámara entre medias.")
    rojos = sum(1 for s in escenas if s.get("acento") == "negativo")
    if rojos > 1:
        aviso(f"⚠️ El color negativo aparece {rojos} veces (máximo 1).")

    nb = sum(1 for s in escenas if s["comp"] == "B")
    barra = "".join(f'<div class="seg {s["comp"]}" style="flex:{s["t1"] - s["t0"]:.2f}"></div>' for s in escenas)
    css = f"""
@font-face{{font-family:Anton;src:url(storyboard/Anton-Regular.ttf)}}
@font-face{{font-family:Figtree;font-weight:700;src:url(storyboard/Figtree-Bold.ttf)}}
@font-face{{font-family:Figtree;font-weight:900;src:url(storyboard/Figtree-Black.ttf)}}
:root{{--bg:#0e0f12;--card:#16181d;--txt:#f2f2f2;--sub:#9aa0aa;--am:{acento};--neg:{negativo};--linea:#262932}}
body{{margin:0;background:var(--bg);color:var(--txt);font-family:Figtree,system-ui,sans-serif}}
header{{padding:28px 16px 8px;max-width:1100px;margin:auto}} h1{{font-family:Anton;font-weight:400;font-size:38px;margin:0}} h1 span{{color:var(--am)}}
.meta{{color:var(--sub);margin:6px 0 12px}}
.ley{{color:var(--sub);font-size:13px;margin-top:8px}} .barra{{display:flex;height:14px;border-radius:7px;overflow:hidden;gap:2px}} .seg.A{{background:#3a3f4a}} .seg.B{{background:var(--am)}}
main{{max-width:1100px;margin:auto;padding:12px 16px 60px;display:grid;gap:14px}}
.esc{{display:grid;grid-template-columns:{ANCHO}px 1fr;gap:18px;background:var(--card);border:1px solid var(--linea);border-radius:16px;padding:14px}}
.pant{{width:{ANCHO}px;aspect-ratio:9/16;border-radius:12px;overflow:hidden;position:relative;background:#000}}
.full{{position:absolute;inset:0;background-size:cover;background-position:center}} .full.zoom{{background-size:112%}}
.panel{{position:absolute;left:0;right:0;top:0;height:50%;background-size:cover;background-position:center;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:10px;box-sizing:border-box;text-align:center}}
.panel>*{{position:relative}} .panel>.bgp{{position:absolute;inset:0;width:100%;height:100%}} .grano{{position:absolute!important;inset:0;opacity:.18;background-image:radial-gradient(rgba(255,255,255,.5) .5px,transparent .6px);background-size:3px 3px}}
.panel.svg{{padding:0;display:block}} .panel.svg svg{{width:100%;height:100%;display:block}}
.tira{{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}} .tira figure{{margin:0;width:150px}} .tira svg{{width:150px;border-radius:8px;display:block}}
.aviso{{color:#ff8a8f;font-size:13px;margin:8px 0 0}} .tira figcaption{{font-size:12px;color:var(--sub);margin-top:4px}} .tira b{{color:var(--am)}}
.talento{{position:absolute;left:0;right:0;bottom:0;height:50%;background-size:100% auto;background-repeat:no-repeat}}
.costura{{position:absolute;left:8%;right:8%;top:50%;height:1px;background:linear-gradient(90deg,transparent,var(--am),transparent)}}
.linea{{font-weight:700;font-size:7.5px;letter-spacing:1.6px;color:#d9dbe0}}
.hero{{font-family:Anton;font-size:30px;line-height:.95;color:#fff}} .hero em{{font-style:normal;color:var(--am)}} .hero.am{{color:var(--am);font-size:46px}} .hero.neg{{color:var(--neg);font-size:36px}}
.sub-l{{width:60%;height:2px;background:var(--am);border-radius:2px}}
.ln{{font-weight:700;font-size:7.5px;letter-spacing:1.2px;color:#e6e7ea;border-top:1px solid rgba(255,255,255,.15);padding-top:3px;width:70%}} .ln.am{{color:var(--am)}}
.num-f{{font-family:Anton;font-size:11px;color:var(--am)}}
.bote{{width:26px;height:38px;border-radius:5px;background:linear-gradient(100deg,#ddd,#fff 40%,#bbb);display:flex;align-items:center;justify-content:center;box-shadow:0 0 14px rgba(255,255,255,.25)}} .bote span{{font-size:5px;color:#333;font-weight:700}}
.sil{{display:flex;gap:3px}} .sil span{{width:9px;height:16px;border:1px solid rgba(255,255,255,.35);border-radius:2px}} .sil span.on{{border-color:var(--am);background:rgba(255,230,0,.25)}}
.comp2{{display:flex;gap:6px}} .ficha{{border:1px solid rgba(255,255,255,.25);border-radius:6px;padding:6px 5px;display:flex;flex-direction:column;gap:2px;min-width:70px;opacity:.6}}
.ficha.on{{border-color:var(--am);opacity:1}} .ficha i{{font-style:normal;font-family:Anton;font-size:9px;color:var(--am)}} .ficha b{{font-family:Anton;font-weight:400;font-size:11px}} .ficha small{{font-size:6px;letter-spacing:1px;font-weight:700;color:var(--am)}}
.cta{{position:absolute;left:0;right:0;top:57%;text-align:center;font-family:Anton;font-size:17px;color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.6)}} .cta em{{font-style:normal;color:var(--am)}}
.cab{{display:flex;flex-wrap:wrap;align-items:center;gap:8px}} .num{{font-family:Anton;font-size:26px;color:var(--sub)}} .nom{{font-family:Anton;font-size:24px}}
.comp{{font-size:11px;font-weight:900;border-radius:20px;padding:3px 9px}} .cB{{background:var(--am);color:#111}} .cA{{background:#3a3f4a;color:#ddd}}
.tiempo{{margin-left:auto;color:var(--sub)}} .voz{{font-size:15px;line-height:1.45;margin:8px 0}}
ul{{margin:0;padding-left:18px;color:#d6d8dd;font-size:14px;line-height:1.6}} ul b{{color:var(--am)}} .son{{color:var(--sub);font-size:13px;margin:8px 0 0}}
@media (max-width:640px){{.esc{{grid-template-columns:1fr}} .pant{{margin:auto}}}}"""
    pagina = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Storyboard explicativo</title><style>{css}</style></head><body>
<header><h1>STORYBOARD · <span>{E(sb.get("titulo", "").upper())}</span></h1>
<div class="meta">{E(sb.get("formato", "Explicativo con texto · pantalla dividida"))} · {len(escenas)} escenas · {nb} divididas · cabeza a {a.aire} px de la costura</div>
<div class="barra">{barra}</div><div class="ley">En las tiras, el recuadro azul discontinuo es la zona segura: nada sale de él y nada se pisa.</div></header><main>{"".join(tarjetas)}</main></body></html>"""
    (tr / f"{a.salida}.html").write_text(pagina, encoding="utf-8")
    (tr / f"{a.salida}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    escribir_json(tr / "cabeza.json", cab)
    aviso(f"Storyboard: {tr / (a.salida + '.html')}  ({len(escenas)} escenas, {nb} divididas)")


if __name__ == "__main__":
    main()
