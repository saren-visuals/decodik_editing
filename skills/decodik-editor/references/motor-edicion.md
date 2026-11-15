# Motor de edición

Lo que necesita el equipo del talento para que `decodik-editor` edite vídeo, y cómo comprobarlo.

**Stack:** ffmpeg (corte, montaje, subtítulos y render) + whisper (transcripción con tiempos por palabra, con faster-whisper). Sin Remotion.

## Qué hay que instalar

| Programa | Para qué | Windows | Mac | Linux |
|---|---|---|---|---|
| **ffmpeg** (con ffprobe) | Cortar, montar, subtitular y renderizar | `winget install Gyan.FFmpeg` | `brew install ffmpeg` | `sudo apt install ffmpeg` |
| **uv** | Trae Python y las librerías de transcripción. No hace falta instalar Python aparte | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | igual que Mac |

En Windows, después de instalar algo hay que **cerrar y volver a abrir** Claude (o la terminal) para que lo encuentre.

No hace falta ninguna clave de API. Todo funciona en el equipo del talento, sin coste.

## Comprobar el equipo

Antes del primer vídeo, o si algo falla:

```
uv run scripts/revisar_equipo.py --whisper --prueba 06_entrega
```

- Responde con ✓ y ✗, y debajo de cada ✗ el comando que lo arregla.
- `--whisper` prepara la transcripción. La primera vez descarga Python 3.12 y faster-whisper (unos minutos con internet).
- `--prueba 06_entrega` renderiza `prueba-motor.mp4`: 5 s en vertical 1080×1920 con audio. Si sale, el motor funciona.
- Termina con «Todo listo para editar.» (código 0) o «Falta algo…» (código 1).

**Cómo se lo cuentas al talento:** no le enseñes la salida entera. Dile en una línea si está todo listo; si falta algo, dale solo el comando del ✗, explica que lo pegue en la terminal y espera a que te diga «hecho».

## Lo que tarda

- **La primera vez:** descarga las librerías (aquí) y, en el primer vídeo, el modelo de voz (cientos de MB). Avisa al talento antes para que no piense que se ha colgado.
- **Después:** no descarga nada.
- Sin tarjeta gráfica NVIDIA se transcribe con el procesador: más lento en vídeos largos, pero funciona igual.

## Licencias

- ffmpeg: LGPL/GPL según la compilación.
- faster-whisper: MIT. Modelos Whisper de OpenAI: MIT.
- uv: MIT / Apache-2.0.

Se instalan desde sus fuentes oficiales; el repo no incluye ninguno.

## Transcribir los brutos

```
uv run scripts/transcribir.py <carpeta del talento> --nombres "Nombre Propio, Marca, Producto"
```

- Busca los vídeos en `02_brutos/` (también en subcarpetas) en orden natural: «Clip 2» va antes que «Clip 10».
- Escribe `06_entrega/trabajo/transcripcion.json` (tiempos por palabra) y `transcripcion.md` (para leer).
- `--nombres`: pon los nombres propios, marcas y productos del vídeo. Se corrigen después de transcribir («Eilengu» → «Eileen Gu») y lo que oyó Whisper queda en `p_whisper`. No se le pasan a Whisper como pista porque así a veces se salta una toma repetida.
- Whisper suele adelantar la primera palabra después de una pausa. Esos inicios se corrigen con la detección de silencios de ffmpeg; el valor original queda en `inicio_whisper`.
- Si un clip no ha cambiado, no se vuelve a transcribir. `--forzar` lo obliga.
- Tarda unos 5 s por clip corto en un portátil sin tarjeta gráfica; la primera vez descarga el modelo `large-v3-turbo` (~1,6 GB).
