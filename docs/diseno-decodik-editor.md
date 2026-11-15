# Diseño · decodik-editor v0.2

_Estado: **aprobado por Santiago el 2026-11-15**_

## Entrada
El talento escribe **«edita mi vídeo»** (o algo parecido). La skill pregunta una sola cosa:

> ¿Qué vídeo vamos a hacer?
> **1. Marca personal** — contenido para tu cuenta.
> **2. UGC para una marca** — vídeo que te ha encargado una marca.

Primero se construye **2. UGC para marcas**. Marca personal sigue usando el flujo actual (idea → plantilla → guion → guía) hasta v0.3.

## Flujo UGC para marcas (7 fases)

Cada fase termina con algo que el talento ve y aprueba. No se pasa a la siguiente sin su «ok».

### Fase 1 · Brief y guion de la marca
- **El talento sube** a `01_brief/` el brief completo y el guion de la marca (PDF, Word, Google Doc exportado, captura o texto pegado).
- **La IA entrega la Ficha de campaña** (`06_entrega/ficha-campana.md`):
  - marca, producto, objetivo de la campaña;
  - entregables: nº de vídeos, duración, formatos, plataformas, si es orgánico en la cuenta del talento o anuncio en la cuenta de la marca;
  - **guion de la marca dividido en escenas** (nº, texto a decir, qué se ve, duración);
  - obligatorios, prohibidos, CTA, señalización de publicidad;
  - estilo pedido: subtítulos, música, texto en pantalla, logo, ritmo;
  - fechas, rondas de cambios, derechos de uso;
  - **huecos:** lo que el brief no dice.

### Fase 2 · Dudas
- El talento pregunta lo que quiera («¿puedo decirlo con mis palabras?», «¿sale el logo?», «¿qué ropa llevo?»).
- La IA **responde solo con lo que dice el brief**, citando la parte. Si el brief no lo dice, lo dice así y no inventa.
- Con los huecos, prepara un **mensaje para la marca** con las preguntas pendientes, listo para copiar.

### Fase 3 · Plan de grabación
- Del guion de la marca saca la **lista de tomas**: por escena, la toma principal hablando, los planos de producto, los recursos y los planos de apoyo.
- Recomendaciones para grabar (luz, sonido, encuadre, grabar 2-3 veces cada frase obligatoria y el gancho).
- Checklist para el día de grabación.

### Fase 4 · Estilo de edición
- Propone un **estilo** a partir del brief y, si existe, de `04_marca/` (guía de marca):
  - UGC nativo (lo habitual): parece hecho por el creador, subtítulos al estilo de la red, cortes rápidos, sin efectos de anuncio;
  - o el estilo que pida la marca.
- Entrega la **Ficha de estilo**: ritmo, subtítulos (tipo, tamaño, posición), texto en pantalla, música, logo, señalización, versiones.
- El talento la aprueba o pide cambios.

### Fase 5 · Brutos y cobertura del guion
- El talento sube los clips a `02_brutos/`.
- La IA transcribe con marcas de tiempo y hace la **tabla de cobertura**:

| Escena | Frase del guion | Mejor toma (clip + segundo) | ¿Dice lo exigido? | Calidad | Problema |
|---|---|---|---|---|---|

- Avisa de: escenas sin grabar, frases obligatorias que no se dicen igual, **palabras prohibidas**, producto mal nombrado, audio o luz malos.
- Si falta algo, dice exactamente qué volver a grabar. Si todo está, pide el «ok» para editar.

### Fase 6 · Edición
- Corte limpio (silencios, muletillas, repeticiones).
- Montaje escena a escena siguiendo el guion de la marca y la Ficha de estilo.
- Subtítulos, texto en pantalla, planos de producto y recursos, música si la hay, señalización.
- Render 1080×1920 (y otros formatos si el brief los pide).
- **Versiones habituales en UGC** (solo si el brief las pide): variantes de gancho, versión sin subtítulos, versión sin música.

### Fase 7 · Revisión y entrega
- Revisión con el estándar de calidad DECODIK + **tabla de cumplimiento del brief** → Sello DECODIK o lista de arreglos.
- Entrega en `06_entrega/`:
  - vídeo(s) final(es) MP4;
  - subtítulos SRT;
  - ficha de campaña, ficha de estilo y tabla de cumplimiento;
  - **mensaje de entrega para la marca**, listo para copiar.
- Si la marca pide cambios: el talento pega sus comentarios y la IA hace la versión siguiente (v2, v3…).

## Estructura de archivos propuesta
```
skills/decodik-editor/
  SKILL.md                     entrada: elegir modo y dirigir por fases
  references/
    contexto-decodik.md        (se mueve desde decodik-edicion)
    estandar-calidad.md        (se mueve desde decodik-edicion)
    modo-marca-personal.md     flujo actual resumido (idea → plantilla → guion → guía)
    modo-ugc.md                las 7 fases de arriba
    ficha-campana.md           plantilla de la Ficha de campaña
    ficha-estilo.md            plantilla de la Ficha de estilo + estilos base
    cobertura-guion.md         cómo emparejar guion y tomas
    catalogo-plantillas.md     (se mueve desde decodik-edicion)
    guia-capcut.md             ruta sin edición automática
  scripts/
    revisar_carpeta.py         comprueba la carpeta y lista lo que falta
    transcribir.py             whisper → transcripcion.json con tiempos
    cobertura.py               tabla escena ↔ toma
    cortar.py                  silencios, muletillas, repeticiones
    montar/                    proyecto Remotion: escenas, subtítulos, textos
    render.py                  render y extracción de fotogramas de revisión
plantilla-carpeta/             carpeta vacía 01-06 + LEEME.md para el talento
```
`decodik-perfil` se mantiene aparte (se usa una vez). `decodik-edicion` y `decodik-marca` se retiran cuando `decodik-editor` pase los casos de prueba.

## Orden de construcción propuesto
1. Fases 1-4 (solo texto, sin vídeo): ficha de campaña, dudas, plan de grabación, ficha de estilo. **Ya útil desde el día 1**, también para quien no tenga carpeta conectada.
2. Fase 5 (transcripción y cobertura).
3. Fase 6 (edición) con un solo estilo: UGC nativo.
4. Fase 7 (revisión y entrega).
5. Versiones y otros estilos.
