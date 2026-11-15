# Marca DECODIK · colores, fuentes y recursos

Usa esta marca por defecto en todo lo que generes: subtítulos, textos en pantalla, gráficos, miniaturas, portadas, PDFs y slides.

## Orden de preferencia
1. Lo que el talento pida de forma explícita (un código hex, una fuente concreta).
2. En modo UGC: la guía de la marca que haya en `04_marca/`. La marca del cliente manda sobre DECODIK.
3. La identidad propia del talento, si está en `perfil-talento.md`.
4. Si no hay nada de lo anterior: la marca DECODIK (este archivo).

**Cómo se aplica en los scripts:** por defecto usan la marca DECODIK (`scripts/marca.py`). Si se da el caso 1, 2 o 3, escribe `06_entrega/trabajo/marca.json` con los colores que mandan (ver abajo) y los scripts lo usan. Si el talento pide un color solo para la palabra clave, basta con `--color-clave HEX`.

```json
{"origen": "04_marca/guia-zancada.md", "colores": {"texto": "F4F1EA", "contorno": "1A1A1A", "clave": "0E7C66"}}
```
Claves posibles: `texto`, `contorno`, `clave`, `caja`, `texto_caja`, `acento2`. Las que no pongas se quedan con el valor DECODIK.

## Colores
Cuando el talento diga un color por su nombre, usa SIEMPRE el tono DECODIK equivalente:

| Si dice… | Usa | Hex |
|---|---|---|
| amarillo | Amarillo Decodik | #F7CE07 |
| amarillo claro / pastel | Amarillo suave | #FFEF88 |
| amarillo para etiquetas/píldoras | Amarillo píldora | #FADE4E |
| azul / azul oscuro / azul noche | Azul noche | #010F20 |
| azul medio | Azul medio | #0D2334 |
| azul claro / celeste | Azul cielo | #ACD0DF |
| verde / menta / turquesa claro | Menta | #5DD7B9 |
| verde claro / menta suave | Menta suave | #B9E8E4 |
| verde azulado / petróleo | Azul petróleo | #163843 |
| rosa / fucsia | Rosa Decodik | #FF5FA2 |
| rosa claro / pastel | Rosa suave | #F799C4 |
| blanco | Crema | #F8F2E9 |
| blanco papel / fondo claro | Papel | #F7F1E8 |
| negro / texto oscuro | Tinta | #021020 |

- Nunca uses blanco puro (#FFFFFF) ni negro puro (#000000): usa Crema y Tinta.
- Si pide un color que no está en la tabla (rojo, naranja, morado…), usa el DECODIK más cercano (rojo → Rosa Decodik) y díselo en una línea: «He usado el rosa Decodik; si quieres rojo puro, dímelo».
- Contraste: texto claro sobre Azul noche, Azul medio o Azul petróleo; texto Tinta sobre Amarillo, Menta, Crema o Papel.
- Amarillo solo para destacar: una palabra clave por subtítulo o un elemento por pantalla.

## Fuentes
| Uso | Fuente |
|---|---|
| Subtítulos y texto general | Figtree (ExtraBold 800) |
| Ganchos y textos grandes en pantalla | Anton (en mayúsculas) |
| Etiquetas, rótulos pequeños y fechas | Bebas Neue (en mayúsculas) |
| Logotipo «decodik.» (solo el logo) | Fraunces Bold |

## Estilo de subtítulos por defecto
- Figtree ExtraBold, color Crema, contorno fino Tinta.
- Palabra clave en Amarillo Decodik.
- Dentro de la zona segura de 9:16 (lejos de la interfaz de la red).

En la skill es el estilo `clave` (el de por defecto). Los otros 7 estilos de `references/estilos-subtitulos.md` usan los mismos colores DECODIK; son alternativas que el talento puede pedir.
