# Formato · Explicativo con texto · pantalla dividida

Para vídeos hablados que **explican** algo (un producto, un dato, dos opciones que se comparan, unos pasos). Cuando la persona dice lo importante, la pantalla se divide: **arriba, una palabra protagonista**; **abajo, la persona**. El resto del vídeo va a cámara. Se entiende sin sonido y nunca se le tapa la cara.

Nivel mínimo: **intermedio**. Se hace después del corte (`protocolo-corte.md`). Va **sin subtítulos** salvo que el usuario los pida: el texto de arriba ya cuenta la idea.

## 1. Las dos composiciones
| Comp. | Cuándo | Qué se ve |
|---|---|---|
| **B · dividida** | Gancho, datos, cifras, el «qué es» de cada opción, la comparación final | Arriba (960 px): **fondo premium** (`bocetos_motion.fondo_premium`): degradado negro azulado con textura (nubes de ruido, rejilla y trama de puntos, haces de luz diagonales, partículas desenfocadas alrededor, grano y viñetas) y un halo suave del acento detrás del contenido. **Nunca la toma de la persona desenfocada**, y encima el texto. Abajo (960 px): la persona |
| **A · a cámara** | Problema, opinión, humor, remate corto, frases de transición | La persona a pantalla completa. Alterna plano normal y plano cerrado (zoom 1,12) |

- **Como mucho 3 escenas B seguidas**, y siempre una A entre bloques para que se vea la cara.
- **Unas 8 escenas B en un vídeo de 60-80 s.** Menos y más largas: cada una respira.
- El gancho (0-3 s) es B y algo se mueve en los primeros 15 fotogramas.

## Cambios de pantalla y cortes
- **Los cambios de pantalla van en el corte de toma, no en la palabra.** Pasar de cámara a pantalla dividida (o al revés) en mitad de una toma, o unos fotogramas antes o después del corte, se nota como un doble salto. El storyboard avisa cuando un cambio cae en mitad de una toma y `construir_explicativo.py` pega solo cada cambio al corte más cercano (≤ 0,25 s, de `cortes.json`). Si no hay corte cerca: alarga la escena hasta el corte anterior o siguiente, o deja esa toma entera a cámara.
- Dentro de una escena dividida con varias tomas, el encuadre de la persona se vuelve a medir en cada corte (pelo siempre a 40 px de la costura).
- Los cambios de dibujo dentro de una escena sí van en la palabra, pero no a menos de ~0,6 s de un corte de toma (dos cambios seguidos): adelántalos o pásalos al corte.

## 2. Encuadre de la persona en B (lo que más se nota)
- **La cabeza va pegada a la costura:** el pelo queda a **40 px** de la línea, no media pared encima.
- Se **mide en cada escena**, porque cambia entre plano cerrado y abierto. En cada escena se toma la parte más alta a la que llega la cabeza (para que el pelo no se corte al moverse) y se desplaza la toma para que quede a 40 px. `storyboard_explicativo.py` lo mide solo.
- Nada del texto de arriba baja de la costura.

## 3. El texto de arriba: un protagonista por escena
- **Protagonista:** una palabra o dos, grande, en la fuente de la palabra clave del estilo (Anton en los estilos de Decodik). Ej.: «EQUIVOCADO», «10», «LAXANTE».
- **Línea:** una frase corta en mayúsculas pequeñas y espaciadas (Figtree 700, ~40 px, interletraje amplio) encima o debajo del protagonista.
- **Fichas:** cuando se presentan dos o más opciones, todas usan la **misma ficha** (número pequeño, nombre grande, «qué lleva» y hasta 3 líneas que entran al decirlas).
- **Comparativa final:** las fichas se juntan, la buena se marca con un marco fino de acento y se remata con la palabra del gancho (eco).
- **Nada de** chips con iconos, check y ✕ en cada línea, emojis ni burbujas: lo que suma piezas pequeñas resta categoría.
- No hay datos, cifras ni marcas que la persona no haya dicho o dado.

## 4. Color, movimiento y sonido
- **Acento** (el color de la palabra clave del estilo): una palabra, un subrayado o un marco **por escena**, nunca todo el texto.
- **Color negativo** (rojo): **una sola vez en todo el vídeo**, en la palabra más fuerte.
- **Costura:** línea fina (2 px) del color de acento, con fundido hacia los lados.
- **Entradas:** máscara y desenfoque que se aclara (0,4-0,6 s), deslizamientos lentos, barridos de luz. **Sin rebotes ni pops.** Cada elemento entra en la palabra en que se dice.
- **Producto:** si hay foto del producto o se puede recortar de la toma, entra en el gancho con un barrido de luz. Nunca dibujado si existe el real.
- **Sonido:** whoosh suave en cada entrada, un clic fino en el protagonista y un golpe grave solo en el gancho y en la comparativa. Solo efectos del usuario (ver `sonido.md`).
- **CTA:** a cámara, con «COMENTA «PALABRA»» a la altura del pecho (la palabra en el color de acento), sin tapar la cara.

## 5. Storyboard visual antes de construir
1. Escribe `06_trabajo/storyboard.json` (formato abajo) con los tiempos de `palabras.json`.
2. Genera la página:
   ```bash
   python "{SKILL}/scripts/storyboard_explicativo.py" --trabajo 06_trabajo --estilo <estilo.json>
   ```
   Crea `06_trabajo/storyboard-explicativo.html` (una tarjeta por escena con el fotograma real, el boceto de la pantalla, en qué palabra entra cada cosa y el sonido) y `storyboard-explicativo.md`. Mide la cabeza en cada escena B y la guarda en `cabeza.json`.
3. Sírvela por http para verla en el navegador (`python -m http.server` en `06_trabajo`), explícala con una línea por escena y **espera el OK**.

```json
{
 "titulo": "Tema del vídeo",
 "escenas": [
  {"n": "GANCHO", "t0": 0.0, "t1": 4.4, "comp": "B", "voz": "…",
   "motion": [[0.0, "Si", "El producto entra con un barrido de luz"], [3.4, "equivocado", "Protagonista con subrayado"]],
   "hero": "EQUIVOCADO", "linea": "SI NO NOTAS NADA", "acento": "subrayado", "producto": true, "sonido": "whoosh · golpe"},
  {"n": "FICHA 01 · NOMBRE", "t0": 32.2, "t1": 40.3, "comp": "B", "voz": "…", "motion": [],
   "hero": "NOMBRE", "linea": "QUÉ LLEVA", "lineas": ["VENTAJA", "VENTAJA", "PROBLEMA"], "acento": "ultima", "sonido": "whoosh · clics"},
  {"n": "COMPARATIVA", "t0": 59.6, "t1": 69.3, "comp": "B", "voz": "…", "motion": [],
   "comparativa": ["OPCIÓN 1", "OPCIÓN 2"], "ganadora": 1, "linea": "PARA QUÉ", "sonido": "whoosh · golpe"},
  {"n": "TRANSICIÓN", "t0": 10.0, "t1": 12.1, "comp": "A", "voz": "…", "motion": [], "zoom": true},
  {"n": "CTA", "t0": 69.4, "t1": 79.0, "comp": "A", "voz": "…", "motion": [], "cta": "PALABRA"}
 ]
}
```
`acento`: `subrayado` · `trazo` · `ultima` (la última palabra o línea en color) · `hero` (el protagonista entero) · `negativo` (la única vez en rojo). Opcional `siluetas: 10` (fila de siluetas de las que se ilumina una).

## 6. Construir
De momento el motor de gráficos (`construir_composicion.py`) no dibuja este formato: los motions se construyen a partir del storyboard aprobado con HyperFrames, siguiendo estas reglas, y se revisan con la hoja de contacto (`control-calidad.md`).
