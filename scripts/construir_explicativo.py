"""Construye en HyperFrames un vídeo de los formatos explicativos con pantalla dividida a partir del storyboard aprobado.

Uso:
  python construir_explicativo.py --trabajo 06_trabajo --storyboard storyboard-motion.json --estilo <estilo.json> [--aire 40]
Después:
  cd 06_trabajo/explicativo && npx hyperframes check . && npx hyperframes render . -o ../con_motion.mp4
  python mezclar.py --video 06_trabajo/con_motion.mp4 --voz 06_trabajo/voz_cortada.wav --out 07_entrega/<tema>.mp4

Qué hace:
- Escenas A: la persona a pantalla completa; con "zoom": true, plano más cerrado (1,12) centrado en la cara.
- Escenas B: arriba (0-960 px) los fotogramas clave del storyboard (fondo premium + motion), cada uno entra en su
  palabra con un fundido y desenfoque que se aclara; abajo la persona, desplazada para que el pelo quede a --aire px
  de la costura; si la escena tiene varias tomas, se mide la cabeza en cada una y el encuadre se ajusta en cada corte. Costura fina del color de acento.
- Los dibujos animados (SVG/SMIL de bocetos_motion y personajes_motion) se congelan y HyperFrames los coloca en el
  instante exacto de cada fotograma (protocolo hf-seek): el render es determinista y se mueve igual que el storyboard.
- CTA: «COMENTA / «PALABRA»» a la altura del pecho, dentro de la zona segura y sin tapar la cara.
- Cada cambio de escena se pega al corte de toma más cercano (≤ 0,25 s, de cortes.json); si no hay ninguno, avisa.
- Cortes secos entre escenas. Sin subtítulos. Sin efectos de sonido (los pone el usuario; ver sonido.md).
"""
import argparse
import html
import json
import shutil
from pathlib import Path

from bocetos_motion import panel_svg
from comun import aviso, error, leer_json, sondear
from storyboard_explicativo import cabeza, cortes_salida, pegar_a_cortes

SKILL = Path(__file__).resolve().parent.parent
E = html.escape
PANEL = 960


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trabajo", required=True)
    ap.add_argument("--storyboard", default="storyboard-motion.json")
    ap.add_argument("--estilo")
    ap.add_argument("--aire", type=int, default=40)
    a = ap.parse_args()
    tr = Path(a.trabajo)
    sb = leer_json(tr / a.storyboard)
    cab = {int(k): v for k, v in leer_json(tr / "cabeza.json").items()} if (tr / "cabeza.json").exists() else {}
    video = tr / "cortado.mp4"
    if not video.exists():
        error("Falta cortado.mp4")
    dur = round(sondear(video)["duracion"], 3)
    acento, negativo = "#FFE600", "#E50914"
    if a.estilo:
        e = leer_json(Path(a.estilo))
        acento = e.get("subtitulos", {}).get("clave_color", acento)
        g = e.get("graficos", {})
        if isinstance(g, dict):
            negativo = g.get("colores_por_dato", {}).get("negativo", negativo)

    out = tr / "explicativo"
    (out / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(video, out / "assets" / "base.mp4")
    shutil.copy2(SKILL / "plantillas" / "hyperframes" / "gsap.min.js", out / "assets" / "gsap.min.js")
    for f in ("Anton-Regular.ttf", "Figtree-Bold.ttf", "Figtree-Black.ttf"):
        shutil.copy2(SKILL / "fonts" / f, out / "assets" / "fonts" / f)

    paneles, js, avisos = [], [], []
    escenas = sb["escenas"]
    # los cambios de escena se pegan al corte de toma más cercano (≤ 0,25 s): nunca un doble salto
    cortes = cortes_salida(tr)
    for x in pegar_a_cortes(escenas, cortes):
        avisos.append(x)
    for i, s in enumerate(escenas, 1):
        t0, t1 = s["t0"], min(s["t1"], dur)
        # la escena dura hasta que empieza la siguiente (sin huecos negros)
        if i < len(escenas):
            t1 = escenas[i]["t0"]
        else:
            t1 = dur
        if s["comp"] == "B":
            # en cada toma de la escena se vuelve a medir la cabeza: el pelo siempre a --aire px de la costura
            bordes = [t0] + [c for c in cortes if t0 + 0.05 < c < t1 - 0.05] + [t1]
            for b0, b1 in zip(bordes, bordes[1:]):
                arriba_cabeza = cabeza(video, b0, b1) if len(bordes) > 2 else cab.get(i, cabeza(video, b0, b1))
                js.append(f'tl.set("#talento", {{ y: {PANEL + a.aire - arriba_cabeza}, scale: 1 }}, {b0:.3f});')
            js.append(f'tl.set("#abajo", {{ clipPath: "inset({PANEL}px 0px 0px 0px)" }}, {t0:.3f});')
            js.append(f'tl.set("#arriba", {{ opacity: 1 }}, {t0:.3f});')
            kfs = s.get("keyframes", [])
            for k, kf in enumerate(kfs):
                # Cambio de dibujo en dos tiempos, sobre el mismo fondo (es igual en todos los fotogramas):
                # 1) el contenido del dibujo anterior se desvanece (0,2 s); 2) entra el nuevo (0,45 s).
                # Así nunca se ven dos dibujos a la vez (regla: nada se solapa) ni el panel se queda a oscuras.
                ini = t0 if k == 0 else max(t0, kf["t"] - 0.15)
                fin = (max(t0, kfs[k + 1]["t"] - 0.15) + 0.2) if k + 1 < len(kfs) else t1
                svg, av = panel_svg(kf["elementos"], acento, negativo, devolver_avisos=True,
                                    titulo=kf.get("titulo", s.get("kicker")))
                avisos += [f"escena {i} · {kf['t']:.1f} s: {x}" for x in av]
                pid = f"p{i}_{k}"
                entra = ini if k == 0 else ini + 0.2
                paneles.append(f'<div class="kf" id="{pid}" data-ini="{entra:.3f}">{svg}</div>')
                js.append(f'tl.set("#{pid}", {{ opacity: 1 }}, {ini if k == 0 else entra:.3f});')
                if k == 0 and ini < 0.05:
                    desde = '{ opacity: 1, y: 14, filter: "blur(3px)" }'   # primer fotograma del vídeo: ya visible
                else:
                    desde = '{ opacity: 0, y: 26, filter: "blur(10px)" }'
                js.append(f'tl.fromTo("#{pid} .contenido", {desde}, '
                          f'{{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.45, ease: "power3.out" }}, {entra:.3f});')
                if k + 1 < len(kfs):
                    sale = max(t0, kfs[k + 1]["t"] - 0.15)
                    js.append(f'tl.to("#{pid} .contenido", {{ opacity: 0, y: -14, duration: 0.2, ease: "power2.in" }}, {sale:.3f});')
                js.append(f'tl.set("#{pid}", {{ opacity: 0 }}, {fin:.3f});')
        else:
            z = 1.12 if s.get("zoom") else 1.0
            js.append(f'tl.set("#talento", {{ y: 0, scale: {z} }}, {t0:.3f});')
            js.append(f'tl.set("#abajo", {{ clipPath: "inset(0px 0px 0px 0px)" }}, {t0:.3f});')
            js.append(f'tl.set("#arriba", {{ opacity: 0 }}, {t0:.3f});')
            if s.get("cta"):
                tc = next((m[0] for m in s.get("motion", []) if m[1].lower().startswith("coment")), t0)
                js.append(f'tl.fromTo("#cta", {{ opacity: 0, y: 30, filter: "blur(8px)" }}, '
                          f'{{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.5, ease: "power3.out" }}, {tc:.3f});')
    if avisos:
        for x in avisos:
            aviso("⚠️ " + x)

    cta = next((s.get("cta") for s in escenas if s.get("cta")), None)
    cta_html = (f'<div id="cta"><div class="c1">COMENTA</div><div class="c2">&quot;<span class="p">{E(cta)}</span>&quot;</div>'
                f'<div class="sub"></div></div>') if cta else ""
    index = f"""<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="assets/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Anton"; src: url("assets/fonts/Anton-Regular.ttf"); }}
      @font-face {{ font-family: "Figtree"; font-weight: 700; src: url("assets/fonts/Figtree-Bold.ttf"); }}
      @font-face {{ font-family: "Figtree"; font-weight: 900; src: url("assets/fonts/Figtree-Black.ttf"); }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #07080b; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #07080b; }}
      #abajo {{ position: absolute; inset: 0; overflow: hidden; }}
      #talento {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; transform-origin: 540px 640px; }}
      #base {{ width: 100%; height: 100%; object-fit: cover; }}
      #arriba {{ position: absolute; left: 0; top: 0; width: 1080px; height: {PANEL}px; overflow: hidden; opacity: 0; }}
      .kf {{ position: absolute; inset: 0; opacity: 0; }}
      .kf svg {{ width: 1080px; height: {PANEL}px; display: block; }}
      #costura {{ position: absolute; left: 0; right: 0; top: {PANEL - 1}px; height: 2px;
                 background: linear-gradient(90deg, transparent 6%, {acento} 50%, transparent 94%); }}
      #cta {{ position: absolute; left: 300px; width: 480px; top: 1010px; text-align: center; opacity: 0; padding: 26px 20px 30px;
             background: rgba(7,8,11,.72); border: 2px solid rgba(255,255,255,.08); border-radius: 30px;
             font-family: "Anton"; color: #fff; text-shadow: 0 4px 22px rgba(0,0,0,.55); }}
      #cta .c1 {{ font-size: 64px; line-height: 1; letter-spacing: 1px; }}
      #cta .c2 {{ font-size: 80px; line-height: 1.02; color: {acento}; white-space: nowrap; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="1080" data-height="1920">
      <div id="abajo"><div id="talento"><video id="base" class="clip" src="assets/base.mp4" playsinline data-has-audio="true"
        data-start="0" data-duration="{dur}" data-track-index="0"></video></div></div>
      <div id="arriba">
        {"".join(paneles)}
        <div id="costura"></div>
      </div>
      {cta_html}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      " + x for x in js)}
      tl.set({{}}, {{}}, {dur});
      window.__timelines["main"] = tl;
      // Dibujos SVG animados: congelados y colocados en el instante exacto de cada fotograma.
      const kfs = [...document.querySelectorAll(".kf")].map(d => [d.querySelector("svg"), parseFloat(d.dataset.ini)]);
      kfs.forEach(([s]) => s && s.pauseAnimations());
      function renderAt(t) {{ kfs.forEach(([s, ini]) => s && s.setCurrentTime(Math.max(0, t - ini))); }}
      window.addEventListener("hf-seek", (e) => renderAt(e.detail.time));
      renderAt(0);
    </script>
  </body>
</html>
"""
    (out / "index.html").write_text(index, encoding="utf-8")
    aviso(f"Proyecto listo: {out}  ({dur} s, {len(paneles)} fotogramas clave). Siguiente: npx hyperframes check y render.")


if __name__ == "__main__":
    main()
