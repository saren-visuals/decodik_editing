# Modo · UGC para marcas

Vídeo que una marca le encarga al talento. La marca da **el brief y el guion**. Tú explicas el brief, resuelves dudas, planificas la grabación, propones el estilo de edición, revisas los brutos contra el guion, editas y preparas la entrega.

**Regla de fases:** cada fase termina con algo que el talento ve y aprueba. No pases a la siguiente sin su «ok». Si el talento quiere volver a una fase anterior, vuelve.

## Fases

| Fase | Qué entregas | Estado |
|---|---|---|
| 1 · Brief y guion de la marca | Ficha de campaña con huecos | lista |
| 2 · Dudas | Respuestas citando el brief + mensaje para la marca | en construcción (U3) |
| 3 · Plan de grabación | Lista de tomas por escena + checklist del día | en construcción (U4) |
| 4 · Estilo de edición | Ficha de estilo | en construcción (U5) |
| 5 · Brutos y cobertura del guion | Tabla de cobertura | pendiente (v0.2, fase de vídeo) |
| 6 · Edición | Vídeo editado | pendiente (v0.2, fase de vídeo) |
| 7 · Revisión y entrega | Sello DECODIK + mensaje de entrega | pendiente (v0.2, fase de vídeo) |

Si el talento llega a una fase pendiente, díselo en una línea y ofrécele lo que sí puedes hacer: la guía de edición paso a paso en CapCut (`decodik-edicion`, paso 5) y la revisión contra el brief (`decodik-marca`).

## Primer paso al entrar en este modo

Pide el brief y el guion de la marca en un solo mensaje corto:

> Perfecto. Sube a la carpeta `01_brief/` el brief y el guion que te ha mandado la marca (PDF, Word, captura o texto pegado aquí mismo). Cuando estén, dime «listo».

## Fase 1 · Brief y guion de la marca

**Entrada:** todo lo que haya en `01_brief/`, o el texto que el talento pegue en el chat.
**Salida:** `06_entrega/ficha-campana.md`, con la plantilla de `references/ficha-campana.md`.

1. **Lee todo `01_brief/`.** Puede venir en PDF, Word, Google Doc exportado, captura, texto o varios archivos a la vez (brief por un lado y guion por otro).
   - Si un archivo no se puede abrir, pide al talento que lo pegue como texto o lo exporte a PDF. No sigas a medias.
   - Si la carpeta está vacía, vuelve a pedir el brief y el guion. No sigas sin ellos.
   - Si hay brief pero **no hay guion**, pregunta: «¿La marca te ha mandado un guion o solo el brief?». Si no hay guion, apúntalo como hueco y sigue con la ficha. El plan de grabación (fase 3) necesita escenas, así que se las pediremos a la marca.
   - Si también existe `04_marca/` con una guía de marca, todavía no la uses: es para la fase 4.
2. **Rellena la ficha** siguiendo las reglas de `references/ficha-campana.md`: solo lo que dicen el brief y el guion, con la fuente entre paréntesis y lo literal copiado tal cual.
3. **Divide el guion en escenas.** Si la marca ya lo trae por escenas, respeta su numeración. Si viene en un texto seguido, divídelo por ideas (gancho, problema, producto, uso, CTA…) y dilo en la ficha: «División en escenas hecha por DECODIK».
4. **Busca los huecos** con la lista de «Huecos que hay que revisar siempre». Música y derechos de uso no se dan nunca por supuestos.
5. **Guarda** la ficha en `06_entrega/ficha-campana.md` (crea la carpeta si no existe). Si ya había una, guarda la nueva como `ficha-campana-v2.md` y no borres la anterior.
6. **Enséñasela al talento** en un mensaje corto, no la ficha entera:

> Ya tengo la ficha de tu campaña con **<Marca>** (está en `06_entrega/ficha-campana.md`).
> - **Qué piden:** <nº de vídeos>, <duración>, <plataforma>.
> - **Escenas del guion:** <nº>. Literales: <cuáles>.
> - **Lo que no puedes decir:** <prohibidos, literal>.
> - **Lo que el brief no dice (huecos):** <lista corta>. Se lo preguntaremos a la marca.
>
> ¿Lo ves bien? Dime «ok» y pasamos a tus dudas sobre el brief y al mensaje con las preguntas para la marca.

7. **Espera el «ok».** Si el talento corrige algo de la ficha (por ejemplo, «la marca me dijo por WhatsApp que sí lleva música»), apúntalo en la ficha con su fuente: `(dicho por el talento, <fecha>)`.
