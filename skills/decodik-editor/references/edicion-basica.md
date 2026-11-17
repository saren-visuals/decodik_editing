# Edición básica · de los clips del móvil al vídeo listo

El talento deja sus clips en `02_brutos/` de la carpeta del vídeo y recibe `06_entrega/video-vN.mp4`: cortado (sin silencios, muletillas ni tomas repetidas), con subtítulos, con el volumen de las redes y con el color tal como lo grabó.

Lleva gancho, cifras grandes, CTA y recursos del talento (B-roll y tarjetas) en pantalla. Todavía **sin** música ni formatos: llegan después.

## Antes de empezar

- **`$SKILL`** = la carpeta de esta skill (la que contiene `SKILL.md`). Los scripts están en `$SKILL/scripts/`. Usa siempre la ruta real, no la supongas.
- **Carpeta del vídeo** = la carpeta `AAAA-MM-DD Nombre` de este vídeo, dentro de la carpeta del talento. Se elige o se crea antes de empezar, con `references/carpetas.md`. En los comandos de abajo, `<carpeta del vídeo>` es su ruta completa.
- **Necesitas poder ejecutar comandos** (Claude Code o la app de escritorio con la carpeta conectada). Si no puedes, díselo en una línea y sigue con la ruta sin edición automática (guion + guía CapCut de `decodik-edicion`).
- Cada script dice al final qué ha hecho. Códigos de salida: 0 bien · 1 error · 2 falta algo del talento · 3 sin conexión. Si algo falla, explícalo en una frase sencilla y da el siguiente paso; no le enseñes la salida técnica.

## Pasos

Un paso cada vez. Antes de los pasos largos, avisa de cuánto va a tardar para que no piense que se ha colgado.

### 1. Mira la carpeta del vídeo
- Si todavía no hay carpeta del vídeo, créala o elígela con `references/carpetas.md`.
- Comprueba que su `02_brutos/` tiene vídeos (`.mp4`, `.mov`…), también dentro de subcarpetas.
- Si está vacía: «Deja en `<nombre de la carpeta>/02_brutos/` los clips del móvil, tal cual salen, y dime "listo"». Para hasta que lo haga.
- Dile cuántos clips has encontrado y que se ordenan por su nombre (Clip 1, Clip 2… Clip 10).

### 2. Revisa el equipo (solo la primera vez, o si algo falla)
```
uv run "$SKILL/scripts/revisar_equipo.py" --whisper
```
- Si sale «Todo listo para editar», sigue sin contarle nada técnico.
- Si sale un ✗, dale **solo** el comando de esa línea, dile que lo pegue en la terminal y que te diga «hecho». En Windows, después de instalar hay que cerrar y volver a abrir Claude. Detalle en `references/motor-edicion.md`.

### 3. Pregunta los nombres propios
En una sola pregunta: «¿Sale algún nombre propio, marca o producto en el vídeo? Escríbemelos tal cual se escriben (por ejemplo: Eileen Gu, Stanford). Si no hay, dime "no"».

### 4. Transcribe
```
uv run "$SKILL/scripts/transcribir.py" "<carpeta del vídeo>" --nombres "<nombres separados por comas>"
```
- Sin nombres, quita `--nombres`.
- La primera vez descarga el modelo de voz (~1,6 GB). Tarda alrededor de 1 s por cada segundo de vídeo.
- Lee `06_entrega/trabajo/transcripcion.md` entero. Si ves un nombre mal escrito que no te dio, pregúntale cómo se escribe y repite con `--nombres`.

### 4 bis. Formato
Con la transcripción, elige el formato (p. ej. «Hablando a cámara») y abre su skill: `references/formatos.md`. Comprueba sus **requisitos** (sobre todo los recursos de `03_recursos/`) y usa su **receta** en los pasos 6 a 6 quater.

### 4 ter. Tu estilo
Mira si el talento tiene estilo guardado y, si no, pregúntale si quiere editarlo como un vídeo que le guste (o con el estilo Decodik). Todo el paso, en `references/estilo-talento.md`. Termina con:
```
uv run "$SKILL/scripts/estilo.py" aplicar "<carpeta del vídeo>"
```
Usa en los pasos 5 a 6 quater las opciones que dice (pausa, estilo de subtítulos, textos, recursos y encuadre).

```
uv run "$SKILL/scripts/cortar.py" "<carpeta del vídeo>" --sin-video --pausa-max <la del estilo>
```
- Lee `06_entrega/trabajo/cortes.md` y cuéntale en 2-3 líneas qué ha pasado: duración antes → después y qué se quitó, sobre todo las **tomas repetidas** («Dijiste dos veces lo de la periodista; me quedo con la segunda, que se oye más clara»).
- Si el corte dura mucho más o mucho menos de lo que pide su formato o su plataforma, díselo, pero no quites frases por tu cuenta.

### 6. Subtítulos
- **Estilo:** el que dice `estilo.py aplicar` (por defecto `clave`). Cómo elegir otro y los 8 que hay: `references/estilos-subtitulos.md`.
- **Palabras clave:** lee `06_entrega/trabajo/transcripcion.md` y escribe `06_entrega/trabajo/claves.json` con la palabra que lleva el peso de cada frase (cifras, nombres, la promesa). Cómo hacerlo, en la misma guía.
```
uv run "$SKILL/scripts/subtitulos.py" "<carpeta del vídeo>" --estilo <el del estilo> [--max-palabras N, si lo dice] --sin-video
```
Lee `06_entrega/trabajo/subtitulos.srt` por encima: nombres bien escritos, nada raro.

### 6 bis. Gancho, cifras y CTA
- Propón el gancho, las cifras que cuentan la historia y el CTA en `06_entrega/trabajo/textos.json` y enséñaselos al talento en 3 líneas. Con su «ok»:
```
uv run "$SKILL/scripts/textos.py" "<carpeta del vídeo>"
```
- Cómo elegirlos: `references/textos-pantalla.md`.

### 6 ter. Recursos en pantalla
- Si hay fotos, capturas o clips en `03_recursos/`, empareja cada uno con la palabra en que el talento lo nombra, escribe `06_entrega/trabajo/recursos.json` y enséñaselo en una lista corta. Con su «ok»:
```
uv run "$SKILL/scripts/recursos.py" "<carpeta del vídeo>"
```
- Cómo elegir modo (pantalla completa o tarjeta) y momento: `references/recursos-pantalla.md`. Si algo es material de otros, avísale de los derechos en una línea.

### 6 quater. Cambio de encuadre
Por defecto, en los vídeos hablados a cámara, alterna plano normal y plano un 12 % más cerrado en cada corte, centrado en la cara:
```
uv run "$SKILL/scripts/encuadre.py" "<carpeta del vídeo>"
```
Si el talento no lo quiere, `--quitar`. En los tramos con pantalla partida no se aplica.

### 7. Render y revisión
```
uv run "$SKILL/scripts/render.py" "<carpeta del vídeo>"
```
- Tarda entre 1 y 2 veces la duración del vídeo (más si el móvil grabó en HDR).
- **Mira tú la hoja de contacto** `06_entrega/trabajo/revision/hoja.png` antes de decir nada: subtítulo legible, sin tapar la cara, nada raro en la imagen.
- Si el script dice «No pasa la revisión», no lo entregues: arregla lo marcado con ✗ (normalmente, volviendo al paso que lo causa) y vuelve a renderizar.

### 8. Entrega
Mensaje corto:

> ¡Listo! Tu vídeo está en `2026-11-15 Eileen Gu/06_entrega/video-v1.mp4` (de 1:38 a 1:01). He quitado los silencios y la toma repetida, y le he puesto subtítulos.
> Míralo en el móvil. Si algo no te convence (un corte, una palabra mal escrita…), dime el segundo y lo cambio.

- **¿Guardo tu estilo?** Si el estilo de este vídeo no es el que ya tenía guardado, añade una línea preguntando si lo guarda para los próximos vídeos (`references/estilo-talento.md`, punto 5).
- Si pide cambios, haz el cambio y renderiza otra vez: sale `video-v2.mp4` y la v1 se queda como estaba.
- Los subtítulos sueltos están en `06_entrega/subtitulos-vN.srt`, por si su red le deja subirlos aparte.

## Lo que esta versión no hace (todavía)
Música, formatos (lista, ranking…), versiones para otras redes. Si lo pide, díselo en una línea y ofrécele la guía de CapCut (`decodik-edicion`, paso 5) para añadirlo a mano.
