# Checklist v0.2 · decodik-editor (Día 1)

Los números coinciden con la checklist general de Santiago. Marca `[x]` solo cuando se cumple el **criterio de hecho** y añade la prueba en «Prueba».

## 0 · Diseño
- [x] #0 `docs/diseno-decodik-editor.md` aprobado por Santiago · **Hecho cuando:** Santiago da el «ok» al diseño · Prueba: ok de Santiago el 2026-11-15

## UGC para marcas · fases 1-4 (primero, sin vídeo)
- [ ] U1 Elección de modo (marca personal / UGC para marcas) · **Hecho cuando:** «edita mi vídeo» lleva a esa pregunta y a nada más
- [ ] U2 Ficha de campaña desde brief + guion de la marca · **Hecho cuando:** en caso B salen todas las secciones de `ficha-campana.md` y los huecos
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
- [ ] #15 Transcripción con marcas de tiempo · **Hecho cuando:** `transcripcion.json` con tiempos por palabra o frase para cada bruto
- [ ] #16 Inventario de tomas · **Hecho cuando:** tabla con clip, contenido, calidad y mejores tomas
- [ ] #19 Guion a partir de lo grabado · **Hecho cuando:** cada frase del guion apunta a un clip y segundo reales
- [ ] #21 3 ganchos · **Hecho cuando:** 3 opciones (verbal, texto, visual) usando tomas reales
- [ ] #22 Validación contra brief · **Hecho cuando:** tabla de cumplimiento antes de editar
- [ ] #23 Aprobación · **Hecho cuando:** la skill se detiene y no edita sin «ok»

## Edición
- [ ] #24 Motor (ffmpeg + whisper + Remotion) instalado y documentado · **Hecho cuando:** un comando de prueba renderiza un MP4 de 5 s
- [ ] #25 Corte automático · **Hecho cuando:** el vídeo empieza en la primera palabra y no hay silencios > 0,3 s ni sílabas cortadas (escuchado)
- [ ] #26 Montaje de 3 plantillas (Lista rápida, Ranking, Integración de marca) · **Hecho cuando:** cada una renderizada con un caso de prueba
- [ ] #28 Subtítulos · **Hecho cuando:** 1-4 palabras por bloque, sincronizados, en zona segura, nombres bien escritos
- [ ] #29 Gancho y CTA en pantalla · **Hecho cuando:** gancho visible desde el frame 0, CTA al final
- [ ] #34 Render 1080×1920 + revisión de fotogramas · **Hecho cuando:** la skill extrae y revisa fotogramas clave antes de entregar

## Revisión y entrega
- [ ] #35 Reglas de anuncio · **Hecho cuando:** en modo anuncio avisa de afirmaciones sin fuente y de música sin licencia
- [ ] #40 Estándar de calidad + Sello · **Hecho cuando:** devuelve Sello o lista de arreglos
- [ ] #41 Revisión contra brief · **Hecho cuando:** tabla punto por punto en caso B
- [ ] #43 Entrega en `06_entrega/` · **Hecho cuando:** MP4 + SRT + guion + notas
- [ ] #44 Mensaje a la marca · **Hecho cuando:** texto listo para copiar en caso B

## Pruebas
- [ ] #55 Los 3 casos de `casos-de-prueba.md` pasan de principio a fin · **Hecho cuando:** Santiago ve los 3 vídeos y da el ok
