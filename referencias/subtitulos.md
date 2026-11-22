# Pasada de subtítulos

## 1. Trocear (lo haces tú, Claude)
Escribe `06_trabajo/frases.txt`: **una frase por línea**, trozos de 1-3 palabras separados con `|` (el máximo lo da `palabras_max` del estilo) y **una palabra clave por frase** entre `*asteriscos*`.
```
Hoy te enseño | a *editar* | con Claude
sin abrir | ningún *editor*
```
- El texto debe coincidir palabra por palabra con `palabras.json` (el script avisa si no).
- Palabra clave: la que da sentido a la frase (cifras, el beneficio, el nombre del producto, el verbo de acción). Nunca artículos ni muletillas.
- Corta los trozos donde se respira al leer, no cada 3 palabras a ciegas.

### Estilo Minimal (TikTok): sin palabra clave
Minimal tiene `"palabra_clave": false`, `"puntuacion": false` (el script quita puntos, comas e interrogaciones al generar), `palabras_max: 2` y, como todos los estilos, subtítulos **centrados** (x = 540). En `frases.txt`:
- **No marques `*palabras clave*`** (si quedara alguna, el script la ignora).
- Trozos de **1 o 2 palabras que tengan sentido juntas**: `en cinco | minutos`, `sin tocar | un editor`, `te mando | el skill`.
- Con texto centrado, un trozo de más de ~480 px (unos 15 caracteres a 72 px) invade la columna de botones de TikTok: pártelo si se puede.
- **Nunca** una palabra de enlace suelta al final de un trozo (`un`, `el`, `la`, `de`, `y`, `en`, `que`, `a`): va con la palabra que la sigue.
```
Edité | este vídeo | en cinco | minutos | sin tocar | un editor
```

## 2. Aprobar
Enseña la lista de palabras clave (una por frase) y **espera el OK**, en revisión guiada y en rápida.
**Con Minimal no hay palabras clave: no pidas esta aprobación** y pasa directamente a generar.

## 3. Generar
```bash
python "{SKILL}/scripts/subtitulos.py" --palabras 06_trabajo/palabras.json --frases 06_trabajo/frases.txt --estilo "{SKILL}/estilos/<id>.json" --out 06_trabajo/subtitulos
```
Genera `subtitulos.json` (trozos con tiempos, para HyperFrames), `subtitulos.ass` (con el estilo, para quemar con ffmpeg) y `subtitulos.srt` (texto plano para la entrega).
- Cada trozo dura hasta que empieza el siguiente, con +0,3 s de cola como mucho y nunca menos de `duracion_minima_s`.
- Con `--fuentes <carpeta>` se usan las tipografías de la marca o del talento.

## 4. Montar
- **Básico:** quema el `.ass` directamente:
  ```bash
  python "{SKILL}/scripts/quemar_subtitulos.py" --video 06_trabajo/cortado.mp4 --ass 06_trabajo/subtitulos/subtitulos.ass --out 06_trabajo/con_subtitulos.mp4
  ```
- **Intermedio y avanzado:** los subtítulos se dibujan en HyperFrames junto con los gráficos (ver `graficos.md`), a partir de `subtitulos.json`, con la entrada que diga el estilo. **Textos sin rebote.**
- Oculta el subtítulo cuando un gráfico dice lo mismo en ese momento.
