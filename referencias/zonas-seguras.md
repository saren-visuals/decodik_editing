# Zonas seguras (lienzo 1080×1920)

Las redes dibujan encima del vídeo: barra de estado y búsqueda arriba, texto, usuario y botones abajo, y la columna de botones a la derecha. Todo lo que hay que leer (subtítulos, gráficos, logos, CTA) va dentro de la **banda común** que dejan libre TikTok, Instagram Reels y YouTube Shorts a la vez. Es la misma que comprueba `npx hyperframes check` (aviso `outside_safe_zone`).

| | Valor (1080×1920) |
|---|---|
| Arriba | desde y = 288 px |
| Abajo | hasta y = 1248 px |
| Izquierda | desde x = 120 px |
| Derecha | hasta x = 888 px, y **hasta x = 780 px por debajo de y = 840** (la columna de botones de TikTok se ensancha) |

En 4K (2160×3840) multiplica por 2. Fuera de la banda solo puede haber textura o decoración.

Si el vídeo es solo para una red, se puede ser menos estricto y comprobar solo esa: `npx hyperframes check . --safe-zone reels` (o `tiktok`, `shorts`).

## Reglas de posición
- **Cara y barbilla libres**, también con el zoom máximo.
- **Todo centrado en horizontal (x = 540), en todos los estilos:** subtítulos al fondo de la banda (centro en y ≈ 1160) y gráficos «pecho» y «arriba». Es la regla de Decodik aunque la columna de botones de TikTok (x > 780 por debajo de y = 840) pueda rozar el borde derecho de un texto ancho: en ese caso, **acorta o parte el texto** (subtítulos de 1-3 palabras, tarjetas de unos 15-18 caracteres por línea), no lo descentres.
- **Gráficos «pecho»** apoyados en el borde inferior de la banda (y = 1248) y creciendo hacia arriba. Mientras están, los subtítulos se ocultan solos.
- **Gráficos «arriba»** desde y = 288. Úsalo para píldoras y titulares, o si la cara está baja.
- Si un gráfico alto (lista larga) llega a la cara, pártelo en dos o usa una escena a pantalla completa.
- El CTA final, entero dentro de la banda.
