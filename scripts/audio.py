"""Lectura de audio y energía (RMS) con ffmpeg + numpy."""
import subprocess

import numpy as np

from comun import herramienta

RATE = 16000
VENTANA = 0.01  # 10 ms


def leer_mono(ruta, rate=RATE):
    r = subprocess.run([herramienta("ffmpeg"), "-v", "error", "-i", str(ruta), "-ac", "1", "-ar", str(rate),
                        "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32)


def energia_db(muestras, rate=RATE, ventana=VENTANA):
    """dB RMS cada `ventana` segundos."""
    n = int(rate * ventana)
    k = len(muestras) // n
    if k == 0:
        return np.array([-90.0])
    bloques = muestras[: k * n].reshape(k, n)
    rms = np.sqrt(np.mean(bloques ** 2, axis=1) + 1e-12)
    return 20 * np.log10(rms + 1e-12)


def umbral_silencio(db):
    """Umbral adaptativo: entre el ruido de fondo y la voz.
    Con percentil 10/80 y 0,35 quedaba pegado al ruido de la sala (respiraciones a −48 dB
    contaban como voz y no se quitaban pausas). 20/90 y 0,45 lo deja a ~−43 dB en una toma
    típica de móvil: separa pausa de voz sin comerse consonantes suaves."""
    suelo = np.percentile(db, 20)
    voz = np.percentile(db, 90)
    return max(suelo + 0.45 * (voz - suelo), -50.0)


def punto_mas_silencioso(db, t_ini, t_fin, ventana=VENTANA):
    i0, i1 = max(0, int(t_ini / ventana)), min(len(db), int(t_fin / ventana) + 1)
    if i1 <= i0:
        return (t_ini + t_fin) / 2
    return (i0 + int(np.argmin(db[i0:i1]))) * ventana + ventana / 2
