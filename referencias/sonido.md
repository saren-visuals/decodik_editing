# Pasada de sonido

## Voz (todos los niveles)
Se mezcla desde `voz_cortada.wav` (sacada del WAV original, no del audio comprimido del vídeo) con una cadena suave: filtro de graves a 80 Hz, reducción de ruido ligera y compresión 2,5:1. Lo hace `mezclar.py`.

## Música (intermedio y avanzado)
La skill **no trae música ni la genera**: la pone el usuario. Tres opciones, por este orden de preferencia en vídeos para marcas:
1. **La de la marca o la del usuario** (`05_musica/`), con licencia.
2. **Música libre de derechos que el usuario descarga él mismo**:
   - **Pixabay Music** (recomendada): gratis, sin atribución, vale para TikTok, Instagram y YouTube.
   - **Biblioteca de audio de YouTube** (YouTube Studio → Biblioteca de audio): buena para Shorts; algunas pistas piden atribución en la descripción, avísalo.
   Puedes buscar y proponer 3 pistas con su enlace (energía para Golpe y Espacial, tranquila para Editorial y Premium), pero **la descarga la hace el usuario** y la guarda en `05_musica/`. Nunca descargues música por tu cuenta.
3. **Sin música**: explica que puede añadirla desde la biblioteca de la red al publicar.

Se mezcla 12 dB por debajo de la voz, con **ducking** (baja sola cuando habla), entrada de 0,6 s y fundido final de 1,5 s. Si la pista es más corta que el vídeo, dilo y propón otra; si es más larga, se recorta.

## Efectos (intermedio y avanzado)
También los aporta el usuario (por ejemplo, efectos libres de Pixabay: whoosh, clic, impacto). Pídele que los guarde en `05_musica/efectos/` y conviértelos a WAV con estos nombres para que los encuentre el plan:
```bash
ffmpeg -i "<descargado>.mp3" -ar 48000 -ac 2 "05_musica/efectos/whoosh.wav"
```
Nombres: `whoosh`, `impact`, `riser`, `uiclick`, `glitch`, `braaam`. Si falta alguno, ese evento va sin efecto (no lo inventes).

- Solo los que diga `sonido.efectos` del estilo. Uno por evento visual, 20-40 ms antes del visual.
- Niveles orientativos: `impact` −16 dB en el gancho, `whoosh` −21 dB en tarjetas, `uiclick` −22 dB en checks, `riser` −24 dB antes de un momento grande, `braaam` −20 dB en el cierre.
- Lista en `06_trabajo/efectos.json`:
  `[{"archivo": "05_musica/efectos/impact.wav", "t": 0.0, "db": -16}, {"archivo": "05_musica/efectos/whoosh.wav", "t": 2.26, "db": -21}]`
- Los tiempos salen del plan de gráficos (el instante en que entra cada gráfico).

## Estilo Premium
- Música 20 dB por debajo de la voz: `mezclar.py --musica-db -20`.
- Efectos: usa `06_trabajo/efectos_sugeridos.json`, que genera `construir_composicion.py` (whoosh −24 dB en barridos, clic −28 dB en palabras serif, impacto −20 dB en capítulos). Quita las líneas de los efectos que el usuario no tenga.
- Sin silencios de más de 0,3 s, salvo un respiro de 0,4 s tras un remate.

## Máster
−14 LUFS integrado (el volumen que usan Instagram y TikTok), pico real por debajo de −1 dB, medido sobre el MP4 final.

```bash
python "{SKILL}/scripts/mezclar.py" --video <vídeo> --voz 06_trabajo/voz_cortada.wav [--musica 05_musica/<pista>] [--efectos 06_trabajo/efectos.json] --out 07_entrega/<tema>.mp4
```
El script hace el máster en dos pasadas y comprueba el resultado.

## Notas típicas
- «Los efectos están muy fuertes» → baja todos 6 dB en `efectos.json`.
- «No se me entiende con la música» → baja la música 4 dB (`--musica-db -16`).
