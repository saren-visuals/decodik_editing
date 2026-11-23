# Cambios · decodik-editor

## 1.1 · 23-11-2026
**Corte**
- Storyboard visual de la propuesta de corte (`scripts/storyboard_corte.py`): escenas con fotogramas, cortes con su motivo, forma de la voz y botones para ver cada trozo o «así quedaría». Se enseña en el paso 4 del protocolo, antes del OK. Lecciones afectadas: las que enseñan la propuesta de corte.

## 1.0 · 22-11-2026 · versión congelada para los alumnos
Primera versión estable. Cualquier cambio después de grabar las lecciones va a la 1.1, revisando qué lecciones afecta.

**Corte**
- Las pausas se miden en el audio, también dentro de las frases. Corte natural (0,4 s) o ajustado (0,25 s).
- Las tomas repetidas se quitan sin tachar el principio de la toma buena.
- Tras cortar, se vuelve a transcribir el vídeo cortado: tiempos exactos para los subtítulos y aviso solo si falta una palabra de verdad.

**Subtítulos y estilos**
- Minimal pasa a estilo TikTok: 1-2 palabras, blanco con contorno negro, sin palabra clave, sin puntuación y sin animación.
- Todos los estilos centran subtítulos y gráficos.

**Formatos y gráficos**
- Pantalla dividida y recuadro: con capturas o vídeos reales si los hay; si no, animaciones explicativas (`scripts/motions.py`).

**Imagen y sonido**
- HDR y Dolby Vision del iPhone pasan a SDR automáticamente.
- Color de cine graduado en RGB, ahora también en Windows.
- La skill no incluye música ni efectos: los aporta el usuario (suyos, de la marca o libres de derechos que descarga él).

**Equipo**
- Funciona en Windows con consola en cp1252, PyAV 15+, ffmpeg 7-9 y tarjetas NVIDIA sin librerías CUDA (sigue en CPU).
- El modelo de recorte (GPL-3.0) no va en el paquete: se descarga del repositorio oficial la primera vez, con permiso.
