# Estilos de subtítulos

8 estilos DECODIK, sacados de los reels de referencia (`docs/investigacion-estilos-marca-personal.md`). **Por defecto: Clave.**

Todos usan los **colores de la marca** (DECODIK por defecto: texto Crema #F8F2E9, contorno Tinta #021020, palabra clave Amarillo Decodik #F7CE07; nunca blanco ni negro puros). Ver `references/marca-decodik.md`.

| Estilo | Cómo se ve | Palabra clave | Úsalo para |
|---|---|---|---|
| `clave` | **Estilo DECODIK:** Figtree ExtraBold, Crema, contorno fino Tinta, 1-3 palabras a media altura | **Amarillo Decodik**, algo más grande | Por defecto; hablar a cámara |
| `serif` | Serif cursiva, 1-4 palabras | **grande, recta y en negrita** | Historias, reflexión, el estilo de Jesús |
| `frase` | Frase entera en 1-2 líneas, pequeña (Figtree SemiBold) | — | Storytelling, pizarra, explicaciones largas |
| `impacto` | MAYÚSCULAS cursivas con contorno (Inter Display Black), 1-3 palabras | **Menta** | Opinión, entrevistas, puntuaciones |
| `caja` | Texto Tinta sobre caja Crema (Figtree Bold), 1-4 palabras | — | Listas, POV, aspecto «nativo de Instagram» |
| `condensada` | MAYÚSCULAS en Anton, 1-3 palabras | **Amarillo Decodik** | Ganchos con fuerza, tono de cartel |
| `mixta` | Frase pequeña (Figtree Medium) | **en negrita** (Figtree Black) | Conversación, dos personas |
| `minimo` | Letra pequeña centrada (Figtree Medium), frases largas | — | Vídeo de frase, vlog |

**Una sola palabra destacada por subtítulo** (regla de la marca): si en un bloque caen dos claves separadas, solo se resalta la primera.

## Cómo elegir el estilo

- Si el talento no dice nada: **`clave`**.
- Si su vídeo es una historia o una reflexión, ofrécele `serif` en una línea («¿Lo quieres más de historia, con letra serif?»).
- Si nombra un estilo o enseña uno que le gusta, usa el más parecido de la tabla. En marca personal, eso lo hace el paso «Tu estilo» (`references/estilo-talento.md`), que además lo guarda para los próximos vídeos.
- Si pide un color, usa el tono DECODIK equivalente (tabla de `marca-decodik.md`) con `--color-clave HEX`. En UGC con guía de marca en `04_marca/`, o si el talento tiene identidad propia en `perfil-talento.md`, escribe `marca.json` (ver `marca-decodik.md`).
- Para enseñarle cómo queda antes del render: `subtitulos.py` sin `--sin-video` crea `06_entrega/trabajo/subtitulado.mp4`.

## Palabras clave (las eliges tú)

Antes de generar los subtítulos, lee `06_entrega/trabajo/transcripcion.md` y escribe `06_entrega/trabajo/claves.json`:

```json
{"claves": ["olímpica#1", "Eileen Gu", "62 créditos", "veterinaria", "elegir#2"]}
```

- **Una por frase como mucho**, la que lleva el peso: una cifra, un nombre, la promesa, el contraste, el verbo fuerte. Si todo se resalta, no se resalta nada: en el caso A fueron 20 claves para 61 s.
- Puede ser una palabra o varias seguidas («62 créditos», «lo elige todo»).
- **`#n`** marca solo la n-ésima vez que se dice en el vídeo **ya cortado** («olímpica#1»).
- Copia las palabras tal cual salen en la transcripción (las tildes y mayúsculas dan igual).
- Si no escribes `claves.json`, se resaltan solas las cifras y los nombres que se pasaron con `--nombres`.

El script dice cuántas palabras ha resaltado. Si son 0 con una lista llena, alguna clave no coincide con la transcripción: revísala.

## Reglas del motor (no hace falta tocarlas)

- Los bloques no terminan en palabras de enlace («y», «de», «que», «en lo»…) si la frase sigue: pasan al bloque siguiente.
- En `clave`, `serif`, `impacto`, `caja` y `condensada` se quitan puntos y comas al final; en `frase`, `mixta` y `minimo` se deja la puntuación.
- Ningún bloque dura menos de 4 fotogramas. Base del texto al 66 % de la altura (zona segura de TikTok y Reels); `minimo` va centrado.
- En vídeos HDR los colores del texto se convierten para verse igual que en SDR (ver «Color» en `motor-edicion.md`).
- `serif` usa de momento **Georgia**, la que trae Windows y Mac. Pendiente de elegir una serif libre para que sea igual en todos los equipos.
