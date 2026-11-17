---
name: decodik-formato-hablando-a-camara
description: Formato DECODIK «Hablando a cámara»: el talento cuenta una idea, una historia o una opinión mirando a cámara, con subtítulos de palabra clave, gancho escrito, cifras grandes, recursos que aparecen cuando los nombra (pantalla completa, tarjeta o pantalla partida) y CTA final. Es el formato más usado del banco DECODIK. Lo usa decodik-editor cuando el talento elige este formato o su vídeo es él hablando a cámara. Úsala con «edita mi vídeo hablando a cámara», «es un vídeo hablado», «cuento una historia a cámara», «doy mi opinión», «estilo Jesús».
---

# Formato · Hablando a cámara

Este formato lo edita `decodik-editor` (corte, subtítulos, textos, recursos y render, con la marca DECODIK). Esta skill dice **qué es, qué hay que grabar y cómo se edita**; los valores para los scripts están en `formato.json`.

## Qué es
El talento, de cerca, cuenta **una sola idea** mirando al objetivo: un dato, una historia, una opinión o un consejo de su mundo. Sin aire entre frases, con lo importante escrito y con imágenes que aparecen justo cuando las nombra. Quien mira siente que se lo cuentan a él.

## Cuándo usarlo
- Para dar **valor, opinión o autoridad** en el nicho del talento, o contar una **historia** (suya o de su deporte).
- Para cualquier perfil (deportista, fan, analista, fitness…). Es el formato más fácil para empezar.
- **No** si no hay voz (vídeo de frase, vlog con música) ni si lo importante es una lista larga (mejor «Lista rápida» cuando exista).

## Qué grabar (requisitos)
| Material | Obligatorio | Detalle |
|---|---|---|
| Clips del talento en `02_brutos/` | **Sí** | Vertical, móvil a la altura de los ojos, luz de frente, sin ruido de fondo. Un clip por frase o por idea: mejor 10-15 clips cortos que uno largo. Si se equivoca, que repita la frase entera (la skill se queda con la mejor toma). |
| Recursos en `03_recursos/` | **Sí, al menos 3** (recomendado 5-8 para 1 minuto) | Fotos, capturas o clips de **lo que cuenta**: el lugar, el entreno, el partido, el producto, la persona de la que habla, una noticia. Mejor en vertical; los horizontales también valen. Vídeos largos (un reportaje, un partido) también: la skill elige los fragmentos. |

**Si faltan recursos:** antes de editar, pídeselos en un mensaje, con una lista **adaptada a lo que cuenta** (sácala de la transcripción: «Para "Stanford", una foto del campus; para "62 créditos", una captura de tu expediente…»). Si no tiene o no quiere, **edita igual** y avísale en una línea de que quedará más plano: el ritmo lo darán solo el cambio de encuadre, el gancho y las cifras.

Si un recurso es de otros (un documental, una retransmisión, fotos de un famoso), avisa en una línea de los derechos (la red puede silenciar o bloquear el vídeo). Lo decide el talento.

## Estructura
| Momento | Qué pasa | En pantalla |
|---|---|---|
| 0-3 s (gancho) | La frase que engancha, sin saludos. Voz desde el segundo 0 | Gancho escrito arriba (Helvetica Now Display, palabra fuerte en amarillo). Si hay una cifra, cifra gigante |
| Cuerpo | La idea, con un ejemplo suyo | Subtítulos `clave`; un recurso cada 6-8 s cuando nombra algo; cifras que cuentan la historia |
| Cierre | La idea que se queda y **un solo** CTA | CTA escrito arriba los últimos 2,5 s |

## Receta de edición
Sigue `decodik-editor/references/edicion-basica.md` con estos valores (también en `formato.json`):

1. **Corte:** sin aire, mejor toma (`cortar.py`, por defecto).
2. **Subtítulos:** estilo `clave` (marca DECODIK). Para historias o reflexión, ofrece `serif`. Una palabra clave por frase en `claves.json`.
3. **Gancho, cifras y CTA:** siempre gancho y CTA; 1-3 cifras solo si cuentan la historia (`textos.json`).
4. **Recursos** (`recursos.json`, guía `decodik-editor/references/recursos-pantalla.md`):
   - Uno cada **6-8 s** como mucho, en la palabra en que lo nombra.
   - **Pantalla partida** (estilo Jesús) para fragmentos que acompañan una frase entera: **3 s o más**, dentro de un mismo plano del talento.
   - **Pantalla completa** de 1,2-2 s para planos rápidos o cuando el plano del talento es corto.
   - **Tarjeta** para fotos, capturas y datos que se leen.
   - Varía los modos: no más de dos seguidos iguales.
5. **Encuadre:** cambio de encuadre alterno en los cortes (`encuadre.py`, ×1,12).
6. **Música:** no (la voz manda). Si el talento la pide, muy baja.

## Reglas propias del formato
- **La cara del talento no se tapa nunca** (tarjetas fuera de la cara; el motor lo garantiza).
- **Sin cambios bruscos:** ningún recurso entra o sale junto a un corte; la pantalla partida dura al menos 2,5 s dentro de un tramo (el motor lo garantiza; si no hay hueco, elige otra palabra o modo).
- El color de clips y recursos no se convierte nunca.
- Una sola idea por vídeo. Si el corte dura más de 90 s, díselo: probablemente son dos vídeos.

## Ejemplo
`caso-a` (Eileen Gu, 61 s): 20 palabras clave, gancho «No eligió una sola etiqueta», cifras 62 y 36, CTA «Guárdalo para cuando te pregunten qué eres», 6 recursos de un reportaje (2 partidas de 3 s, 3 pantallas completas, 1 tarjeta) → `video-v17.mp4`, aprobado por Santiago.

## De dónde sale
Patrón observado en los 21 reels «Hablar a cámara» del banco DECODIK (`docs/investigacion-estilos-marca-personal.md`, sección «Hablar a cámara en detalle»). Diseño y textos propios de DECODIK.
