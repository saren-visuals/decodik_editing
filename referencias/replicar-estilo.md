# Replicar un estilo

Objetivo: que el usuario edite **como en un vídeo que le gusta** (subtítulos, ritmo, gráficos, transiciones, sonido) y que ese estilo quede guardado con nombre para usarlo cuando quiera. Se pueden guardar todos los estilos que quiera.

Diferencia con `mi-estilo.md`: aquel crea **un** estilo propio con preguntas o con varias referencias mezcladas. Este copia el **lenguaje de edición de un vídeo concreto** y lo guarda en una biblioteca.

## Reglas
- **Inspírate, no copies contenido.** Se replica el *cómo se edita*, nunca los clips, la música, el logo, la marca de agua ni los textos del creador original. La referencia no aparece en el vídeo final.
- **Las referencias las trae el usuario**, descargadas o grabadas en pantalla. No las descargues tú de redes sociales. Son para analizarlas en su ordenador, no para publicarlas.
- **Fuentes:** si la de la referencia es de pago, propone la libre más parecida (de `{SKILL}/fonts/` o de Google Fonts) y dilo.
- **Di lo que no se puede** antes de prometer nada (ver «Límites»).

## Pasos
1. **Nombre y carpeta.** Pregunta cómo quiere llamar al estilo (corto: «gym-rapido», «podcast-limpio»). Crea `<Decodik>/_estilos/<nombre>/referencias/` y pídele que deje ahí **1-3 vídeos del mismo estilo** (mejor del mismo creador). Si da un enlace, pídele que lo descargue él o que grabe la pantalla del móvil.
2. **Mide la referencia.** Explica en una frase que vas a «mirar el vídeo con lupa». Por cada referencia:
   - Datos: `ffprobe` (resolución, fps, duración).
   - Ritmo de planos: `ffmpeg -i ref.mp4 -vf "select='gt(scene,0.3)',showinfo" -f null -` → cortes por segundo y duración media de plano.
   - Fotogramas: 2 por segundo (`-vf fps=2`) y una hoja de contacto (`tile=6x4`). Míralos. Amplía los subtítulos con un recorte para ver fuente, contorno y sombra.
   - Voz y texto: transcribe con faster-whisper y compara con los subtítulos: cuántas palabras por subtítulo, cuánto duran, si van palabra a palabra, si hay palabra clave y de qué color.
   - Sonido: `ffmpeg -i ref.mp4 -af ebur128 -f null -` (volumen), si hay música de fondo y efectos en los cortes o en los textos.
   - Color: toma el HEX de los colores de texto y gráficos sobre los fotogramas (Pillow).
3. **Ficha del estilo.** Enseña una tabla con lo medido: subtítulos (fuente parecida, tamaño en px sobre 1080×1920, color HEX, posición, palabras, animación), palabra clave, ritmo (s por plano, pausas), gráficos y zooms, transiciones, música y efectos, color. Añade una columna **¿Se puede replicar?** con *Sí*, *Aproximado* o *No* y el nivel que necesita (básico, intermedio o avanzado). Si su nivel no llega a algo, díselo y ofrece subir de nivel (`comprobar_equipo.py`).
4. **Preguntas.** Una tanda de AskUserQuestion (máximo 4): qué es lo que más le gusta, qué cambiaría, si usa **sus** colores y logo o los de la referencia (recomienda los suyos) y qué no quiere ver nunca.
5. **Guárdalo.** En `_estilos/<nombre>/`:
   - `estilo.json` con **la misma estructura que el estilo Decodik más parecido** (`{SKILL}/estilos/<id>.json`; `minimal.json` si es básico), con valores medibles (HEX, px, s, dB) y `"nivel_minimo"`.
   - `ficha.md`: la tabla del paso 3 y lo que no se replica.
   - `muestra.jpg`: un fotograma de la referencia para reconocerlo.
6. **Prueba de comparación.** Edita **10-15 s** de una toma del usuario con el estilo y monta la comparación lado a lado, a la misma altura, con la referencia a la izquierda (`ffmpeg ... hstack`). Guárdala en `_estilos/<nombre>/comparacion.mp4` y enséñala. Pregunta qué se ve distinto, ajusta `estilo.json` y repite (**3 rondas como mucho**; si sigue sin parecerse, explica qué parte es un límite).
7. **Listo.** Dile en una línea que desde ahora, al editar (flujo B), sus estilos guardados aparecen como opción: «edita con mi estilo gym-rapido».

## Límites (dilo claro)
- **Se replica bien:** subtítulos (fuente parecida, color, tamaño, posición, palabras, animaciones sencillas), ritmo de corte, zooms, tarjetas y gráficos sencillos, transiciones de corte, volumen y uso de música y efectos.
- **Aproximado:** animaciones de texto complejas, color de cine (con `color.md`), gráficos muy elaborados (necesitan intermedio).
- **No se puede:** lo que viene del rodaje (luz, cámara, encuadre, movimientos), efectos de After Effects con seguimiento 3D o partículas, y la música o los clips del creador.
