# /// script
# requires-python = ">=3.10"
# ///
"""Render final: brutos → vídeo vertical cortado, subtitulado y con el volumen de las redes.

Uso:
    uv run render.py <carpeta del talento> [--sin-gpu] [--sin-revision]

Lee 06_entrega/trabajo/cortes.json y subtitulos.ass (de cortar.py y subtitulos.py) y hace en una
sola pasada desde los brutos: corte, subtítulos y volumen. El color sale como se grabó:
HDR (HEVC 10 bits) si los brutos son HDR, SDR (H.264) si son SDR (ver color.py).

Escribe en 06_entrega/:
    video-vN.mp4          1080×1920, 30 fps, HEVC 10 bits HDR o H.264 SDR, audio AAC a −14 LUFS
    subtitulos-vN.srt     los subtítulos del vídeo, para entregar o subir a la red
y en 06_entrega/trabajo/revision/ los fotogramas clave, la hoja de contacto y revision.md.

N es la primera versión libre: nunca se sobrescribe una entrega anterior.
Si hay tarjeta NVIDIA (o un Mac), usa el hardware para leer y codificar el vídeo; si falla,
vuelve solo al procesador. Códigos: 0 bien · 1 error · 2 falta algo.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import color  # noqa: E402
from cortar import FPS  # noqa: E402
import fuentes as letras  # noqa: E402
from subtitulos import ruta_filtro, todas_las_letras  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LUFS = -14.0          # referencia de TikTok, Instagram y YouTube
PICO = -1.5           # dBTP máximo
FOTOGRAMAS = 8


def ejecutar(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


# ---------- hardware ----------

def hardware(sin_gpu: bool, decision: dict) -> dict:
    """Elige cómo leer y codificar: NVIDIA (CUDA + NVENC), Mac (VideoToolbox) o procesador.
    En HDR se codifica en HEVC 10 bits; en SDR, en H.264."""
    hdr = decision["modo"] == "hdr"
    cpu = {"nombre": "procesador", "entrada": [], "codec": color.codec_cpu(decision)}
    if sin_gpu:
        return cpu
    codificadores = ejecutar(["ffmpeg", "-hide_banner", "-encoders"]).stdout
    if shutil.which("nvidia-smi"):
        nombre = "hevc_nvenc" if hdr else "h264_nvenc"
        nvenc = ["-c:v", nombre, "-preset", "p5", "-tune", "hq", "-rc", "vbr", "-cq", "19", "-b:v", "0",
                 *(["-profile:v", "main10", "-tag:v", "hvc1"] if hdr else [])]
        if f" {nombre} " in codificadores and prueba_codificador(nvenc, decision):
            return {"nombre": "tarjeta NVIDIA", "entrada": ["-hwaccel", "cuda"], "codec": nvenc}
        # La tarjeta lee el vídeo aunque no pueda codificarlo (p. ej. con un controlador antiguo).
        aviso = ejecutar(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                          "testsrc2=size=256x256:duration=0.1", "-c:v", nombre, "-f", "null", "-"]).stderr
        motivo = next((l.split("] ", 1)[-1] for l in aviso.splitlines() if "minimum required" in l), "")
        return {"nombre": "tarjeta NVIDIA para leer y procesador para codificar", "entrada": ["-hwaccel", "cuda"],
                "codec": cpu["codec"], "aviso": motivo}
    nombre = "hevc_videotoolbox" if hdr else "h264_videotoolbox"
    if platform.system() == "Darwin" and f" {nombre} " in codificadores:
        vt = ["-c:v", nombre, "-q:v", "65", *(["-profile:v", "main10", "-tag:v", "hvc1"] if hdr else [])]
        if prueba_codificador(vt, decision):
            return {"nombre": "Mac (VideoToolbox)", "entrada": ["-hwaccel", "videotoolbox"], "codec": vt}
    return cpu


def prueba_codificador(codec: list[str], decision: dict) -> bool:
    """Codifica 0,1 s de prueba: que el codificador exista no garantiza que el controlador lo acepte."""
    return ejecutar(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                     "testsrc2=size=1080x1920:rate=30:duration=0.1",
                     *codec, *color.etiquetas_salida(decision), "-f", "null", "-"]).returncode == 0


# ---------- grafo ----------

def entradas(segmentos: list[dict], brutos: Path, por_entrada: list[str]) -> list[str]:
    args = []
    for s in segmentos:
        d = s["cuadros"] / FPS
        args += [*por_entrada, "-ss", f"{s['inicio']:.3f}", "-t", f"{d + 0.2:.3f}", "-i", str(brutos / s["clip"])]
    return args


def cadenas_audio(segmentos: list[dict]) -> str:
    partes = []
    for k, s in enumerate(segmentos):
        d = s["cuadros"] / FPS
        partes.append(f"[{k}:a:0]asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,"
                      f"atrim=end={d:.6f},apad=whole_dur={d:.6f},"
                      f"afade=t=in:d=0.01,afade=t=out:st={max(d - 0.01, 0):.6f}:d=0.01[a{k}];")
    return "".join(partes)


def subtitulos_con_huecos(ass: Path) -> Path:
    """Copia de los subtítulos para el render: sin texto mientras se ve una cifra grande
    (textos.py) y con el texto en la unión de las dos mitades durante una pantalla partida
    (recursos.py). Si no hace falta nada de eso, los subtítulos tal cual."""
    huecos_f = ass.with_name("textos-huecos.json")
    if not ass.with_name("textos.ass").exists():
        huecos_f = ass.with_name("no-hay-huecos.json")
    huecos = json.loads(huecos_f.read_text(encoding="utf-8")).get("sin_subtitulos", []) if huecos_f.exists() else []
    partidas = [(r["inicio"], r["fin"]) for r in plan_recursos(ass) if r["modo"] == "partida"]
    if not huecos and not partidas:
        return ass

    def seg(t: str) -> float:
        h, m, s = t.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    def ts(x: float) -> str:
        cs = round(x * 100)
        return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"

    lineas = []
    for linea in ass.read_text(encoding="utf-8").splitlines():
        if not linea.startswith("Dialogue:"):
            lineas.append(linea)
            continue
        cab, resto = linea.split(":", 1)
        p = resto.split(",", 9)
        ini, fin = seg(p[1]), seg(p[2])
        trozos = [(ini, fin)]
        for a, b in huecos:
            nuevos = []
            for x, y in trozos:
                if y <= a or x >= b:
                    nuevos.append((x, y))
                    continue
                if x < a:
                    nuevos.append((x, a))
                if y > b:
                    nuevos.append((b, y))
            trozos = nuevos
        # Trozos dentro de una pantalla partida: el texto sube a la unión de las dos mitades.
        finales = []
        for x, y in trozos:
            cortes_t = sorted({x, y, *[c for a, b in partidas for c in (a, b) if x < c < y]})
            finales += list(zip(cortes_t, cortes_t[1:]))
        for x, y in finales:
            if y - x >= 0.1:
                p[1], p[2] = ts(x), ts(y)
                texto = p[9]
                if any(a <= (x + y) / 2 < b for a, b in partidas):
                    p[9] = "{\\an2\\pos(540,945)}" + texto
                lineas.append(cab + ":" + ",".join(p))
                p[9] = texto
    copia = ass.with_name("subtitulos-render.ass")
    copia.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return copia


def plan_recursos(ass: Path) -> list[dict]:
    """Recursos en pantalla preparados por recursos.py (vacío si no hay)."""
    f = ass.with_name("recursos-plan.json")
    if not f.exists():
        return []
    return json.loads(f.read_text(encoding="utf-8")).get("recursos", [])


def entradas_recursos(plan: list[dict]) -> list[str]:
    args = []
    for r in plan:
        dura = r["fin"] - r["inicio"] + 0.3
        if r["tipo"] == "imagen":
            args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dura:.3f}", "-i", r["preparado"]]
        else:
            args += ["-ss", f"{r.get('desde', 0):.3f}", "-t", f"{dura:.3f}", "-i", r["archivo"]]
    return args


def capas_recursos(plan: list[dict], primera: int, decision: dict, entrada: str) -> tuple[str, str]:
    """Filtros que ponen cada recurso encima del vídeo (en orden de tiempo). Devuelve el grafo y la
    etiqueta de salida.
    - completo: el recurso cubre la pantalla (las fotos con un acercamiento lento del 5 %).
    - tarjeta: entra deslizándose 40 px con un fundido de 0,18 s y sale con fundido.
    - partida: el recurso arriba (1080×960) y abajo el propio vídeo recortado alrededor de la cara."""
    hdr = decision["modo"] == "hdr"
    matriz, formato = ("bt2020", "yuva420p10le") if hdr else ("bt709", "yuva420p")
    mezcla = "yuv420p10" if hdr else "yuv420"
    partes, actual = [], entrada
    y_tarjeta = round(1920 * 0.38)
    partidas = [r for r in plan if r["modo"] == "partida"]
    if partidas:
        # Una copia del vídeo por cada pantalla partida, para recortar al talento en su mitad.
        partes.append(f"[{entrada}]split={len(partidas) + 1}[base]" + "".join(f"[pm{j}]" for j in range(len(partidas))) + ";")
        actual = "base"
    j_partida = 0
    for k, r in enumerate(plan):
        i = primera + k
        ini, fin = r["inicio"], r["fin"]
        alto_rec = 960 if r["modo"] == "partida" else 1920
        if r["tipo"] == "imagen":
            # PNG ya escalado (y en HLG si el vídeo es HDR): solo se pasa a YUV con la matriz correcta.
            base = f"[{i}:v:0]scale=out_color_matrix={matriz}:out_range=tv,format={formato}"
            if r["modo"] in ("completo", "partida"):
                # Foto que llena su sitio: acercamiento lento del 5 % para que no parezca congelada.
                d = max(fin - ini, 0.1)
                base += (f",scale=w='1080*(1+0.05*t/{d:.3f})':h='{alto_rec}*(1+0.05*t/{d:.3f})':eval=frame:flags=bicubic,"
                         f"crop=1080:{alto_rec}:(iw-1080)/2:(ih-{alto_rec})/2")
        elif r["modo"] == "completo" and r.get("horizontal"):
            # Clip horizontal a pantalla completa: entero y centrado, con una copia suya ampliada y
            # desenfocada de fondo (como hacen las apps). El color no se toca.
            partes.append(f"[{i}:v:0]setsar=1,fps={FPS},split[hf{k}][hc{k}];"
                          f"[hf{k}]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                          f"boxblur=luma_radius=40:luma_power=2[hb{k}];"
                          f"[hc{k}]scale=1080:-2:flags=lanczos[hn{k}];"
                          f"[hb{k}][hn{k}]overlay=x=0:y=(H-h)/2[hx{k}];")
            base = f"[hx{k}]format={formato}"
        else:
            if r["modo"] in ("completo", "partida"):
                caja = f"scale=1080:{alto_rec}:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:{alto_rec}"
            else:
                caja = f"scale={r['ancho']}:{r['alto']}:flags=lanczos"
            base = f"[{i}:v:0]{caja},setsar=1,fps={FPS},format={formato}"
        base += f",setpts=PTS-STARTPTS+{ini:.3f}/TB"
        cuando = f"enable='between(t\\,{ini:.3f}\\,{fin:.3f})':eof_action=pass:format={mezcla}"
        if r["modo"] == "tarjeta":
            base += (f",fade=t=in:st={ini:.3f}:d=0.18:alpha=1,"
                     f"fade=t=out:st={max(fin - 0.18, ini):.3f}:d=0.18:alpha=1")
            # La «y» la calcula recursos.py para no tapar la cara. Entra deslizándose 40 px desde
            # fuera de la cara: hacia arriba si está debajo de ella, hacia abajo si está encima.
            y = r.get("y", y_tarjeta)
            signo = "-" if y < 1920 * 0.3 else "+"
            pos = f"x=(W-w)/2:y={y}{signo}40*max(0\\,1-(t-{ini:.3f})/0.2)"
        else:
            pos = "x=0:y=0"
        partes.append(f"{base}[r{k}];")
        partes.append(f"[{actual}][r{k}]overlay={pos}:{cuando}[o{k}];")
        actual = f"o{k}"
        if r["modo"] == "partida":
            j = j_partida
            j_partida += 1
            partes.append(f"[pm{j}]crop=1080:960:0:{r['corte_y']}[pc{j}];")
            partes.append(f"[{actual}][pc{j}]overlay=x=0:y=960:{cuando}[op{j}];")
            actual = f"op{j}"
    return "".join(partes), actual


def grafo_completo(segmentos: list[dict], brutos: Path, decision: dict, ass: Path, fuentes: Path, volumen: str) -> str:
    partes = []
    # Cambio de encuadre (encuadre.py): en los tramos en plano cerrado, recorte hacia la cara y
    # vuelta a 1080×1920.
    f_encuadre = ass.with_name("encuadre.json")
    tramos = json.loads(f_encuadre.read_text(encoding="utf-8"))["tramos"] if f_encuadre.exists() else []
    partidas = [(r["inicio"], r["fin"]) for r in plan_recursos(ass) if r["modo"] == "partida"]
    for k, s in enumerate(segmentos):
        plano = tramos[k] if k < len(tramos) else None
        if plano and any(s["salida_inicio"] < b and s["salida_fin"] > a for a, b in partidas):
            plano = None   # en pantalla partida el talento ya va recortado: sin plano cerrado
        cerrar = (f",crop={plano['ancho']}:{plano['alto']}:{plano['x']}:{plano['y']},scale=1080:1920:flags=lanczos,setsar=1"
                  if plano else "")
        partes.append(f"[{k}:v:0]setpts=PTS-STARTPTS,{color.filtro_clip(brutos / s['clip'], decision, FPS)}{cerrar},"
                      f"trim=end_frame={s['cuadros']},setpts=PTS-STARTPTS[v{k}];")
    union = "".join(f"[v{k}][a{k}]" for k in range(len(segmentos)))
    # Recursos (recursos.py) encima del vídeo; subtítulos y textos, encima de todo.
    capas, salida_capas = capas_recursos(plan_recursos(ass), len(segmentos), decision, "vc")
    return ("".join(partes) + cadenas_audio(segmentos)
            + f"{union}concat=n={len(segmentos)}:v=1:a=1[vc][ac];"
            + capas
            + f"[{salida_capas}]subtitles=filename='{ruta_filtro(subtitulos_con_huecos(ass))}':fontsdir='{ruta_filtro(fuentes)}'"
            # Gancho, cifras y CTA (textos.py), encima de los subtítulos, si los hay.
            + (f",subtitles=filename='{ruta_filtro(ass.with_name('textos.ass'))}':fontsdir='{ruta_filtro(fuentes)}'"
               if ass.with_name("textos.ass").exists() else "")
            + "[v];"
            + f"[ac]{volumen},aresample=48000[a]")


def medir_volumen(segmentos: list[dict], brutos: Path, trabajo: Path) -> dict:
    """Primera pasada (solo audio): mide el volumen del corte para normalizarlo con precisión."""
    union = "".join(f"[a{k}]" for k in range(len(segmentos)))
    grafo = (cadenas_audio(segmentos) + f"{union}concat=n={len(segmentos)}:v=0:a=1,"
             f"loudnorm=I={LUFS}:TP={PICO}:LRA=11:print_format=json[a]")
    script = trabajo / "volumen.filtro.txt"
    script.write_text(grafo, encoding="utf-8")
    r = ejecutar(["ffmpeg", "-hide_banner", "-nostdin", *entradas(segmentos, brutos, []),
                  "-/filter_complex", str(script), "-map", "[a]", "-f", "null", "-"])
    script.unlink(missing_ok=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr)
    if r.returncode != 0 or not m:
        raise RuntimeError("no se pudo medir el volumen: " + r.stderr.strip()[-400:])
    return json.loads(m.group(0))


def filtro_volumen(medida: dict) -> str:
    return (f"loudnorm=I={LUFS}:TP={PICO}:LRA=11:measured_I={medida['input_i']}:measured_TP={medida['input_tp']}:"
            f"measured_LRA={medida['input_lra']}:measured_thresh={medida['input_thresh']}:"
            f"offset={medida['target_offset']}:linear=true")


# ---------- revisión ----------

def instantes(segmentos: list[dict], duracion: float) -> list[float]:
    """Primer cuadro, último y cambios de tramo repartidos por el vídeo."""
    cambios = [s["salida_inicio"] + 0.15 for s in segmentos[1:]]
    paso = max(1, len(cambios) // (FOTOGRAMAS - 2))
    elegidos = cambios[::paso][:FOTOGRAMAS - 2]
    return [0.1, *elegidos, max(duracion - 0.2, 0)]


def eventos_ass(ass: Path) -> list[tuple[float, float]]:
    def t(x: str) -> float:
        h, m, s = x.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    ev = []
    for linea in ass.read_text(encoding="utf-8").splitlines():
        if linea.startswith("Dialogue:"):
            p = linea.split(",", 9)
            ev.append((t(p[1]), t(p[2])))
    return ev


def silencios(video: Path) -> list[tuple[float, float]]:
    r = ejecutar(["ffmpeg", "-nostdin", "-hide_banner", "-i", str(video), "-vn",
                  "-af", "silencedetect=n=-35dB:d=0.1", "-f", "null", "-"])
    a = [float(x) for x in re.findall(r"silence_start: (-?[0-9.]+)", r.stderr)]
    b = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    return list(zip(a, b))


def revisar(video: Path, segmentos: list[dict], ass: Path, carpeta: Path, fuentes: Path,
            decision: dict) -> tuple[bool, list[str]]:
    carpeta.mkdir(parents=True, exist_ok=True)
    for viejo in carpeta.glob("*.png"):
        viejo.unlink()
    info = json.loads(ejecutar(["ffprobe", "-v", "error", "-show_entries",
                                "stream=codec_type,width,height,r_frame_rate:format=duration",
                                "-of", "json", str(video)]).stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    duracion = float(info["format"]["duration"])
    esperado = segmentos[-1]["salida_fin"]
    notas, bien = [], True

    def nota(ok: bool, texto: str) -> None:
        nonlocal bien
        bien = bien and ok
        notas.append(f"{'✓' if ok else '✗'} {texto}")

    nota(v["width"] == 1080 and v["height"] == 1920, f"Tamaño {v['width']}×{v['height']}")
    nota(v["r_frame_rate"] == f"{FPS}/1", f"Cuadros por segundo {v['r_frame_rate']}")
    nota(abs(duracion - esperado) < 0.1, f"Duración {duracion:.2f} s (corte: {esperado:.2f} s)")

    r = ejecutar(["ffmpeg", "-nostdin", "-hide_banner", "-i", str(video), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"])
    i_lufs = re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)
    pico = re.findall(r"Peak:\s+(-?[0-9.]+) dBFS", r.stderr)
    if i_lufs and pico:
        nota(abs(float(i_lufs[-1]) - LUFS) <= 1.0, f"Volumen {float(i_lufs[-1]):.1f} LUFS (objetivo {LUFS:.0f})")
        # Se apunta a −1,5 dBTP; el AAC puede subir unas décimas, así que el límite que se
        # comprueba es −1,0 dBTP, el que piden las plataformas.
        nota(float(pico[-1]) <= -1.0, f"Pico {float(pico[-1]):.1f} dBTP (máximo −1,0)")

    r = ejecutar(["ffmpeg", "-nostdin", "-hide_banner", "-i", str(video), "-an",
                  "-vf", "freezedetect=n=-60dB:d=1,blackdetect=d=0.2:pix_th=0.1", "-f", "null", "-"])
    # Una foto puesta a propósito (recursos.py) no cuenta como imagen congelada.
    fotos = [(x["inicio"] - 0.3, x["fin"] + 0.3) for x in plan_recursos(ass) if x["tipo"] == "imagen"]
    congelado = [inicio for inicio in re.findall(r"freeze_start: ([0-9.]+)", r.stderr)
                 if not any(a <= float(inicio) <= b for a, b in fotos)]
    negro = re.findall(r"black_duration:([0-9.]+)", r.stderr)
    nota(not congelado, "Sin imagen congelada más de 1 s" + (f" (hay {len(congelado)})" if congelado else ""))
    nota(not negro, "Sin fotogramas negros" + (f" (hay {len(negro)} tramos)" if negro else ""))

    eventos = eventos_ass(ass)
    sil = silencios(video)
    con_voz_sin_texto = []
    rutas = []
    for k, t in enumerate(instantes(segmentos, duracion), 1):
        ruta = carpeta / f"{k:02d}-{t:06.2f}s.png"
        ejecutar(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                  "-vf", color.filtro_vista_previa(decision["modo"], decision["transferencia"]), str(ruta)])
        rutas.append(ruta)
        hay_voz = not any(a <= t < b for a, b in sil)
        hay_texto = any(a <= t < b for a, b in eventos)
        if hay_voz and not hay_texto:
            con_voz_sin_texto.append(f"{t:.2f} s")
    nota(not con_voz_sin_texto, f"Subtítulo visible en los {len(rutas)} fotogramas clave con voz"
         + (f" (falta en {', '.join(con_voz_sin_texto)})" if con_voz_sin_texto else ""))

    # Hoja de contacto: 4 × 2 fotogramas con su segundo.
    fuente = (fuentes / "InterDisplay-Bold.ttf").as_posix().replace(":", "\\:")
    entradas_hoja, cadenas = [], []
    for k, ruta in enumerate(rutas):
        segundo = ruta.stem.split("-")[1]
        entradas_hoja += ["-i", str(ruta)]
        cadenas.append(f"[{k}:v]scale=270:480,drawtext=fontfile='{fuente}':text='{segundo}':x=10:y=10:"
                       f"fontsize=24:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=6[f{k}]")
    n = len(rutas)
    fila = (n + 1) // 2
    cadenas.append("".join(f"[f{k}]" for k in range(n)) + f"xstack=inputs={n}:layout="
                   + "|".join(f"{(k % fila) * 270}_{(k // fila) * 480}" for k in range(n)) + "[h]")
    hoja = carpeta / "hoja.png"
    r = ejecutar(["ffmpeg", "-v", "error", "-y", *entradas_hoja, "-filter_complex", ";".join(cadenas),
                  "-map", "[h]", "-frames:v", "1", str(hoja)])
    if r.returncode != 0:
        notas.append(f"· No se pudo montar la hoja de contacto: {r.stderr.strip()[-200:]}")
    return bien, notas


# ---------- principal ----------

def siguiente_version(entrega: Path) -> int:
    hechas = [int(m.group(1)) for p in entrega.glob("video-v*.mp4") if (m := re.match(r"video-v(\d+)\.mp4$", p.name))]
    return max(hechas, default=0) + 1


def main() -> int:
    p = argparse.ArgumentParser(description="Render final del vídeo cortado y subtitulado.")
    p.add_argument("carpeta", type=Path, help="carpeta del talento")
    p.add_argument("--sin-gpu", action="store_true", help="no usa la tarjeta gráfica aunque la haya")
    p.add_argument("--sin-revision", action="store_true", help="no saca fotogramas de revisión")
    args = p.parse_args()

    talento = args.carpeta.resolve()
    entrega = talento / "06_entrega"
    trabajo = entrega / "trabajo"
    for nombre in ("cortes.json", "subtitulos.ass", "subtitulos.srt"):
        if not (trabajo / nombre).exists():
            print(f"Falta {trabajo / nombre}. Antes ejecuta cortar.py y subtitulos.py.")
            return 2
    cortes = json.loads((trabajo / "cortes.json").read_text(encoding="utf-8"))
    segmentos = cortes["segmentos"]
    if "cuadros" not in segmentos[0]:
        print("cortes.json es de una versión anterior. Vuelve a ejecutar cortar.py y subtitulos.py.")
        return 2
    brutos = talento / "02_brutos"
    fuentes = letras.asegurar(todas_las_letras())
    ass = trabajo / "subtitulos.ass"

    n = siguiente_version(entrega)
    salida = entrega / f"video-v{n}.mp4"
    t0 = time.time()
    print(f"Render de la versión {n}: {len(segmentos)} tramos, {segmentos[-1]['salida_fin']:.1f} s.")
    print("  … Midiendo el volumen")
    medida = medir_volumen(segmentos, brutos, trabajo)
    print(f"    {float(medida['input_i']):.1f} LUFS → se lleva a {LUFS:.0f} LUFS")

    decision = color.decidir([brutos / c for c in sorted({s["clip"] for s in segmentos})])
    if decision["aviso"]:
        print(f"  · {decision['aviso']}")
    print("  · Color: " + (f"HDR ({decision['transferencia']}), como se grabó" if decision["modo"] == "hdr"
                          else "SDR, como se grabó"))
    script = trabajo / "render.filtro.txt"
    script.write_text(grafo_completo(segmentos, brutos, decision, ass, fuentes, filtro_volumen(medida)),
                      encoding="utf-8")
    hw = hardware(args.sin_gpu, decision)
    if hw.get("aviso"):
        print(f"  · La tarjeta no puede codificar: {hw['aviso']}")
    intentos = [hw] if hw["nombre"] == "procesador" else [hw, hardware(True, decision)]
    for intento in intentos:
        print(f"  … Renderizando con {intento['nombre']}")
        t1 = time.time()
        r = ejecutar(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin",
                      *entradas(segmentos, brutos, intento["entrada"]), *entradas_recursos(plan_recursos(ass)),
                      "-/filter_complex", str(script), "-map", "[v]", "-map", "[a]",
                      *intento["codec"], *color.etiquetas_salida(decision),
                      "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(salida)])
        if r.returncode == 0:
            print(f"    listo en {time.time() - t1:.0f} s")
            break
        salida.unlink(missing_ok=True)
        print(f"    no funcionó con {intento['nombre']}: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'sin detalle'}")
    else:
        script.unlink(missing_ok=True)
        print("No se pudo renderizar el vídeo.")
        return 1
    script.unlink(missing_ok=True)
    shutil.copyfile(trabajo / "subtitulos.srt", entrega / f"subtitulos-v{n}.srt")
    print(f"  {salida}")
    print(f"  {entrega / f'subtitulos-v{n}.srt'}")

    if args.sin_revision:
        return 0
    carpeta = trabajo / "revision"
    bien, notas = revisar(salida, segmentos, ass, carpeta, fuentes, decision)
    informe = [f"# Revisión · video-v{n}.mp4", "", *[f"- {x}" for x in notas], "",
               f"Hoja de contacto: `revision/hoja.png` · Tiempo total: {time.time() - t0:.0f} s", ""]
    (carpeta / "revision.md").write_text("\n".join(informe), encoding="utf-8")
    print("\nRevisión:")
    for x in notas:
        print(f"  {x}")
    print(f"  Hoja de contacto: {carpeta / 'hoja.png'}")
    print("\n" + ("Pasa la revisión automática. Mira la hoja de contacto antes de entregar."
                  if bien else "No pasa la revisión: arregla lo marcado con ✗ antes de entregar."))
    return 0 if bien else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as e:
        print(f"No se pudo renderizar: {e}")
        sys.exit(1)
