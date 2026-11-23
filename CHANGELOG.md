# Cambios · decodik-editor

## 1.3 · 23-11-2026
**Pedidos**
- Nuevo flujo **Armar un pedido** (`flujos/pedido.md`): «arma el pedido DK-0007» lee la fila del pedido en el Google Sheet de la landing «Pide tu edición» (conector de Google Sheets), crea el proyecto, trae los brutos y el archivo, pasa el pipeline del formato pedido y deja un borrador en CapCut. El storyboard se sigue enseñando antes de construir.
- `scripts/pedido.py`: `leer` (fila y columnas del pedido, sin la clave de seguimiento), `preparar` (proyecto `<fecha>_<talento>-<tema>`, descarga de carpetas públicas de Drive con subcarpetas, o copia de una carpeta o .zip ya descargados, y reparto en tomas, recursos y brief; se puede relanzar), `estado` (celdas que hay que escribir: «En edición», «Edición (interno)», «Proyecto en el ordenador») y `capcut` (exporta con la plantilla de `_mi-estilo/pedidos.json` y comprueba que el borrador queda registrado).
- La configuración del editor (Sheet y borrador plantilla) va en `_mi-estilo/pedidos.json`, fuera de la skill.
- `storyboard_corte.py`: si el vídeo de trabajo va sin sonido, crea `vista-con-voz.mp4` con la voz para poder escuchar el corte.
- `storyboard_corte.py`: «Así quedaría» reproduce `asi-quedaria.mp4`, el corte montado de verdad. Antes saltaba las pausas en directo y, como el navegador solo mira el tiempo ~4 veces por segundo, las pausas cortas se seguían oyendo.
- `scripts/servir.py`: sirve los storyboards por http dejando saltar dentro del vídeo (con `python -m http.server` los ▶ y «Así quedaría» no saltaban) y los abre en el navegador del usuario.
- `exportar_capcut.py`: con la estructura «superposiciones» (por defecto) ya no hace falta `--plantilla-audio`; la voz va en la propia toma.

## 1.2 · 23-11-2026
**Formatos**
- Nuevo formato **Tierlist** (`referencias/formato-tierlist.md`, nivel intermedio). Título fijo arriba y tabla de niveles de colores bajo la barbilla; cada cosa que se nombra entra en foto real y baja a su nivel en la palabra del veredicto (y se mueve si cambia de opinión). La foto grande se coloca donde no hay miniaturas, subtítulos de 1-3 palabras que no acaban en «y», «la», «sin», destello al quitar la tabla y píldora de Follow. Zona propia (x 120-960, y 288-1450) porque la tabla no cabe en la banda común.
- La skill **busca las fotos** (`scripts/tierlist_fotos.py`): Openverse y Wikimedia Commons (y Pexels si hay clave), sin licencias ND ni NC, hoja de candidatas para elegir y créditos en `07_entrega/creditos-fotos.txt`. `scripts/tierlist_plan.py` saca tiempos y posiciones de la transcripción y avisa de lo que se pisa; `scripts/construir_tierlist.py` lo dibuja y exporta.
- Subtítulos en la palabra: `scripts/alinear_palabras.py` ajusta los tiempos de whisper a la voz real (tramos de voz del audio + tiempos DTW de whisper.cpp con `-dtw … -nfa`), porque whisper movía palabras sueltas hasta 0,6 s. El agrupado del tierlist no parte frases por un punto, no acaba en palabra de enlace y no deja subtítulos de menos de 0,35 s.
- Nuevo formato **Explicativo con texto · pantalla dividida** (`referencias/formato-explicativo-texto.md`, nivel intermedio). Cuando se explica algo, arriba va una palabra protagonista y una línea corta sobre un fondo premium (degradado oscuro, halo suave del acento, rejilla fina, grano y viñeta); abajo la persona, con la cabeza a 40 px de la costura. Fichas iguales para cada opción, comparativa final, acento de color una vez por escena y el rojo una sola vez. Sin subtítulos salvo que se pidan.
- Storyboard visual del formato (`scripts/storyboard_explicativo.py`): una tarjeta por escena con el fotograma real y el boceto de la pantalla; mide la cabeza en cada escena y avisa si hay más de 3 escenas divididas seguidas.
- De momento `construir_composicion.py` no dibuja este formato: se construye a partir del storyboard aprobado.
- Nuevo formato **Explicativo con motion graphics · pantalla dividida** (`referencias/formato-explicativo-motion.md`): la misma estructura, pero arriba explica un dibujo animado que cambia con la voz. Librería de motions de línea en `scripts/bocetos_motion.py` (producto, medidor, molécula, iconos, fila, ondas, barra, gotas, comparativa, etiqueta) y tira de fotogramas clave en el storyboard.

- Motions: tipo `cadena` (frase visual causa → efecto con flechas y sellos ✓/✗, 1-2 palabras como mucho), iconos nuevos (precio, molécula, calendario, batería, corazón, músculo) y criterios con icono en la comparativa. Rótulo de escena, insignias de cristal y órbitas para que el panel no quede vacío.
- Motions con **personaje pictograma** (`scripts/personajes_motion.py`, tipo `persona`) que hace lo que se cuenta: entrena, duerme, calambre, compra, relajado, recupera, toma, corre. Todo se mueve en bucle (producto, aguja, flechas, insignias, órbitas) y el storyboard lo enseña animado.
- `scripts/construir_explicativo.py`: construye en HyperFrames el formato con motion graphics a partir del storyboard (pantalla dividida, personaje y motions animados de forma determinista, CTA en zona segura).
- Los cambios de pantalla (cámara ↔ dividida) se pegan al corte de toma más cercano y el storyboard avisa si alguno cae en mitad de una toma; el encuadre de la persona se reajusta en cada corte dentro de una escena dividida.
- Los dos formatos explicativos comparten el fondo premium con textura del panel de arriba (`fondo_premium`); la toma desenfocada de la persona ya no se usa como fondo.

- Nuevo formato **Mi historia · B-roll encima con subtítulos** (`referencias/formato-mi-historia.md`, nivel básico): el archivo de la persona entra encima en cada frase que nombra algo (vídeo vertical a pantalla completa, horizontal en recuadro arriba sobre su fondo desenfocado, fotos con zoom lento, HDR a SDR) y subtítulos simples. Storyboard visual con comprobaciones (`scripts/storyboard_historia.py`) y montaje con ffmpeg (`scripts/construir_historia.py`).
- `storyboard_historia.py --ajustar`: mueve cada cambio de plano que cae dentro de una palabra al borde más cercano. Los tiempos de palabra para subtítulos salen de faster-whisper (los de whisper.cpp con `-ml 1` se desvían hasta ~0,7 s).
- Recursos: `analizar_recursos.py` (actividad, cortes internos, huellas de encuadre, orientación real) y `tramos.py`: cada B-roll entra en su tramo más activo y estable, sin cruzar cortes ni barridos; lo horizontal (también fotos) en recuadro, nunca recortado.
- `exportar_capcut.py`: exporta el montaje «Mi historia» a un borrador de CapCut editable, usando un borrador del usuario como plantilla.
- Subtítulos con fuente propia: en el `.ass` va el nombre de familia interno de la fuente (p. ej. «HelveticaNowDisplay ExtraBold»); si no, libass pone otra sin avisar.

**Regla para todo motion graphic**
- Ningún icono ni texto se pisa, todo entra en pantalla y en la zona segura con margen, y ningún texto baja de 26 px (si no cabe, se acorta). El storyboard lo comprueba solo y avisa; también está en `control-calidad.md` y `graficos.md`.

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
