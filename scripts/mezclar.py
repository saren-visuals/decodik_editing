"""Pasada de sonido: voz limpia + música con ducking + efectos + máster a −14 LUFS, y unión con el vídeo.

Uso:
  python mezclar.py --video <vídeo> --voz 06_trabajo/voz_cortada.wav --out 07_entrega/<tema>.mp4
                    [--musica 05_musica/pista.mp3] [--musica-db -12] [--efectos 06_trabajo/efectos.json]
efectos.json: [{"archivo": "05_musica/efectos/whoosh.wav", "t": 3.42, "db": -22}]
"""
import argparse
from pathlib import Path

from comun import aviso, ffmpeg, leer_json, medir_volumen as medir, sondear

VOZ = "highpass=f=80,afftdn=nf=-30:nr=8,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=140:makeup=2"
OBJ_I, OBJ_TP, OBJ_LRA = -14, -1.5, 11


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--voz", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--musica")
    ap.add_argument("--musica-db", type=float, default=-12, help="Música respecto a la voz, en dB")
    ap.add_argument("--efectos")
    a = ap.parse_args()

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.parent / "_mezcla.wav"
    dur = sondear(a.video)["duracion"]

    entradas = ["-i", a.voz]
    filtros = [f"[0:a]{VOZ},loudnorm=I={OBJ_I}:TP={OBJ_TP},aresample=48000,asplit=2[voz][vozsc]"]
    mezcla = ["[voz]"]
    n = 1
    if a.musica:
        entradas += ["-stream_loop", "-1", "-i", a.musica]
        filtros.append(
            f"[{n}:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=mono,"
            f"loudnorm=I={OBJ_I + a.musica_db}:TP=-6,afade=t=in:d=0.6,afade=t=out:st={max(0, dur - 1.5):.3f}:d=1.5[mus];"
            f"[mus][vozsc]sidechaincompress=threshold=0.03:ratio=4:attack=40:release=450:makeup=1[musd]")
        mezcla.append("[musd]")
        n += 1
    else:
        filtros[0] = filtros[0].replace(",asplit=2[voz][vozsc]", "[voz]")
    if a.efectos:
        for e in leer_json(a.efectos):
            entradas += ["-i", e["archivo"]]
            ms = int(round(e["t"] * 1000))
            filtros.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=mono,volume={e.get('db', -22)}dB,"
                           f"adelay={ms}|{ms}[e{n}]")
            mezcla.append(f"[e{n}]")
            n += 1
    if len(mezcla) > 1:
        filtros.append(f"{''.join(mezcla)}amix=inputs={len(mezcla)}:normalize=0:duration=first[mix]")
    else:
        filtros.append("[voz]anull[mix]")
    ffmpeg([*entradas, "-filter_complex", ";".join(filtros), "-map", "[mix]", "-t", f"{dur:.3f}",
            "-ar", "48000", "-c:a", "pcm_s24le", str(tmp)])

    # Máster en dos pasadas
    m = medir(tmp)
    ln = (f"loudnorm=I={OBJ_I}:TP={OBJ_TP}:LRA={OBJ_LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    ffmpeg(["-i", a.video, "-i", str(tmp), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", f"{ln},aresample=48000",
            "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", str(out)])
    tmp.unlink(missing_ok=True)

    f = medir(out)
    aviso(f"Máster: {float(f['input_i']):.1f} LUFS (objetivo {OBJ_I}), pico {float(f['input_tp']):.1f} dB. → {out}")


if __name__ == "__main__":
    main()
