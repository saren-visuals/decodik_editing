# Plantilla · Ficha de estilo

Se rellena en la fase 4 del modo UGC y se guarda en `06_entrega/ficha-estilo.md`. Dice **cómo se va a editar** el vídeo de la marca, en palabras que el talento entiende y con los valores que usa el motor (fase 6).

## De dónde sale cada decisión (en este orden)
1. Lo que pida el **brief** (sección de estilo, ejemplos, «sí / no»). Manda sobre todo.
2. La **guía de marca** de `04_marca/` (colores, letras, logo, tono). Manda sobre la marca DECODIK (`references/marca-decodik.md`).
3. Lo que el talento haya pedido o tenga en `perfil-talento.md`.
4. Lo que el brief no dice: **UGC natural** (parece hecho por un creador, no por la marca) con la marca DECODIK, y **lo que dependa de la marca va a huecos** (música, logo). Nunca decidas tú la música.

## Estilos base
| Estilo | Cuándo | Cómo se edita |
|---|---|---|
| **UGC natural** (por defecto) | El brief no pide otra cosa o pide «que parezca tu vídeo» | Formato «Hablando a cámara»; subtítulos `clave`; recursos y pantallas de producto por corte seco o pantalla partida; gancho y CTA escritos solo si el brief no los prohíbe; sin efectos de anuncio |
| **Problema → solución** | Producto que resuelve algo concreto | Igual, con el problema en el gancho y el producto como giro |
| **Unboxing / primera impresión** | Lanzamiento o envío de producto | Planos de detalle cortos; reacción a cámara; subtítulos `caja` o `clave` |
| **El que pida la marca** | El brief describe un estilo o da ejemplos | Lo más parecido con las piezas del motor; si algo no se puede, dilo |

---

```markdown
# Ficha de estilo · <Marca> · <Producto>

_Hecha a partir de: ficha-campana.md, <guía de 04_marca o «sin guía de marca»> · <fecha>_

## Estilo
- **Estilo base:** <UGC natural / …> — <por qué, citando el brief>
- **Formato de edición:** <decodik-formato-…>

## Cómo se verá
| Elemento | Decisión | De dónde sale |
|---|---|---|
| Ritmo | | |
| Subtítulos (estilo, tamaño, posición) | | |
| Palabra clave y colores | | |
| Texto en pantalla (gancho, cifras, CTA) | | |
| Recursos y pantallas de producto | | |
| Música | | |
| Logo | | |
| Señalización | | |
| Versiones (ganchos, formatos, sin subtítulos…) | | |

## Valores para el motor (fase 6)
- `subtitulos.py --estilo …`
- `marca.json`: <colores de la guía de la marca, o «sin marca.json: marca DECODIK»>
- `textos.json`: <gancho / cifras / CTA: sí o no>
- `recursos.json`: <modos y frecuencia>
- `encuadre.py`: <sí / --quitar>

## Pendiente de la marca
- …
```
