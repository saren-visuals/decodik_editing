# Checklist v0.2 · decodik-editor (Día 1)

Los números coinciden con la checklist general de Santiago. Marca `[x]` solo cuando se cumple el **criterio de hecho** y añade la prueba en «Prueba».

**Orden (cambiado por Santiago el 2026-11-15):** primero la edición básica de bruto a editado (#24 → #15 → #25 → #28 → #34); después U3–U5 y lo complejo.

## 0 · Diseño
- [x] #0 `docs/diseno-decodik-editor.md` aprobado por Santiago · **Hecho cuando:** Santiago da el «ok» al diseño · Prueba: ok de Santiago el 2026-11-15

## UGC para marcas · fases 1-4 (primero, sin vídeo)
- [x] U1 Elección de modo (marca personal / UGC para marcas) · **Hecho cuando:** «edita mi vídeo» lleva a esa pregunta y a nada más · Prueba: 2026-11-15, a mano siguiendo `SKILL.md` (sin sesión nueva con el plugin): «edita mi vídeo» → solo la pregunta de modo, sin herramientas; «no sé» → ejemplo por opción y misma pregunta; modo ya dicho → confirma y sigue. Repetir en sesión real con `claude --plugin-dir .`
- [x] U2 Ficha de campaña desde brief + guion de la marca · **Hecho cuando:** en caso B salen todas las secciones de `ficha-campana.md` y los huecos · Prueba: 2026-11-15, caso B (Zancada) a mano siguiendo `modo-ugc.md` fase 1 → `06_entrega/ficha-campana.md` con las 8 secciones, 5 escenas (literales 3 y 5) y 5 huecos (música, derechos de uso, regrabación en la ronda, quién aprueba, envío del producto); frases literales idénticas y ningún dato de producto fuera del brief (comprobado con script).
- [ ] U3 Dudas respondidas solo con el brief · **Hecho cuando:** a una pregunta cuya respuesta no está en el brief, contesta que no lo dice y la añade al mensaje para la marca
- [ ] U4 Plan de grabación por escenas · **Hecho cuando:** cada escena del guion tiene sus tomas y la checklist del día
- [ ] U5 Ficha de estilo · **Hecho cuando:** propone estilo a partir del brief y la guía de marca y espera aprobación

## UGC para marcas · fases 5-7 (vídeo)
- [ ] U6 Tabla de cobertura del guion · **Hecho cuando:** en caso B cada escena apunta a clip + segundo y detecta la palabra prohibida
- [ ] U7 Montaje escena a escena con la ficha de estilo · **Hecho cuando:** el orden y los textos siguen el guion de la marca
- [ ] U8 Cambios de la marca → nueva versión · **Hecho cuando:** pegando comentarios de ejemplo sale v2 con los cambios y nada más

Las tareas de abajo siguen valiendo para las fases 5-7.

## Decisiones (Santiago)
- [ ] #2 Dónde trabaja el talento (app de escritorio con carpeta / chat sin carpeta) · **Hecho cuando:** decidido y escrito en CLAUDE.md
- [ ] #3 Límites de los brutos · **Hecho cuando:** probado con un bruto 4K y uno 1080p de 1-3 min; tiempos anotados
- [ ] #4 Plataformas y formatos · **Hecho cuando:** lista cerrada en CLAUDE.md
- [ ] #5 Qué recibe el talento · **Hecho cuando:** lista cerrada en CLAUDE.md
- [ ] #6 Nombre y frase de activación · **Hecho cuando:** escrita en la `description` de la skill

## Estructura
- [ ] #46 Skill `skills/decodik-editor/` con `SKILL.md` y referencias por modo y por fase; `decodik-edicion` y `decodik-marca` integradas · **Hecho cuando:** Santiago aprueba la estructura de archivos
- [ ] #47 Ruta sin edición automática (guion + guía CapCut) sigue funcionando · **Hecho cuando:** caso C da guion y guía sin tocar vídeo

## Carpeta y preguntas
- [ ] #7 Plantilla de carpeta con LEEME · **Hecho cuando:** existe `plantilla-carpeta/` y se puede descargar en ZIP
- [ ] #8 Formatos admitidos y nombres · **Hecho cuando:** documentado en el LEEME
- [ ] #10 Detecta lo que falta · **Hecho cuando:** con una carpeta sin brief en modo marca, lo pide en vez de seguir
- [ ] #11-13 Preguntas iniciales (modo, plataforma, duración, plantilla, perfil) · **Hecho cuando:** en cada caso de prueba pregunta solo lo que falta, en un mensaje

## Análisis y guion
- [ ] #14 Ficha de brief · **Hecho cuando:** caso B genera la ficha con mensajes clave, prohibidos y CTA
- [x] #15 Transcripción con marcas de tiempo · **Hecho cuando:** `transcripcion.json` con tiempos por palabra o frase para cada bruto · Prueba: 2026-11-15, caso A (15 clips .mov 4K HEVC del iPhone, 107 s) → `transcripcion.json` con 210 palabras con inicio y fin, en 84 s; texto revisado clip a clip; «Eileen Gu» corregido con `--nombres`; la toma repetida del Clip 8 aparece dos veces; 10 inicios adelantados por Whisper corregidos con los silencios de ffmpeg (p. ej. Clip 2 «Se» 1,34 → 3,23 s, donde empieza la voz); segunda ejecución sin cambios en 0,3 s.
- [ ] #16 Inventario de tomas · **Hecho cuando:** tabla con clip, contenido, calidad y mejores tomas
- [ ] #19 Guion a partir de lo grabado · **Hecho cuando:** cada frase del guion apunta a un clip y segundo reales
- [ ] #21 3 ganchos · **Hecho cuando:** 3 opciones (verbal, texto, visual) usando tomas reales
- [ ] #22 Validación contra brief · **Hecho cuando:** tabla de cumplimiento antes de editar
- [ ] #23 Aprobación · **Hecho cuando:** la skill se detiene y no edita sin «ok»

## Edición
- [x] #24 Motor (ffmpeg + whisper) instalado y documentado · **Hecho cuando:** un comando de prueba renderiza un MP4 de 5 s · Prueba: 2026-11-15, `uv run scripts/revisar_equipo.py --whisper --prueba …` en Windows → ffmpeg 9.0.2 con libx264 y libass, faster-whisper 1.2.1 listo, `prueba-motor.mp4` 1080×1920, 30 fps, AAC, 5,00 s; sin ffmpeg en el PATH da ✗ con `winget install Gyan.FFmpeg` y sale con 1. Documentado en `references/motor-edicion.md`.
- [x] #25 Corte automático · **Hecho cuando:** el vídeo empieza en la primera palabra y no hay silencios > 0,3 s ni sílabas cortadas (escuchado) · Prueba: 2026-11-15, caso A: 97,9 s de brutos → `corte.mp4` de 62,8 s en 20 tramos; la voz suena a los 0,06 s; silencio más largo 0,298 s (silencedetect -35 dB); los 30 ms de entrada y salida de los 20 tramos por debajo de -30 dB; del Clip 8 (frase dicha dos veces) se queda la mejor toma (nota 0,99 frente a 0,95); HDR del iPhone pasado a BT.709. Escuchado por Santiago: «suena bien». Decisión de Santiago: con tomas repetidas, la mejor toma (no la última).
- [ ] #26 Montaje de 3 plantillas (Lista rápida, Ranking, Integración de marca) · **Hecho cuando:** cada una renderizada con un caso de prueba
- [x] #28 Subtítulos · **Hecho cuando:** 1-4 palabras por bloque, sincronizados, en zona segura, nombres bien escritos · Prueba: 2026-11-15, caso A: 190 palabras en 61 bloques, ninguno de más de 4 palabras visibles; estilo nativo + palabra a palabra (Montserrat ExtraBold, OFL); base al 66 % de la altura y 130 px de margen lateral, sin tapar la cara en 6 fotogramas revisados; 0 de 190 palabras resaltadas más de 100 ms antes de sonar (silencedetect sobre `subtitulado.mp4`); «Eileen Gu» bien escrito. Visto por Santiago: «van bien». Para esto, `cortar.py` recorta cada tramo a cuadros exactos y `transcribir.py` mueve al final del silencio cualquier palabra que Whisper coloca dentro de una pausa; el corte se volvió a medir con los criterios de #25 (máx. 0,297 s, voz a 0,06 s, 0 bordes dentro de voz).
- [ ] #29 Gancho y CTA en pantalla · **Hecho cuando:** gancho visible desde el frame 0, CTA al final
- [x] #34 Render 1080×1920 + revisión de fotogramas · **Hecho cuando:** la skill extrae y revisa fotogramas clave antes de entregar · Prueba: 2026-11-15, caso A → `06_entrega/video-v4.mp4` en una sola pasada desde los brutos (corte + subtítulos + volumen): 1080×1920, 30 fps, 61,10 s, −14,9 LUFS, pico −1,2 dBTP; revisión automática 8 de 8 (sin congelados ni negros, subtítulo en los 8 fotogramas clave con voz) y hoja de contacto revisada. Color sin tocar (decisión de Santiago): HDR del iPhone → HEVC 10 bits BT.2020/HLG, luz y color medios a ≤0,1 % del bruto en 3 tramos; texto convertido a BT.2020 + HLG con blanco de referencia. Visto en el móvil por Santiago: «se ve igual». Tarjeta NVIDIA: lee con CUDA; NVENC no disponible con el controlador 592.82 (pide 610), se avisa y codifica con el procesador.

## Revisión y entrega
- [ ] #35 Reglas de anuncio · **Hecho cuando:** en modo anuncio avisa de afirmaciones sin fuente y de música sin licencia
- [ ] #40 Estándar de calidad + Sello · **Hecho cuando:** devuelve Sello o lista de arreglos
- [ ] #41 Revisión contra brief · **Hecho cuando:** tabla punto por punto en caso B
- [ ] #43 Entrega en `06_entrega/` · **Hecho cuando:** MP4 + SRT + guion + notas
- [ ] #44 Mensaje a la marca · **Hecho cuando:** texto listo para copiar en caso B

## Pruebas
- [ ] #55 Los 3 casos de `casos-de-prueba.md` pasan de principio a fin · **Hecho cuando:** Santiago ve los 3 vídeos y da el ok
