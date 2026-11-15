# CLAUDE.md · DECODIK Edición con IA

Lee esto antes de trabajar en este repositorio.

## Qué es
DECODIK acompaña a **talentos apasionados del deporte** (no solo deportistas: fans, analistas, humor, fitness, lifestyle, coleccionistas, noticias…) a profesionalizarse como creadores y **colaborar con marcas**. Este repo es el **Módulo de Edición con IA** de la formación DECODIK: skills + guiones de lecciones.

Responsable: Santiago (contenido de marca personal y edición en DECODIK). Habla con él en español, tuteando.

## Principios (no negociables)
1. **Propiedad intelectual.** Material de formaciones de terceros se usa solo como referencia de investigación. Nunca copies sus SKILL.md, prompts, catálogos, scripts ni textos aquí. Analiza el concepto y escribe una implementación original. `referencias/` y `_investigacion/` están en `.gitignore`.
2. **Cero experiencia.** El talento no sabe editar ni usar IA. Una frase para empezar, preguntas cortas, un paso cada vez.
3. **Cada lección responde:** qué podrá hacer · cómo lo aplica a su contenido · cómo mejora su trabajo con marcas.
4. **Marcas:** señalización de publicidad siempre; no inventar datos de producto.
5. **Cada skill en 3 usos:** alumno (lista para usar) · aprendizaje (comentada) · producción interna.

## Estado (v0.1.0)
- `skills/decodik-perfil` — entrevista → `perfil-talento.md`
- `skills/decodik-edicion` — idea → plantilla → guion + 3 ganchos → lista de tomas → guía CapCut → Sello DECODIK. Referencias: contexto, catálogo de 9 plantillas, estándar de calidad, guía CapCut.
- `skills/decodik-marca` — brief → revisión contra brief → mensaje de entrega
- `modulo/` — mapa de 3 niveles + 7 guiones Loom del nivel 1

## Siguiente objetivo: `decodik-editor` (v0.2)
El talento deja una carpeta y la IA le devuelve el vídeo editado.

**Decisión (actualizada 2026-11-15):** UNA skill de entrada (`decodik-editor`) con **2 modos** — **marca personal** · **UGC para marcas**. Se construye primero **UGC para marcas**: la marca da el brief **y el guion**; la IA explica el brief y responde dudas, planifica la grabación, propone el estilo de edición, revisa los brutos contra el guion, edita y entrega. Diseño completo: `docs/diseno-decodik-editor.md` (manda sobre el flujo de abajo si hay diferencias). Por dentro, un archivo de referencia por modo y por fase. `decodik-edicion` y `decodik-marca` se integran en ella; se mantiene la ruta sin edición automática (guion + guía CapCut).

**Carpeta estándar del talento:**
```
01_brief/      brief de la marca (pdf, docx, txt, captura)
02_brutos/     clips del móvil (mp4, mov)
03_recursos/   fotos, capturas, b-roll
04_marca/      logos, guía de marca
05_musica/     música con licencia
06_entrega/    lo que genera la IA
perfil-talento.md
```

**Flujo:**
1. Comprobar la carpeta y pedir lo que falte.
2. Preguntar modo, plataforma, duración y plantilla (o recomendar 2).
3. Leer el brief → ficha de brief.
4. Transcribir los brutos con marcas de tiempo e inventariar tomas (calidad, mejores tomas).
5. Guion **a partir de lo grabado** (no inventar frases) + 3 ganchos + validación contra brief.
6. **Aprobación del talento** antes de editar.
7. Edición: corte de silencios/muletillas/repeticiones → montaje según plantilla → subtítulos → gancho y CTA en pantalla → render MP4 1080p 9:16.
8. Revisión: estándar de calidad + brief → Sello DECODIK.
9. Entrega en `06_entrega/`: MP4, SRT, guion, notas + mensaje para la marca.

**Estilos de edición:** catálogo propio en `docs/catalogo-estilos-decodik.md` (formatos genéricos de redes con nombres y descripciones de DECODIK + estilos específicos de UGC). **Día 1 del modo UGC:** subtítulo nativo + palabra a palabra, y los estilos UGC natural, Problema → solución y Unboxing; en marca personal, Lista rápida y Ranking por niveles.
**Modo anuncio (v1):** variantes de gancho, 15/30 s, 9:16 · 4:5 · 1:1, zonas seguras, afirmaciones verificables.

**Stack (actualizado 2026-11-15):** **ffmpeg + whisper** (transcripción con marcas de tiempo; corte, subtítulos y textos). Para gráficos y animaciones: **HyperFrames** (HeyGen, Apache-2.0, HTML → MP4). **No usar Remotion:** su licencia es de pago para empresas de 4 personas o más.

**Bases open source permitidas** (descargar siempre del repositorio original, respetar su licencia y citar la procedencia en un `CREDITOS.md`):
- `heygen-com/hyperframes` (Apache-2.0)
- packs de `iart-ai` (MIT), p. ej. `tiktok-video-skills`, `ad-video-skills`, `ecommerce-video-skills`
- ffmpeg, whisper / whisper.cpp, Playwright, GSAP, three.js, rough.js (según su licencia)

**Prohibido como base:** el «Módulo de Edición» de Fórmula 100K (ZIP con `auto-edicion`, `editor-video-formula100k`, `*-f100k`…) y cualquier skill de F100K. Es propietario (todos los derechos reservados). No se copia, no se adapta y no se abre como plantilla al escribir código de DECODIK. Si alguna pieza de ese ZIP declara una licencia libre de un tercero (p. ej. el motor adaptado de iart-ai), se descarga del repositorio original del tercero, nunca del ZIP.

Scripts dentro de la skill (`scripts/`), sin claves de API obligatorias para el modo básico.

## Pendiente de decidir (preguntar a Santiago)
- Disponibilidad de la app de escritorio de Claude con carpeta conectada en el plan de los talentos, y límites de tamaño de los brutos.
- Si la entrega incluye un proyecto editable además del MP4.
- Repo público → privado.

## Protocolo de trabajo (obligatorio)
1. **Antes de cada tarea:** di qué tarea de `docs/checklist-v0.2.md` vas a hacer (por su número), qué archivos vas a crear o cambiar y cómo se comprobará que funciona. **Espera el «ok» de Santiago.**
2. **Una tarea cada vez.** No empieces la siguiente sin cerrar la anterior.
3. **Al terminar cada tarea:**
   - pruébala con el caso de `docs/casos-de-prueba.md` que corresponda y enseña el resultado (archivo generado, captura o salida);
   - marca la tarea con `[x]` en `docs/checklist-v0.2.md` y anota la prueba en una línea;
   - haz un commit con el número de tarea en el mensaje (ej. `#25 corte automático de silencios`).
4. **Si algo no se puede hacer como dice este archivo, para y pregunta.** No cambies decisiones de diseño por tu cuenta.
5. **Al final de cada sesión:** resumen de 5 líneas: qué se hizo, qué se probó, qué falla, siguiente tarea.

## Convenciones
- Todo en español neutro, tuteando. Nombres de skills en minúsculas con guiones, prefijo `decodik-`.
- `SKILL.md` con `name` y `description` (qué hace + frases que la activan). Referencias en `references/`, scripts en `scripts/`.
- Commits pequeños y descriptivos; versión en `.claude-plugin/plugin.json`.
- Probar cada cambio con un caso real antes de darlo por bueno.
