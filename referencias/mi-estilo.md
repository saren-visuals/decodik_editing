# Crear el estilo propio del talento

Objetivo: que Claude edite siempre como el talento quiere. El estilo cabe en una lista con valores medibles.

Si lo que quiere es editar **como en un vídeo concreto** y guardarlo con nombre, sigue `{SKILL}/referencias/replicar-estilo.md`.

Hay dos caminos. Pregunta cuál prefiere (AskUserQuestion): **con referencias** (recomendado si tiene vídeos que le gustan) o **desde cero con preguntas**.

## Con referencias
1. Pide **3 vídeos o capturas** que le gusten de verdad (suyos o de referencia) en `_mi-estilo/referencias/`. Solo vídeos propios o capturas de pantalla: **inspírate, no copies contenido ajeno**.
2. Extrae fotogramas (`ffmpeg -i ref.mp4 -vf fps=1 ref_%02d.jpg`) y míralos. Si es un vídeo, transcribe un trozo para ver el ritmo de corte y de subtítulos.
3. Describe en una tabla lo que ves: subtítulos (fuente aproximada, tamaño, color, posición, cuántas palabras), palabra clave, cada cuántos segundos cambia el plano, tipo de gráficos, zooms, transiciones, música y efectos.
4. Haz 4-6 preguntas para lo que no se ve: colores de su marca, logo, tipografías, qué odia ver.
5. Escribe `_mi-estilo/estilo.json` con **la misma estructura que `{SKILL}/estilos/espacial.json`** (o `minimal.json` en básico), con valores medibles (HEX, px, s, dB), y `_mi-estilo/reglas.md` con las reglas en frases.
6. Pruébalo en el próximo vídeo y ajústalo con sus notas.

## Desde cero con preguntas
Haz 6-8 preguntas con opciones, en dos tandas: ritmo (natural / rápido), subtítulos (palabra a palabra / por frases, mayúsculas sí o no), color de la palabra clave (de su marca o de la paleta Decodik), cantidad de gráficos, tipo de música, efectos sí o no, y qué no quiere ver nunca. Con las respuestas, escribe `estilo.json` y `reglas.md` igual que arriba, partiendo del estilo Decodik más parecido.

## Logo, colores y tipografías
Si los tiene, que los deje en `_mi-estilo/logos/` y `_mi-estilo/tipografias/`, y los colores en HEX. Mandan sobre la paleta Decodik.

A partir de ahí, en el flujo B, `_mi-estilo/estilo.json` aparece como primera opción.
