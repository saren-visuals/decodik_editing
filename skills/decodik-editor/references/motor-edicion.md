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
- **El color no se toca** (ver «Color» más abajo).
- Antes de dar el corte por bueno, el talento lo escucha.

## Subtítulos

```
uv run scripts/subtitulos.py <carpeta del vídeo> [--estilo clave] [--claves claves.json] [--color-clave HEX] [--max-palabras N] [--sin-video]
```

- Lee `transcripcion.json` y `cortes.json`, pasa cada palabra al tiempo del vídeo cortado y escribe `subtitulos.ass` (con estilo), `subtitulos.srt` (para entregar) y `subtitulado.mp4` (el corte con los subtítulos pintados, para revisarlo).
- **8 estilos** (`clave` por defecto, `serif`, `frase`, `impacto`, `caja`, `condensada`, `mixta`, `minimo`) y **palabras clave** desde `claves.json`: ver `references/estilos-subtitulos.md`.
- **Bloques** según el estilo (de 1-3 palabras a frases enteras), sin terminar en palabras de enlace. Ningún bloque dura menos de 4 cuadros. Base al 66 % de la altura, dentro de la zona segura de TikTok y Reels.
- **Letras:** Inter, Inter Display y Figtree (OFL), que se descargan de su repositorio oficial la primera vez en `~/.cache/decodik/fuentes/` (`scripts/fuentes.py`; Inter viene en un zip de ~34 MB). `serif` usa de momento Georgia, del sistema. Ver `CREDITOS.md`.
- Los nombres salen como quedaron corregidos en la transcripción (`--nombres` de `transcribir.py`).

## Gancho, cifras y CTA

```
uv run scripts/textos.py <carpeta del vídeo> [--color-clave HEX]
```

- Lee `textos.json` (lo propone Claude y lo aprueba el talento; ver `references/textos-pantalla.md`) y escribe `textos.ass` y `textos-huecos.json`.
- **Gancho** arriba (12 % de la altura, sin tapar los ojos) desde el fotograma 0 hasta el final de la primera frase; **cifras** de 380 px debajo de la cara con un golpe de escala al decirlas (mientras se ven, el subtítulo se aparta); **CTA** arriba los últimos 2,5 s con un fundido.
- `render.py` los pinta encima de los subtítulos si existe `textos.ass`.

## Recursos en pantalla

```
uv run scripts/recursos.py <carpeta del vídeo>
```

- Lee `recursos.json` (propuesto por Claude, aprobado por el talento; ver `references/recursos-pantalla.md`), ancla cada recurso de `03_recursos/` a la palabra en que se nombra y escribe `recursos-plan.json`.
- **Completo:** el recurso cubre los 1080×1920. **Tarjeta:** como mucho 820×440 px, esquinas redondeadas, arriba al 38 % de la altura; entra subiendo 40 px con fundido de 0,18 s y sale con fundido.
- Las imágenes se preparan con numpy (dependencia de `uv run`): escala, esquinas con transparencia y, si el vídeo es HDR, paso a BT.2020 + HLG con el blanco de referencia. Los clips se usan sin sonido y tienen que tener el mismo color que el vídeo.
- `render.py` pone los recursos encima del vídeo y, encima de todo, subtítulos y textos.

## Render final y revisión

```
uv run scripts/render.py <carpeta del talento> [--sin-gpu] [--sin-revision]
```

- Hace el vídeo final **en una sola pasada desde los brutos**: corte, subtítulos y volumen, con el color tal como se grabó.
- Entrega en `06_entrega/`: `video-vN.mp4` (1080×1920, 30 fps, AAC; HEVC 10 bits si es HDR, H.264 si es SDR) y `subtitulos-vN.srt`. N es la primera versión libre: nunca se sobrescribe una entrega.
- **Volumen:** se mide primero y se lleva a −14 LUFS con pico máximo de −1,5 dBTP (el que usan TikTok, Instagram y YouTube).
- **Hardware:** con tarjeta NVIDIA lee el vídeo con la tarjeta y, si el controlador lo permite, también codifica con ella; en Mac usa VideoToolbox. Antes de usar el codificador de la tarjeta hace una prueba de 0,1 s; si falla (por ejemplo, controlador NVIDIA anterior al 610), codifica con el procesador y lo avisa. `--sin-gpu` lo fuerza todo al procesador.
- **Revisión automática antes de entregar** (`06_entrega/trabajo/revision/`): tamaño, cuadros por segundo, duración, volumen y pico, sin imagen congelada ni fotogramas negros, y subtítulo visible en los fotogramas clave con voz. Saca 8 fotogramas (primero, último y cambios de tramo) y una hoja de contacto `hoja.png`.
- **Tú (Claude) miras la hoja de contacto** antes de decir que el vídeo está listo: que el subtítulo se lea, no tape la cara y no haya nada raro en la imagen. Si la revisión marca un ✗, no se entrega: se arregla y se vuelve a renderizar.

## Color

**El color de los brutos no se toca** (decisión de Santiago, 2026-11-15). Lo decide `scripts/color.py` para los tres scripts:

- **Brutos HDR** (los iPhone graban en HLG, a veces con Dolby Vision) → el vídeo sale en **HDR**: HEVC 10 bits con las mismas etiquetas de color (BT.2020, HLG). Instagram y TikTok aceptan HDR. Se pierde la capa Dolby Vision, pero se conserva el HLG que va debajo.
- **Brutos SDR** (la mayoría de Android y cámaras) → sale **SDR**: H.264, BT.709.
- **Mezcla de HDR y SDR** → los HDR se pasan a SDR para poder unirlos, y se avisa. Es el único caso en que se convierte.
- **Texto en HDR:** el blanco va al «blanco de referencia» de HLG (75 % de la señal), no al 100 %, para que no deslumbre más que el vídeo. Los colores (el amarillo de la palabra activa) se convierten de sRGB a BT.2020 + HLG para que se vean igual que en SDR.
- **Hoja de revisión:** un PNG no guarda HDR, así que los fotogramas de revisión se pasan a SDR solo para mirarlos. El vídeo entregado no cambia.
- En HDR el render tarda más (HEVC 10 bits): unos 106 s para un vídeo de 61 s en un portátil, frente a unos 46 s en SDR.
