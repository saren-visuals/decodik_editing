"""Transcribe palabra a palabra con faster-whisper.

Uso:
  python transcribir.py --audio 06_trabajo/audio16k.wav --out 06_trabajo/palabras-bruto.json
                        [--idioma es] [--vocab "Decodik, Taekwondo"] [--modelo auto|large-v3|medium|small]
Salida: lista de {"w", "start", "end", "p"}. p < 0.6 = revisar.
Guarda también el vocabulario en vocab.txt (junto a --out) para que cortar.py lo reutilice.
"""
import argparse
import time
from pathlib import Path

from comun import aviso, escribir_json


def elegir(modelo):
    dispositivo, tipo = "cpu", "int8"
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            dispositivo, tipo = "cuda", "float16"
    except Exception:
        pass
    if modelo == "auto":
        modelo = "large-v3" if dispositivo == "cuda" else "medium"
    return modelo, dispositivo, tipo


def cargar_audio(ruta):
    """Audio mono 16 kHz float32 leído con ffmpeg. Así faster-whisper no usa PyAV,
    que en versiones nuevas (15+) rompe faster-whisper <= 1.2 ('metadata_errors')."""
    from audio import leer_mono
    return leer_mono(ruta)


def transcribir(ruta_audio, idioma="es", vocab="", modelo="auto"):
    from faster_whisper import WhisperModel

    nombre, disp, tipo = elegir(modelo)
    aviso(f"Transcribiendo con Whisper {nombre} en {disp.upper()} (la primera vez descarga el modelo)…")
    try:
        m = WhisperModel(nombre, device=disp, compute_type=tipo)
    except Exception as e:  # CUDA sin cuDNN, etc.
        aviso(f"No se pudo usar {disp} ({e}); sigo en CPU.")
        disp = "cpu"
        m = WhisperModel(nombre, device="cpu", compute_type="int8")
    prompt = f"Vocabulario: {vocab}." if vocab else None
    audio = cargar_audio(ruta_audio)

    def pasar(modelo_w):
        segmentos, _ = modelo_w.transcribe(audio, language=idioma, word_timestamps=True,
                                           condition_on_previous_text=False, initial_prompt=prompt,
                                           vad_filter=False)
        salida = []
        for s in segmentos:
            for w in s.words or []:
                texto = w.word.strip()
                if texto:
                    salida.append({"w": texto, "start": round(w.start, 3), "end": round(w.end, 3),
                                   "p": round(w.probability, 2)})
        return salida

    try:
        return pasar(m)
    except RuntimeError as e:  # falta cuBLAS/cuDNN: falla al transcribir, no al cargar
        if disp == "cpu":
            raise
        nombre_cpu = "medium" if modelo == "auto" else nombre
        aviso(f"La tarjeta no está lista ({e}): faltan las librerías CUDA de NVIDIA (cuBLAS/cuDNN). "
              f"Sigo en CPU con Whisper {nombre_cpu} (más lento, mismo resultado).")
        del m
        return pasar(WhisperModel(nombre_cpu, device="cpu", compute_type="int8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--idioma", default="es")
    ap.add_argument("--vocab", default="")
    ap.add_argument("--modelo", default="auto")
    a = ap.parse_args()

    t0 = time.time()
    palabras = transcribir(a.audio, a.idioma, a.vocab, a.modelo)
    escribir_json(a.out, palabras)
    if a.vocab:
        (Path(a.out).parent / "vocab.txt").write_text(a.vocab, encoding="utf-8")
    dudosas = [p["w"] for p in palabras if p["p"] < 0.6]
    aviso(f"{len(palabras)} palabras en {time.time() - t0:.0f} s. Dudosas ({len(dudosas)}): {', '.join(dudosas[:30])}")


if __name__ == "__main__":
    main()
