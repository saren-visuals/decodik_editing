# Estilos de subtítulos

8 estilos DECODIK, sacados de los reels de referencia (`docs/investigacion-estilos-marca-personal.md`). **Por defecto: Clave.**

| Estilo | Cómo se ve | Palabra clave | Úsalo para |
|---|---|---|---|
| `clave` | 1-3 palabras, blanco grueso (Inter Display Black), a media altura | **amarilla y algo más grande** | Hablar a cámara: el más usado |
| `serif` | Serif cursiva, 1-4 palabras | **grande, recta y en negrita** | Historias, reflexión, el estilo de Jesús |
| `frase` | Frase entera en 1-2 líneas, pequeña (Inter SemiBold) | — | Storytelling, pizarra, explicaciones largas |
| `impacto` | MAYÚSCULAS cursivas con contorno, 1-3 palabras | **verde** | Opinión, entrevistas, puntuaciones |
| `caja` | Texto negro sobre caja blanca (Figtree Bold), 1-4 palabras | — | Listas, POV, aspecto «nativo de Instagram» |
| `condensada` | MAYÚSCULAS altas y estrechas, 1-3 palabras | **amarilla** | Ganchos con fuerza, tono de cartel |
| `mixta` | Frase pequeña (Figtree Medium) | **en negrita** (Figtree Black) | Conversación, dos personas |
| `minimo` | Letra pequeña centrada (Inter Medium), frases largas | — | Vídeo de frase, vlog |

## Cómo elegir el estilo

- Si el talento no dice nada: **`clave`**.
- Si su vídeo es una historia o una reflexión, ofrécele `serif` en una línea («¿Lo quieres más de historia, con letra serif?»).
- Si nombra un estilo o enseña uno que le gusta, usa el más parecido de la tabla.
- Si tiene color de marca, úsalo para la palabra clave con `--color-clave HEX`.
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
