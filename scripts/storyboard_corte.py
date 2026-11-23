"""Storyboard visual de la propuesta de corte: una página HTML para revisar los cortes de un vistazo.

Uso:
  python storyboard_corte.py --trabajo 06_trabajo [--keep 06_trabajo/keep.json] [--out 06_trabajo/storyboard-corte.html]

Lee:
  - keep.json (o, si no existe, propuesta.json): los tramos que se quedan.
  - propuesta.json (palabras con «quitar» y probabilidad) o, si no hay, palabras-bruto.json.
  - vertical.mp4 y audio16k.wav de 06_trabajo.
Escribe una página que se abre en el navegador, sin internet:
  - Barra de tiempo con la forma de la voz: verde = se queda, rosa = se quita. Se puede pulsar.
  - Una tarjeta por escena (tramo que se queda) con fotograma inicial y final, tiempos y lo que se dice.
  - Entre escenas, el corte: qué se quita (texto tachado o «silencio de X s») y por qué.
  - Palabras dudosas en amarillo y palabras que el programa quería quitar pero se quedan, subrayadas.
  - Botones ▶ para escuchar cada escena o cada trozo que se quita en el vídeo preparado.
"""
import argparse
import base64
import html
import os
import tempfile
from collections import Counter
from pathlib import Path

from comun import SKILL, aviso, error, ffmpeg, leer_json

AIRE_MIN = 0.12  # huecos más cortos que esto no se consideran corte (bordes ajustados)


def b64(ruta):
    return base64.b64encode(Path(ruta).read_bytes()).decode()


def fotograma(video, t, tmp, nombre):
    out = Path(tmp) / f"{nombre}.jpg"
    ffmpeg(["-ss", f"{max(t, 0):.3f}", "-i", str(video), "-frames:v", "1",
            "-vf", "scale=270:-2", "-q:v", "4", str(out)])
    return b64(out) if out.exists() else ""


def forma_de_onda(audio, duracion, columnas=600):
    try:
        import numpy as np
        from audio import leer_mono
        m = leer_mono(audio)
        if len(m) == 0:
            return []
        n = max(len(m) // columnas, 1)
        bloques = m[: n * columnas].reshape(-1, n) if len(m) >= n * columnas else m.reshape(1, -1)
        pico = np.sqrt(np.mean(bloques ** 2, axis=1))
        pico = pico / (pico.max() + 1e-9)
        return [round(float(x), 3) for x in pico]
    except Exception:
        return []


def fmt(t):
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:04.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trabajo", required=True)
    ap.add_argument("--keep")
    ap.add_argument("--video")
    ap.add_argument("--out")
    a = ap.parse_args()

    tr = Path(a.trabajo)
    keep_ruta = Path(a.keep) if a.keep else (tr / "keep.json" if (tr / "keep.json").exists() else tr / "propuesta.json")
    if not keep_ruta.exists():
        error("No encuentro keep.json ni propuesta.json. Ejecuta antes analizar.py.")
    keep = leer_json(keep_ruta)
    if isinstance(keep, dict):
        keep = keep["tramos"]
    keep = sorted(keep, key=lambda x: x["start"])

    if (tr / "propuesta.json").exists():
        prop = leer_json(tr / "propuesta.json")
        palabras = prop["palabras"]
        duracion = prop.get("duracion_original")
    else:
        palabras = leer_json(tr / "palabras-bruto.json")
        duracion = None
    video = Path(a.video) if a.video else tr / "vertical.mp4"
    if not video.exists():
        error(f"No encuentro {video}. Ejecuta antes preparar.py.")
    from comun import sondear
    voz = tr / "audio48k.wav"
    if not sondear(video)["tiene_audio"] and voz.exists():
        # vertical.mp4 va sin sonido (la voz se guarda aparte): para ver y oír el corte se junta en una copia
        con_voz = tr / "vista-con-voz.mp4"
        if not con_voz.exists() or con_voz.stat().st_mtime < video.stat().st_mtime:
            aviso("Juntando el vídeo con la voz para poder escucharlo en el storyboard…")
            ffmpeg(["-y", "-i", str(video), "-i", str(voz), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(con_voz)])
        video = con_voz
    if not duracion:
        duracion = float(sondear(video).get("duracion") or palabras[-1]["end"])
    out = Path(a.out) if a.out else tr / "storyboard-corte.html"

    def dentro(p):
        # Whisper estira palabras sobre los silencios («¿Te» de 0,0 a 0,76 s cuando la voz empieza en 0,6):
        # una palabra se queda si cualquier parte suya cae dentro de un tramo, no solo su centro.
        return any(p["end"] > t["start"] + 0.03 and p["start"] < t["end"] - 0.03 for t in keep)

    for p in palabras:
        p["_queda"] = dentro(p)

    # Bloques alternos: corte · escena · corte · escena …
    bloques = []
    cursor = 0.0
    for i, t in enumerate(keep):
        if t["start"] - cursor >= AIRE_MIN:
            bloques.append({"tipo": "corte", "start": cursor, "end": t["start"]})
        bloques.append({"tipo": "escena", "n": i + 1, "start": t["start"], "end": t["end"]})
        cursor = t["end"]
    if duracion - cursor >= AIRE_MIN:
        bloques.append({"tipo": "corte", "start": cursor, "end": duracion})

    aviso(f"Haciendo el storyboard: {len(keep)} escenas…")
    with tempfile.TemporaryDirectory() as tmp:
        for b in bloques:
            if b["tipo"] == "escena":
                ws = [p for p in palabras if p["_queda"] and p["end"] > b["start"] + 0.03 and p["start"] < b["end"] - 0.03
                      and not any(q is not b and q["tipo"] == "escena" and q["start"] <= (p["start"] + p["end"]) / 2 <= q["end"] for q in bloques)]
            else:
                ws = [p for p in palabras if not p["_queda"] and b["start"] <= (p["start"] + p["end"]) / 2 <= b["end"]]
            b["palabras"] = ws
            if b["tipo"] == "escena":
                dur = b["end"] - b["start"]
                b["img1"] = fotograma(video, b["start"] + 0.1, tmp, f"e{b['n']}a")
                b["img2"] = fotograma(video, b["end"] - 0.15, tmp, f"e{b['n']}b") if dur > 1.2 else ""
    onda = forma_de_onda(tr / "audio16k.wav", duracion)

    final = sum(t["end"] - t["start"] for t in keep)
    n_cortes = sum(1 for b in bloques if b["tipo"] == "corte")
    dudosas = sum(1 for p in palabras if p.get("p", 1) < 0.6 and p["_queda"])
    rescatadas = sum(1 for p in palabras if p.get("quitar") and p["_queda"])

    def texto_palabras(ws, en_escena):
        partes = []
        for p in ws:
            w = html.escape(p["w"])
            clases, titulo = [], []
            if not p["_queda"]:
                clases.append("fuera")
            if en_escena and p.get("quitar"):
                clases.append("rescate")
                titulo.append(f"El programa quería quitarla ({p['quitar']}), pero se queda")
            if p.get("p", 1) < 0.6:
                clases.append("duda")
                titulo.append("Palabra dudosa: revisa cómo se escribe")
            t = f' title="{html.escape(" · ".join(titulo))}"' if titulo else ""
            partes.append(f'<span class="{" ".join(clases)}"{t}>{w}</span>' if clases else w)
        return " ".join(partes)

    def motivo(ws):
        if not ws:
            return "Silencio"
        r = Counter((p.get("quitar") or "lo quita Claude al revisar").split(" (")[0] for p in ws)
        return " · ".join(k.capitalize() for k, _ in r.most_common())

    tarjetas = []
    for b in bloques:
        d = b["end"] - b["start"]
        if b["tipo"] == "corte":
            txt = texto_palabras(b["palabras"], False) if b["palabras"] else ""
            tarjetas.append(f"""
<div class="corte" data-a="{b['start']:.3f}" data-b="{b['end']:.3f}">
  <div class="tijera">✂</div>
  <div class="corte-cuerpo">
    <div class="corte-tit">Se quita · {d:.1f} s · <span class="motivo">{html.escape(motivo(b['palabras']))}</span></div>
    {f'<div class="corte-txt">{txt}</div>' if txt else ''}
  </div>
  <button class="play" aria-label="Escuchar lo que se quita">▶</button>
</div>""")
        else:
            imgs = f'<img src="data:image/jpeg;base64,{b["img1"]}" alt="">'
            if b.get("img2"):
                imgs += f'<img src="data:image/jpeg;base64,{b["img2"]}" alt="">'
            tarjetas.append(f"""
<div class="escena" data-a="{b['start']:.3f}" data-b="{b['end']:.3f}">
  <div class="fotos">{imgs}</div>
  <div class="escena-cuerpo">
    <div class="escena-tit"><span class="num">{b['n']:02d}</span> {fmt(b['start'])} → {fmt(b['end'])} <span class="dur">{d:.1f} s</span></div>
    <div class="escena-txt">{texto_palabras(b['palabras'], True) or '<em>(sin voz)</em>'}</div>
  </div>
  <button class="play" aria-label="Ver esta escena">▶</button>
</div>""")

    segs = "".join(
        f'<div class="seg {"si" if b["tipo"] == "escena" else "no"}" style="left:{b["start"] / duracion * 100:.3f}%;width:{(b["end"] - b["start"]) / duracion * 100:.3f}%"></div>'
        for b in bloques)
    barras = "".join(f'<i style="height:{max(v * 100, 2):.1f}%"></i>' for v in onda)

    fuente = ""
    f = SKILL / "fonts" / "Figtree-Bold.ttf"
    if f.exists():
        fuente = f"@font-face{{font-family:Figtree;font-weight:700;src:url(data:font/ttf;base64,{b64(f)})}}"
    f2 = SKILL / "fonts" / "Figtree-SemiBold.ttf"
    if f2.exists():
        fuente += f"@font-face{{font-family:Figtree;font-weight:500;src:url(data:font/ttf;base64,{b64(f2)})}}"

    src_video = Path(os.path.relpath(video.resolve(), out.resolve().parent)).as_posix()

    pagina = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Storyboard del corte</title>
<style>
{fuente}
:root{{--noche:#021020;--petroleo:#254B57;--crema:#F8F2E9;--humo:#C5EAEA;--menta:#5DD7B9;--rosa:#F59BC4;--amarillo:#FBDF4E;--tarjeta:#0a1e33}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--noche);color:var(--crema);font:500 15px/1.5 Figtree,system-ui,sans-serif}}
.marco{{display:grid;grid-template-columns:300px 1fr;gap:28px;max-width:1100px;margin:0 auto;padding:24px 16px 60px}}
@media (max-width:760px){{.marco{{grid-template-columns:1fr}} .lateral{{position:static!important}} video{{max-height:50vh}}}}
.lateral{{position:sticky;top:16px;align-self:start}}
video{{width:100%;border-radius:14px;background:#000;display:block}}
h1{{font-weight:700;font-size:26px;margin:0 0 4px}}
.cifras{{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}}
.cifra{{background:var(--tarjeta);border:1px solid var(--petroleo);border-radius:12px;padding:8px 12px}}
.cifra b{{display:block;font-size:20px;color:var(--menta)}}
.leyenda{{font-size:13px;color:var(--humo);line-height:1.9}}
.leyenda span{{padding:1px 5px;border-radius:4px}}
.linea{{position:relative;height:70px;background:var(--tarjeta);border-radius:12px;overflow:hidden;cursor:pointer;margin:18px 0 6px}}
.seg{{position:absolute;top:0;bottom:0}} .seg.si{{background:rgba(93,215,185,.22)}} .seg.no{{background:rgba(245,155,196,.35)}}
.onda{{position:absolute;inset:6px 0;display:flex;align-items:center;gap:0}}
.onda i{{flex:1;background:var(--crema);opacity:.55;border-radius:1px}}
.cabezal{{position:absolute;top:0;bottom:0;width:2px;background:var(--amarillo);left:0}}
.tiempos{{display:flex;justify-content:space-between;font-size:12px;color:var(--humo);margin-bottom:22px}}
.escena,.corte{{display:flex;gap:14px;align-items:center;border-radius:14px;margin:10px 0}}
.escena{{background:var(--tarjeta);border:1px solid var(--petroleo);padding:12px}}
.escena.activa{{border-color:var(--menta);box-shadow:0 8px 24px rgba(93,215,185,.22)}}
.fotos{{display:flex;gap:6px;flex-shrink:0}}
.fotos img{{width:68px;border-radius:8px;display:block}}
.escena-cuerpo,.corte-cuerpo{{flex:1;min-width:0}}
.escena-tit{{font-size:13px;color:var(--humo);margin-bottom:4px}}
.num{{font-weight:700;color:var(--noche);background:var(--menta);border-radius:6px;padding:0 6px;margin-right:4px}}
.dur{{float:right;color:var(--menta);font-weight:700}}
.escena-txt{{font-size:16px}}
.corte{{padding:6px 12px;margin-left:30px;border:1px dashed var(--rosa);background:rgba(245,155,196,.07)}}
.corte.activa{{background:rgba(245,155,196,.2)}}
.tijera{{color:var(--rosa);font-size:18px}}
.corte-tit{{font-size:13px;color:var(--rosa);font-weight:700}}
.motivo{{font-weight:500;color:var(--crema)}}
.corte-txt{{font-size:14px;color:var(--humo)}}
.fuera{{text-decoration:line-through;text-decoration-color:var(--rosa);opacity:.8}}
.duda{{background:rgba(251,223,78,.25);border-bottom:2px solid var(--amarillo);border-radius:3px}}
.rescate{{border-bottom:2px solid var(--menta)}}
.play{{flex-shrink:0;width:40px;height:40px;border-radius:50%;border:0;background:var(--menta);color:var(--noche);font-size:15px;cursor:pointer}}
.corte .play{{background:var(--rosa);width:32px;height:32px;font-size:12px}}
.modo{{display:flex;gap:6px;margin-top:10px}}
.modo button{{flex:1;padding:8px;border-radius:10px;border:1px solid var(--petroleo);background:var(--tarjeta);color:var(--crema);font:inherit;font-size:13px;cursor:pointer}}
.modo button.on{{background:var(--menta);color:var(--noche);border-color:var(--menta);font-weight:700}}
</style></head><body>
<div class="marco">
  <div class="lateral">
    <video id="v" src="{html.escape(src_video)}" controls playsinline preload="metadata"></video>
    <div class="modo">
      <button id="m-orig" class="on">Original</button>
      <button id="m-corte">Así quedaría</button>
    </div>
  </div>
  <div>
    <h1>Storyboard del corte</h1>
    <div class="cifras">
      <div class="cifra">Antes<b>{duracion:.1f} s</b></div>
      <div class="cifra">Después<b>{final:.1f} s</b></div>
      <div class="cifra">Escenas<b>{len(keep)}</b></div>
      <div class="cifra">Cortes<b>{n_cortes}</b></div>
    </div>
    <div class="leyenda">
      <span style="background:rgba(93,215,185,.22)">verde</span> se queda ·
      <span style="background:rgba(245,155,196,.35)">rosa</span> se quita ·
      <span class="duda">amarillo</span> palabra dudosa ({dudosas})
      {f'· <span class="rescate">subrayado</span> el programa quería quitarla, pero se queda ({rescatadas})' if rescatadas else ''}
    </div>
    <div class="linea" id="linea">{segs}<div class="onda">{barras}</div><div class="cabezal" id="cab"></div></div>
    <div class="tiempos"><span>0:00</span><span>{fmt(duracion)}</span></div>
    {''.join(tarjetas)}
  </div>
</div>
<script>
const v=document.getElementById('v'),cab=document.getElementById('cab'),linea=document.getElementById('linea');
const D={duracion:.3f};
const escenas=[...document.querySelectorAll('.escena')].map(e=>[+e.dataset.a,+e.dataset.b]);
const acum=[];escenas.reduce((s,[a,b],i)=>(acum[i]=s,s+b-a),0);
const ORIG=v.getAttribute('src'), CORTE='asi-quedaria.mp4';
let fin=null, modoCorte=false;
function aOriginal(t){{for(let i=escenas.length-1;i>=0;i--) if(t>=acum[i]) return escenas[i][0]+(t-acum[i]);return 0;}}
function fuente(src,t,luego){{if(v.getAttribute('src')===src){{v.currentTime=t;luego&&luego();return;}}
  v.setAttribute('src',src);v.addEventListener('loadedmetadata',()=>{{v.currentTime=t;luego&&luego();}},{{once:true}});v.load();}}
function marcar(t){{document.querySelectorAll('.escena,.corte').forEach(e=>e.classList.toggle('activa',t>=+e.dataset.a&&t<+e.dataset.b));}}
function tocar(a,b){{modoCorte=false;botones();fin=b;fuente(ORIG,a,()=>v.play());}}
document.querySelectorAll('.escena,.corte').forEach(e=>e.querySelector('.play').onclick=()=>tocar(+e.dataset.a,+e.dataset.b));
linea.onclick=ev=>{{const r=linea.getBoundingClientRect();fin=null;modoCorte=false;botones();fuente(ORIG,(ev.clientX-r.left)/r.width*D,()=>v.play());}};
v.addEventListener('timeupdate',()=>{{
  const t=modoCorte?aOriginal(v.currentTime):v.currentTime;cab.style.left=(t/D*100)+'%';marcar(t);
  if(fin!==null&&t>=fin){{v.pause();fin=null;}}
}});
function botones(){{document.getElementById('m-orig').classList.toggle('on',!modoCorte);document.getElementById('m-corte').classList.toggle('on',modoCorte);}}
document.getElementById('m-orig').onclick=()=>{{modoCorte=false;fin=null;botones();fuente(ORIG,0);}};
document.getElementById('m-corte').onclick=()=>{{modoCorte=true;fin=null;botones();fuente(CORTE,0,()=>v.play());}};
</script></body></html>"""
    out.write_text(pagina, encoding="utf-8")
    # «Así quedaría»: un vídeo con el corte hecho de verdad (saltar en directo no vale: el navegador comprueba el
    # tiempo ~4 veces por segundo y las pausas de 0,1-0,5 s se oían igual)
    asi = out.parent / "asi-quedaria.mp4"
    aviso("Montando «Así quedaría»…")
    con_audio = sondear(video)["tiene_audio"]
    partes, n = [], len(keep)
    for i, t in enumerate(keep):
        partes.append(f"[0:v]trim={t['start']:.3f}:{t['end']:.3f},setpts=PTS-STARTPTS,scale=540:-2[v{i}]")
        if con_audio:
            dur = t["end"] - t["start"]
            partes.append(f"[0:a]atrim={t['start']:.3f}:{t['end']:.3f},asetpts=PTS-STARTPTS,"
                          f"afade=t=in:d=0.012,afade=t=out:st={max(dur - 0.012, 0):.3f}:d=0.012[a{i}]")
    union = "".join(f"[v{i}]" + (f"[a{i}]" if con_audio else "") for i in range(n))
    partes.append(f"{union}concat=n={n}:v=1:a={1 if con_audio else 0}[v]" + ("[a]" if con_audio else ""))
    mapas = ["-map", "[v]"] + (["-map", "[a]", "-c:a", "aac", "-b:a", "128k"] if con_audio else [])
    ffmpeg(["-y", "-i", str(video), "-filter_complex", ";".join(partes), *mapas, "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "28", "-movflags", "+faststart", str(asi)])
    aviso(f"Storyboard: {out}  ({len(keep)} escenas, {n_cortes} cortes, {duracion:.1f} s → {final:.1f} s)")


if __name__ == "__main__":
    main()
