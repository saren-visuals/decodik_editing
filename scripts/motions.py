"""Motions explicativos del panel de arriba (pantalla dividida) para construir_composicion.py.

Regla: si el usuario tiene capturas o vídeos para ese momento, se ponen («src»). Si no, el panel
explica lo que se dice con una animación propia de este módulo, nunca con capturas de relleno.

Tipos (cada uno con "t" o "ancla" y "hasta"; textos cortos, en la voz del talento):
  {"src": "../03_recursos/captura.png", "t": 0, "hasta": 3}                     captura o vídeo real
  {"tipo": "cronometro", "valor": "5:00", "etiqueta": "sin editor"}             anillo que se llena
  {"tipo": "chat", "autor": "Claude", "texto": "Corta silencios · subtítulos"}  orden que se escribe sola
  {"tipo": "pasos", "items": [{"num": "01", "texto": "Graba sin miedo", "anim": "rec", "ancla": "Graba"}, ...]}
        anim: rec (punto de grabación) · onda (onda a la que se le quitan los huecos) · estilos (se elige uno)
  {"tipo": "barra", "de": 60, "a": 5, "unidad": "min", "antes": "antes", "despues": "ahora", "ancla_cambio": "ahora"}
  {"tipo": "flujo", "de": "Brief", "a": "Vídeo listo"}                          documento → vídeo terminado
  {"tipo": "comentario", "texto": "EDITA", "sub": "y te mando el skill", "ancla_sub": "mando"}

Todo va centrado en el panel (x 120-960, y 288-738 de un lienzo 1080×1920) y es determinista:
solo tweens de GSAP (nada de onUpdate ni temporizadores), para que HyperFrames pueda saltar a cualquier instante.
"""
import html
from pathlib import Path

NL = "\n"
ROJO_REC = "#FF4D4D"


def esc(t):
    return html.escape(str(t))


def css_panel(m, K, zona="dividida"):
    """zona: «dividida» = panel de arriba (0-768, contenido en y 288-738);
    «recuadro» = fondo a pantalla completa, contenido bajo el recuadro de la persona (y 800-1248, a tamaño real)."""
    px = lambda n: f"{round(n * K)}px"
    alto = "100%" if zona == "recuadro" else px(768)
    caja_top, caja_alto, escala = (800, 448, 1) if zona == "recuadro" else (288, 450, 1)
    return f"""
        .pfondo {{ position: absolute; left: 0; top: 0; width: 100%; height: {alto};
                  background: radial-gradient(rgba(197,234,234,.07) {px(1.6)}, transparent {px(1.6)}) 0 0 / {px(36)} {px(36)},
                              radial-gradient(120% 90% at 50% 0%, {m['petroleo']}, transparent 65%), {m['noche']}; }}
        .pitem {{ position: absolute; left: 0; top: 0; width: 100%; height: {alto}; overflow: hidden; }}
        .pitem .medio {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
        .pm {{ position: absolute; left: {px(120)}; right: {px(120)}; top: {px(caja_top)}; height: {px(caja_alto)};
               display: flex; align-items: center; justify-content: center; }}
        .pm-esc {{ transform: scale({escala}); transform-origin: 50% 50%; }}
        .vid {{ background: rgba(37,75,87,.55); border: {px(2)} solid rgba(197,234,234,.25); border-radius: {px(32)};
                box-shadow: 0 {px(8)} {px(24)} rgba(93,215,185,.22); }}
        .grad {{ background: linear-gradient(90deg, {m['menta']}, {m['cian']}); -webkit-background-clip: text; background-clip: text; color: transparent; }}
        .etq {{ font-family: "Figtree"; font-weight: 900; font-size: {px(28)}; letter-spacing: .12em; text-transform: uppercase; color: {m['menta']}; }}
        /* cronómetro */
        .crono {{ display: flex; flex-direction: column; align-items: center; gap: {px(18)}; }}
        .crono-anillo {{ position: relative; width: {px(330)}; height: {px(330)}; }}
        .crono-anillo svg {{ width: 100%; height: 100%; transform: rotate(-90deg); }}
        .crono-pista {{ fill: none; stroke: rgba(197,234,234,.14); stroke-width: 18; }}
        .crono-arco {{ fill: none; stroke: {m['menta']}; stroke-width: 18; stroke-linecap: round; stroke-dasharray: 879.6; stroke-dashoffset: 879.6;
                      filter: drop-shadow(0 0 {px(10)} rgba(93,215,185,.6)); }}
        .crono-v {{ position: absolute; inset: 0; display: grid; place-items: center; font-family: "Anton"; font-size: {px(120)}; }}
        .pild {{ padding: {px(10)} {px(26)}; border-radius: 999px; background: rgba(93,215,185,.16); border: {px(2)} solid rgba(93,215,185,.5); }}
        /* chat */
        .chat {{ width: {px(820)}; padding: {px(34)} {px(40)}; }}
        .chat-cab {{ display: flex; align-items: center; gap: {px(12)}; margin-bottom: {px(22)}; }}
        .punto {{ width: {px(16)}; height: {px(16)}; border-radius: 50%; background: {m['menta']}; box-shadow: 0 0 {px(12)} {m['menta']}; }}
        .chat-txt {{ font-family: "Figtree"; font-weight: 700; font-size: {px(50)}; line-height: 1.25; color: {m['crema']}; min-height: {px(130)}; }}
        .chat-txt .c {{ display: none; white-space: pre-wrap; }}
        .cursor {{ display: inline-block; width: {px(5)}; height: {px(54)}; background: {m['menta']}; vertical-align: {px(-8)}; margin-left: {px(4)}; }}
        .chat-pie {{ display: flex; justify-content: flex-end; margin-top: {px(18)}; }}
        .enviar {{ width: {px(78)}; height: {px(78)}; border-radius: 50%; display: grid; place-items: center; background: {m['menta']};
                  color: {m['noche']}; font-family: "Figtree"; font-weight: 900; font-size: {px(44)}; }}
        /* pasos */
        .pasos {{ display: flex; gap: {px(18)}; }}
        .paso {{ width: {px(262)}; height: {px(360)}; display: flex; flex-direction: column; align-items: center; justify-content: space-between;
                 padding: {px(26)} {px(14)}; }}
        .paso-n {{ font-family: "Anton"; font-size: {px(70)}; line-height: 1; }}
        .paso-a {{ height: {px(120)}; display: flex; align-items: center; justify-content: center; }}
        .paso-t {{ font-family: "Figtree"; font-weight: 800; font-size: {px(30)}; line-height: 1.15; text-align: center; color: {m['crema']}; }}
        .rec {{ display: flex; align-items: center; gap: {px(14)}; font-family: "Figtree"; font-weight: 900; font-size: {px(34)}; color: {m['crema']}; letter-spacing: .1em; }}
        .rec-p {{ width: {px(38)}; height: {px(38)}; border-radius: 50%; background: {ROJO_REC}; box-shadow: 0 0 {px(18)} {ROJO_REC}; }}
        .onda {{ display: flex; align-items: center; height: {px(100)}; }}
        .onda span {{ display: block; width: {px(10)}; margin: 0 {px(3)}; border-radius: {px(5)}; background: {m['menta']}; }}
        .onda .grupo {{ display: flex; align-items: center; height: 100%; }}
        .onda .h {{ display: block; background: rgba(197,234,234,.22); width: {px(30)}; height: {px(6)}; margin: 0 {px(3)}; border-radius: {px(3)}; }}
        .chips {{ display: flex; flex-direction: column; gap: {px(8)}; align-items: center; }}
        .chip {{ padding: {px(6)} {px(18)}; border-radius: 999px; font-family: "Figtree"; font-weight: 800; font-size: {px(28)};
                 border: {px(2)} solid rgba(197,234,234,.3); color: {m['humo']}; }}
        /* barra */
        .barra {{ display: flex; flex-direction: column; align-items: center; gap: {px(18)}; width: {px(780)}; }}
        .rodillo-fila {{ display: flex; align-items: flex-end; gap: {px(18)}; }}
        .rodillo {{ position: relative; width: {px(230)}; height: {px(200)}; }}
        .rodillo div {{ position: absolute; right: 0; bottom: 0; font-family: "Anton"; font-size: {px(200)}; line-height: 1; }}
        .rodillo-u {{ font-family: "Anton"; font-size: {px(84)}; color: {m['crema']}; padding-bottom: {px(14)}; }}
        .barra-pista {{ width: 100%; height: {px(34)}; border-radius: 999px; background: rgba(197,234,234,.14); overflow: hidden; }}
        .barra-rel {{ width: 100%; height: 100%; border-radius: 999px; background: linear-gradient(90deg, {m['menta']}, {m['cian']}); transform-origin: 0 50%; }}
        .barra-etq {{ position: relative; height: {px(40)}; width: 100%; }}
        .barra-etq .etq {{ position: absolute; left: 0; right: 0; text-align: center; }}
        /* flujo */
        .flujo {{ display: flex; align-items: center; gap: {px(26)}; }}
        .doc {{ width: {px(290)}; height: {px(340)}; padding: {px(28)}; display: flex; flex-direction: column; gap: {px(16)}; }}
        .doc i {{ display: block; height: {px(14)}; border-radius: {px(7)}; background: rgba(248,242,233,.35); }}
        .flecha-l {{ width: {px(120)}; height: {px(8)}; border-radius: {px(4)}; background: {m['menta']}; transform-origin: 0 50%; position: relative; }}
        .flecha-l::after {{ content: ""; position: absolute; right: {px(-14)}; top: {px(-12)}; border-left: {px(22)} solid {m['menta']};
                           border-top: {px(16)} solid transparent; border-bottom: {px(16)} solid transparent; }}
        .listo {{ width: {px(290)}; height: {px(340)}; padding: {px(24)}; display: flex; flex-direction: column; align-items: center; gap: {px(16)}; position: relative; }}
        .marco {{ width: {px(140)}; height: {px(200)}; border-radius: {px(18)}; border: {px(3)} solid rgba(197,234,234,.5);
                  background: linear-gradient(180deg, rgba(93,215,185,.25), rgba(126,222,227,.05)); }}
        .prog {{ width: {px(200)}; height: {px(14)}; border-radius: 999px; background: rgba(197,234,234,.14); overflow: hidden; }}
        .prog b {{ display: block; width: 100%; height: 100%; background: {m['menta']}; transform-origin: 0 50%; transform: scaleX(0); }}
        .ok {{ position: absolute; right: {px(-22)}; top: {px(-22)}; width: {px(76)}; height: {px(76)}; border-radius: 50%; background: {m['menta']};
               color: {m['noche']}; display: grid; place-items: center; font-family: "Figtree"; font-weight: 900; font-size: {px(44)};
               box-shadow: 0 0 {px(22)} rgba(93,215,185,.7); }}
        /* comentario */
        .coment {{ display: flex; flex-direction: column; align-items: center; gap: {px(22)}; }}
        .burbuja {{ width: {px(720)}; padding: {px(22)} {px(26)}; display: flex; align-items: center; gap: {px(22)}; border-radius: 999px; }}
        .avatar {{ width: {px(76)}; height: {px(76)}; border-radius: 50%; background: linear-gradient(135deg, {m['menta']}, {m['cian']}); flex: none; }}
        .campo {{ flex: 1; position: relative; height: {px(70)}; display: flex; align-items: center; font-family: "Figtree"; }}
        .ph {{ position: absolute; left: 0; font-weight: 600; font-size: {px(38)}; color: rgba(248,242,233,.4); }}
        .esc {{ font-weight: 900; font-size: {px(58)}; color: {m['crema']}; letter-spacing: .04em; }}
        .esc .c {{ display: none; }}
        .coment-sub {{ font-family: "Figtree"; font-weight: 700; font-size: {px(40)}; color: {m['crema']}; }}
"""


def _letras(texto, clase="c"):
    return "".join(f'<span class="{clase}">{esc(ch)}</span>' for ch in texto)


def _escribir(sel, n, t, paso=0.045):
    """Muestra n letras una a una desde t (deterministas: tl.set de display)."""
    return "".join(f'        ptl.set("{sel} .c:nth-child({k + 1})", {{ display: "inline" }}, {t + k * paso:.3f});\n' for k in range(n))


def panel_motion(items, anclas, copiar, dur, K=1.0):
    """Devuelve (html, js) de los elementos del panel. `copiar(src)` copia un recurso y da su ruta."""
    clips, js = [], ""
    for n, it in enumerate(items, 1):
        pid = f"pm{n}"
        t0 = anclas.t(it)
        t1 = float(it["hasta"])
        d = max(0.4, t1 - t0)
        entra = f'        ptl.fromTo("#{pid} .pm-in", {{ opacity: 0, y: 50, scale: .94, filter: "blur(14px)" }}, {{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.55, ease: "power3.out" }}, {t0:.3f});\n'
        sale = (f'        ptl.to("#{pid} .pm-in", {{ opacity: 0, y: -30, filter: "blur(10px)", duration: 0.22, ease: "power2.in" }}, {t1 - 0.22:.3f});\n'
                if t1 < dur - 0.05 else "")
        tipo = it.get("tipo")
        cuerpo = ""

        if "src" in it:  # captura o vídeo real del usuario: manda sobre cualquier motion
            src = copiar(it["src"])
            medio = (f'<video src="{src}" muted playsinline class="medio"></video>' if Path(src).suffix.lower() in (".mp4", ".mov", ".webm")
                     else f'<img src="{src}" alt="" class="medio" />')
            clips.append(f'        <div id="{pid}" class="pitem clip" data-start="{t0:.3f}" data-duration="{d:.3f}" data-track-index="1"><div class="pm-in" style="width:100%;height:100%">{medio}</div></div>')
            js += entra.replace("y: 50, scale: .94", "y: 0, scale: 1.04") + sale
            continue

        if tipo == "cronometro":
            llenar = min(2.2, d - 0.7)
            cuerpo = (f'<div class="crono"><div class="crono-anillo"><svg viewBox="0 0 320 320"><circle class="crono-pista" cx="160" cy="160" r="140"/>'
                      f'<circle class="crono-arco" cx="160" cy="160" r="140"/></svg><div class="crono-v grad">{esc(it.get("valor", "5:00"))}</div></div>'
                      f'<div class="pild etq">{esc(it.get("etiqueta", ""))}</div></div>')
            js += (f'        ptl.fromTo("#{pid} .crono-arco", {{ strokeDashoffset: 879.6 }}, {{ strokeDashoffset: 0, duration: {llenar:.2f}, ease: "power2.inOut" }}, {t0 + 0.3:.3f});\n'
                   f'        ptl.fromTo("#{pid} .crono-v", {{ scale: .6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.5, ease: "back.out(1.6)" }}, {t0 + 0.4:.3f});\n'
                   f'        ptl.fromTo("#{pid} .pild", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }}, {t0 + 0.3 + llenar:.3f});\n')

        elif tipo == "chat":
            texto = it["texto"]
            paso = min(0.05, max(0.02, (d - 1.4) / max(1, len(texto))))
            t_esc = t0 + 0.6
            t_fin = t_esc + len(texto) * paso
            cuerpo = (f'<div class="chat vid"><div class="chat-cab"><span class="punto"></span><span class="etq">{esc(it.get("autor", "Claude"))}</span></div>'
                      f'<div class="chat-txt">{_letras(texto)}<span class="cursor"></span></div>'
                      f'<div class="chat-pie"><div class="enviar">↑</div></div></div>')
            js += _escribir(f"#{pid} .chat-txt", len(texto), t_esc, paso)
            js += f'        ptl.fromTo("#{pid} .cursor", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.3, repeat: {max(1, int(d / 0.6))}, yoyo: true, ease: "steps(1)" }}, {t0:.3f});\n'
            js += (f'        ptl.fromTo("#{pid} .enviar", {{ scale: 1, boxShadow: "0 0 0 0 rgba(93,215,185,.6)" }}, {{ scale: .84, boxShadow: "0 0 0 {18}px rgba(93,215,185,0)", duration: 0.18, yoyo: true, repeat: 1, ease: "power2.out" }}, {t_fin + 0.15:.3f});\n')

        elif tipo == "pasos":
            tarjetas = ""
            for k, p in enumerate(it["items"]):
                anim = p.get("anim")
                if anim == "rec":
                    mini = '<div class="rec"><span class="rec-p"></span>REC</div>'
                elif anim == "onda":
                    barras = lambda g: "".join(f'<span style="height:{a}%"></span>' for a in g)
                    mini = (f'<div class="onda"><div class="grupo g0">{barras([40, 72, 30, 92, 56])}</div><i class="h"></i><i class="h"></i>'
                            f'<div class="grupo g1">{barras([84, 46, 66])}</div><i class="h"></i><div class="grupo g2">{barras([52, 88, 36])}</div></div>')
                elif anim == "estilos":
                    mini = '<div class="chips">' + "".join(f'<span class="chip{" elegido" if c == p.get("elegido", "Espacial") else ""}">{esc(c)}</span>'
                                                         for c in p.get("opciones", ["Minimal", "Espacial", "Golpe"])) + "</div>"
                else:
                    mini = ""
                tarjetas += (f'<div class="paso vid" id="{pid}-p{k}"><div class="paso-n grad">{esc(p.get("num", f"{k + 1:02d}"))}</div>'
                             f'<div class="paso-a">{mini}</div><div class="paso-t">{esc(p["texto"])}</div></div>')
            cuerpo = f'<div class="pasos">{tarjetas}</div>'
            js += f'        ptl.set("#{pid} .paso", {{ opacity: .22, borderStyle: "dashed" }}, {t0:.3f});\n'
            js += f'        ptl.set("#{pid} .paso > *", {{ opacity: 0 }}, {t0:.3f});\n'
            for k, p in enumerate(it["items"]):
                tk = anclas.t(p, t0 + 0.6 + 1.2 * k)
                sel = f"#{pid}-p{k}"
                js += (f'        ptl.to("{sel}", {{ opacity: 1, borderStyle: "solid", borderColor: "rgba(93,215,185,.85)", y: -10, duration: 0.35, ease: "power3.out" }}, {tk:.3f});\n'
                       f'        ptl.to("{sel} > *", {{ opacity: 1, duration: 0.3, stagger: 0.08 }}, {tk:.3f});\n')
                if k > 0:
                    js += f'        ptl.to("#{pid}-p{k - 1}", {{ borderColor: "rgba(197,234,234,.25)", y: 0, duration: 0.3 }}, {tk:.3f});\n'
                anim = p.get("anim")
                if anim == "rec":
                    js += f'        ptl.fromTo("{sel} .rec-p", {{ scale: 1, opacity: 1 }}, {{ scale: .7, opacity: .45, duration: 0.45, repeat: 5, yoyo: true, ease: "sine.inOut" }}, {tk + 0.3:.3f});\n'
                elif anim == "onda":
                    # los huecos (silencios) se apagan y los grupos de onda se juntan con x (transform, sin layout)
                    hueco = 36 * K  # ancho de un hueco (30 px) + márgenes (6 px)
                    js += (f'        ptl.fromTo("{sel} .onda span", {{ scaleY: .3 }}, {{ scaleY: 1, duration: 0.4, stagger: 0.03, ease: "power2.out" }}, {tk + 0.2:.3f});\n'
                           f'        ptl.to("{sel} .onda .h", {{ opacity: 0, scaleX: 0, duration: 0.4, ease: "power2.in" }}, {tk + 0.8:.3f});\n'
                           f'        ptl.to("{sel} .onda .g0", {{ x: {1.5 * hueco:.1f}, duration: 0.5, ease: "power3.inOut" }}, {tk + 0.9:.3f});\n'
                           f'        ptl.to("{sel} .onda .g1", {{ x: {-0.5 * hueco:.1f}, duration: 0.5, ease: "power3.inOut" }}, {tk + 0.9:.3f});\n'
                           f'        ptl.to("{sel} .onda .g2", {{ x: {-1.5 * hueco:.1f}, duration: 0.5, ease: "power3.inOut" }}, {tk + 0.9:.3f});\n')
                elif anim == "estilos":
                    js += (f'        ptl.to("{sel} .chip.elegido", {{ backgroundColor: "#5DD7B9", color: "#021020", borderColor: "#5DD7B9", scale: 1.1, duration: 0.3, ease: "back.out(2)" }}, {tk + 0.7:.3f});\n'
                           f'        ptl.to("{sel} .chip:not(.elegido)", {{ opacity: .35, duration: 0.3 }}, {tk + 0.7:.3f});\n')

        elif tipo == "barra":
            de, a = int(it.get("de", 60)), int(it.get("a", 5))
            tira = f'<div class="grad n-de">{de}</div><div class="grad n-a">{a}</div>'
            tc = anclas.t({"ancla": it["ancla_cambio"]}, t0 + d * 0.45) if it.get("ancla_cambio") else t0 + d * 0.45
            cuerpo = (f'<div class="barra"><div class="barra-etq"><div class="etq e-antes">{esc(it.get("antes", "antes"))}</div>'
                      f'<div class="etq e-despues">{esc(it.get("despues", "ahora"))}</div></div>'
                      f'<div class="rodillo-fila"><div class="rodillo">{tira}</div><div class="rodillo-u">{esc(it.get("unidad", "min"))}</div></div>'
                      f'<div class="barra-pista"><div class="barra-rel"></div></div></div>')
            js += (f'        ptl.set("#{pid} .e-despues, #{pid} .n-a", {{ opacity: 0 }}, {t0:.3f});\n'
                   f'        ptl.fromTo("#{pid} .barra-rel", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.6, ease: "power3.out" }}, {t0 + 0.3:.3f});\n'
                   f'        ptl.to("#{pid} .n-de", {{ opacity: 0, yPercent: -40, filter: "blur(8px)", duration: 0.45, ease: "power2.in" }}, {tc:.3f});\n'
                   f'        ptl.fromTo("#{pid} .n-a", {{ opacity: 0, yPercent: 40, filter: "blur(8px)" }}, {{ opacity: 1, yPercent: 0, filter: "blur(0px)", duration: 0.5, ease: "power3.out" }}, {tc + 0.35:.3f});\n'
                   f'        ptl.to("#{pid} .barra-rel", {{ scaleX: {a / de:.4f}, duration: 0.9, ease: "power3.inOut" }}, {tc:.3f});\n'
                   f'        ptl.to("#{pid} .e-antes", {{ opacity: 0, duration: 0.25 }}, {tc:.3f});\n'
                   f'        ptl.to("#{pid} .e-despues", {{ opacity: 1, duration: 0.25 }}, {tc + 0.25:.3f});\n')

        elif tipo == "flujo":
            lineas = "".join(f'<i style="width:{w}%"></i>' for w in (55, 92, 80, 88, 64, 74))
            cuerpo = (f'<div class="flujo"><div class="doc vid"><div class="etq">{esc(it.get("de", "Brief"))}</div>{lineas}</div>'
                      f'<div class="flecha-l"></div>'
                      f'<div class="listo vid"><div class="marco"></div><div class="prog"><b></b></div><div class="etq">{esc(it.get("a", "Vídeo listo"))}</div><div class="ok">✓</div></div></div>')
            ta = t0 + min(1.0, d * 0.25)
            tb = ta + 0.35
            tp = min(1.3, max(0.6, t1 - tb - 0.9))
            js += (f'        ptl.fromTo("#{pid} .doc i", {{ scaleX: 0, transformOrigin: "0 50%" }}, {{ scaleX: 1, duration: 0.3, stagger: 0.08, ease: "power2.out" }}, {t0 + 0.25:.3f});\n'
                   f'        ptl.fromTo("#{pid} .flecha-l", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.35, ease: "power3.out" }}, {ta:.3f});\n'
                   f'        ptl.fromTo("#{pid} .listo", {{ opacity: 0, x: 40 }}, {{ opacity: 1, x: 0, duration: 0.4, ease: "power3.out" }}, {tb:.3f});\n'
                   f'        ptl.fromTo("#{pid} .prog b", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {tp:.2f}, ease: "power1.inOut" }}, {tb + 0.2:.3f});\n'
                   f'        ptl.fromTo("#{pid} .ok", {{ scale: 0, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.2)" }}, {tb + 0.2 + tp:.3f});\n')

        elif tipo == "comentario":
            texto = it.get("texto", "EDITA")
            # el cierre necesita ≥ 2 s en pantalla: se escribe pronto y rápido
            t_esc = anclas.t({"ancla": it["ancla_texto"]}, t0 + 0.3) if it.get("ancla_texto") else t0 + 0.3
            ph = f'<span class="ph">{esc(it["placeholder"])}</span>' if it.get("placeholder") else ""
            cuerpo = (f'<div class="coment"><div class="burbuja vid"><div class="avatar"></div><div class="campo">'
                      f'{ph}<span class="esc">{_letras(texto)}<span class="cursor"></span></span></div>'
                      f'<div class="enviar">↑</div></div>' + (f'<div class="coment-sub">{esc(it["sub"])}</div>' if it.get("sub") else "") + "</div>")
            js += f'        ptl.set("#{pid} .esc .cursor", {{ opacity: 0 }}, {t0:.3f});\n'
            if ph:
                js += f'        ptl.set("#{pid} .ph", {{ opacity: 0 }}, {t_esc:.3f});\n'
            js += f'        ptl.set("#{pid} .esc .cursor", {{ opacity: 1 }}, {t_esc:.3f});\n'
            js += _escribir(f"#{pid} .esc", len(texto), t_esc, 0.06)
            t_fin = t_esc + len(texto) * 0.06
            js += f'        ptl.fromTo("#{pid} .enviar", {{ scale: 1 }}, {{ scale: .84, duration: 0.18, yoyo: true, repeat: 3, ease: "power2.out" }}, {t_fin + 0.1:.3f});\n'
            if it.get("sub"):
                ts = anclas.t({"ancla": it["ancla_sub"]}, t_esc) if it.get("ancla_sub") else t_esc
                js += f'        ptl.fromTo("#{pid} .coment-sub", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }}, {ts:.3f});\n'
        else:
            raise ValueError(f"Tipo de motion desconocido en el panel: {tipo}")

        clips.append(f'        <div id="{pid}" class="pitem clip" data-start="{t0:.3f}" data-duration="{d:.3f}" data-track-index="1"><div class="pm"><div class="pm-esc"><div class="pm-in">{cuerpo}</div></div></div></div>')
        js += entra + sale
    return NL.join(clips), js
