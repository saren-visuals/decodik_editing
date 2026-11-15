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

## Corte automático

```
uv run scripts/cortar.py <carpeta del talento> [--pausa-max 0.3] [--sin-video] [--rapido]
```

- Lee `06_entrega/trabajo/transcripcion.json` y escribe `cortes.json`, `cortes.md` (qué se queda y qué se quita, con el motivo) y `corte.mp4` (borrador vertical 1080×1920 sin subtítulos).
- Quita muletillas («eh», «em», «mmm»), la primera de dos palabras iguales seguidas y el silencio de principio y final de cada frase, y acorta las pausas de más de `--pausa-max` segundos.
- **Tomas repetidas:** si una frase se dice más de una vez (o hay un arranque en falso), se queda la **mejor toma**: la que Whisper oye con más claridad y está más completa, con menos pausas largas y muletillas. Las notas de cada toma quedan en `cortes.json`.
- Las uniones se anclan al sonido real (silencios de ffmpeg desde 50 ms): unos 60 ms de aire antes de que empiece la voz y después de que acabe, para no cortar sílabas.
- Los vídeos HDR del iPhone (HLG) se pasan a color normal (SDR, BT.709) para que no salgan lavados.
- Antes de dar el corte por bueno, el talento lo escucha.

## Subtítulos

```
uv run scripts/subtitulos.py <carpeta del talento> [--max-palabras 4] [--color-activa FFD400] [--sin-video]
```

- Lee `transcripcion.json` y `cortes.json`, pasa cada palabra al tiempo del vídeo cortado y escribe `subtitulos.ass` (con estilo), `subtitulos.srt` (para entregar) y `subtitulado.mp4` (el corte con los subtítulos pintados, para revisarlo).
- **Estilo «nativo + palabra a palabra»:** blanco en negrita con contorno negro, la palabra que suena en amarillo (`--color-activa`), sin puntos ni comas al final.
- **Bloques de 1 a 4 palabras visibles** («Eileen Gu» cuenta como dos). Se abre bloque nuevo en la puntuación y en las pausas. Ningún bloque dura menos de 4 cuadros.
- **Posición:** centrado, con la base al 66 % de la altura y 130 px de margen a cada lado: dentro de la zona segura de TikTok y Reels (fuera de la descripción de abajo y de los botones de la derecha).
- **Letra:** Montserrat ExtraBold (OFL). Se descarga del repositorio oficial la primera vez en `~/.cache/decodik/fuentes/`. Ver `CREDITOS.md`.
- Los nombres salen como quedaron corregidos en la transcripción (`--nombres` de `transcribir.py`).
