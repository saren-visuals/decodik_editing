# Protocolo de corte (todos los niveles, sin saltarse pasos)

Cortar solo silencios deja lo que más se nota: muletillas, repeticiones y frases empezadas dos veces. Este protocolo quita todo eso sin comerse palabras.

## 0. Preparar (lo hace `preparar.py`)
- Pasa a **30 fps** (si no, los gráficos salen a cámara lenta en tomas de 60 o 120 fps).
- Vertical 1080×1920 (o 2160×3840 en avanzado 4K).
- Extrae `audio16k.wav` (para transcribir) y `audio48k.wav` (para la mezcla final).
- Si la voz está muy baja, añade `--normalizar` (sube el volumen antes de cortar).

## 1. Transcribir
```bash
python "{SKILL}/scripts/transcribir.py" --audio 06_trabajo/audio16k.wav --out 06_trabajo/palabras-bruto.json --vocab "<nombres, marcas, deporte, términos técnicos>"
```
- Pon en `--vocab` los nombres propios, la marca, el deporte y los términos que aparezcan (por ejemplo «Decodik, Taekwondo, UGC, Claude Code»). Sin esto, Whisper los escribe mal.
- Palabras con probabilidad < 0,6 quedan marcadas para revisar.
- Guarda el vocabulario en `vocab.txt`; `cortar.py` lo reutiliza al comprobar el corte.
- Si la tarjeta NVIDIA no tiene las librerías CUDA (cuBLAS), sigue sola en CPU: no es un error, solo tarda algo más.

## 2. Analizar
```bash
python "{SKILL}/scripts/analizar.py" --palabras 06_trabajo/palabras-bruto.json --audio 06_trabajo/audio48k.wav --pausa-max <0.4 natural | 0.25 ajustado> --out 06_trabajo/propuesta.json
```
Cruza tres fuentes: pausas entre palabras, silencios reales del audio y repeticiones/muletillas. Escribe una propuesta de tramos que se quedan (`propuesta.json`) y un informe legible (`propuesta.md`).
- **Las pausas se miden en el audio, no en las palabras.** Whisper estira palabras por encima de los silencios («en» de 4 s, 1 s de silencio pegado a «subtítulos»), así que el script parte cada tramo por cualquier silencio real de más de `--pausa-max`, también dentro de una frase (tras «uno», «dos», «tres»…). Respiraciones y roces flojos no cuentan como voz.
- **Natural (0,4)** deja respirar; **ajustado (0,25)** es ritmo de reel. Si el usuario ya tiene una regla en `_mi-estilo/reglas.md`, úsala sin preguntar.
- En tomas repetidas tacha la primera versión entera y conserva la última **desde su primera palabra** («~~el truco está en~~ el truco está en darle…»).

## 3. Leer como un espectador (lo haces tú, Claude)
Lee la transcripción **entera** como alguien que lo ve por primera vez y añade lo que el script no ve:
- Frases dichas dos veces con otras palabras → se queda **la última** (suele ser la buena).
- Arranques en falso («lo que… lo que quiero decir»).
- Muletillas de contexto: «o sea», «este», «no sé», «¿vale?», «bueno» al principio de frase.
- **No quites** contenido, nombres, cifras ni la llamada a la acción.
- **Comprueba el arranque de cada toma buena**: que su primera palabra no salga tachada. Si el script se equivoca, ajusta el tramo en `keep.json`.
- Mira los tiempos de la propuesta, no solo el texto: una palabra con duración 0 o de varios segundos es un error de tiempos de Whisper, no algo que cortar.

## 4. Enseñar y esperar
Enseña al usuario: la transcripción con lo que se quita ~~tachado~~, la lista de palabras dudosas y la duración antes/después. Pregunta si hay palabras mal escritas y si quiere conservar algo. **Espera su OK.**

## 5. Cortar
Escribe `06_trabajo/keep.json` (tramos que se quedan) a partir de la propuesta con las correcciones, y las correcciones de texto en `06_trabajo/correcciones.json` (`{"mal": "bien"}`).
```bash
python "{SKILL}/scripts/cortar.py" --trabajo 06_trabajo --keep 06_trabajo/keep.json --correcciones 06_trabajo/correcciones.json
```
El script ajusta cada borde al punto más silencioso cercano, deja ~0,08 s de aire, hace fundidos de 12 ms (sin chasquidos) y genera `cortado.mp4`, `voz_cortada.wav` y `preview.mp4`.
Después **vuelve a transcribir el audio cortado**: `palabras.json` sale de esa escucha (tiempos exactos y frases completas para los subtítulos) con el texto revisado y las correcciones aplicadas. Las correcciones valen aunque la palabra lleve puntuación o mayúscula. No edites `palabras.json` a mano: corrige en `correcciones.json` y repite.

## 6. Comprobar
- `⚠️ no se oyen en el corte` → faltan de verdad en el audio (no es una sospecha por tiempos). Si no las quitaste a propósito (p. ej. una muletilla), **amplía su tramo en `keep.json` y repite antes de seguir.**
- `ℹ️ se oyen palabras que no estaban en la propuesta` → suele ser un «y» o «vale» que se coló de una toma falsa, o una palabra que Whisper no captó la primera vez. Escucha ese punto en `preview.mp4`; si sobra, recorta el tramo.
- Regla de control: un tramo de más de 6 s sin ningún corte en un vídeo con muletillas suele ser un corte no hecho; revísalo.
- En revisión guiada, enseña `preview.mp4` y espera «siguiente».

## Atajos de nota
- «Has cortado demasiado en X» → amplía ese tramo en `keep.json` y repite el paso 5.
- «Se come el final de la palabra» → repite `analizar.py` con `--aire 0.12` y vuelve a cortar.
