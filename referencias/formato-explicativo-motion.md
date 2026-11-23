# Formato · Explicativo con motion graphics · pantalla dividida

Hermano de «Explicativo con texto» (`formato-explicativo-texto.md`): la misma estructura (escenas A a cámara y B divididas, la persona abajo con la cabeza a 40 px de la costura, y el mismo **fondo premium con textura** (`bocetos_motion.fondo_premium`): degradado negro azulado con nubes de ruido, halo del acento centrado en el motion, rejilla y trama de puntos que se desvanecen, dos haces de luz diagonales, partículas desenfocadas solo alrededor (nunca debajo del motion), grano de película y viñetas. **Nunca la toma de la persona desenfocada** arriba), pero **arriba la idea se explica con un motion graphic**: un dibujo que se mueve y enseña el mecanismo (el producto, un medidor, una molécula que se une, unos iconos que se dibujan, una comparativa de barras). El texto queda en etiquetas cortas.

Nivel mínimo: **intermedio**. Después del corte (`protocolo-corte.md`). Sin subtítulos salvo que se pidan.

## 1. Qué cambia respecto al formato con texto
| | Con texto | Con motion graphics |
|---|---|---|
| Protagonista de cada escena B | Una palabra grande | Un dibujo animado que explica |
| Texto | Palabra + línea | Solo etiquetas cortas (1-3 palabras) bajo el dibujo |
| Cada escena B | 1 fotograma clave | 2-3 fotogramas clave: el dibujo **evoluciona** con la voz |
| Continuidad | Fichas iguales | Los mismos dibujos vuelven con otro estado (el medidor del gancho sube en «laxante»; la molécula «Mg + ?» se completa en cada opción) |

## 2. Librería de motions (`scripts/bocetos_motion.py`)
`producto` (el real: foto o recorte; con barrido de luz, tachado o apagado) · `medidor` (arco con aguja, cualitativo) · `molecula` (esfera + enlace que se dibuja + pareja o «?») · `iconos` (iconos de línea que se dibujan con su etiqueta) · `fila` (siluetas en fila; se ilumina una) · `ondas` (cerebro con ondas que se calman) · `barra` (se llena) · `gotas` (caen hacia el intestino) · `comparativa` (barras cualitativas por criterio, marco en la ganadora) · `etiqueta` (texto corto o grande con subrayado). Parámetros en la cabecera del script.
- Trazo fino (line art), un solo color de acento por escena y el color negativo **una vez** en el vídeo.
- Sin emojis, sin iconos rellenos de stock, sin rebotes ni pops: los trazos **se dibujan**, las agujas y barras **suben**, lo que sobra **se apaga**.
- No hay datos, cifras ni marcas que la persona no haya dicho o dado. Medidores y barras son cualitativos.

## 2a-bis. Un personaje que lo vive (más movimiento)
- Cuando la frase habla de **lo que hace o le pasa a alguien** (entrena, duerme mal, le da un calambre, compra, se calma, recupera, se lo toma, sale corriendo), lo cuenta un **personaje pictograma**: cabeza redonda maciza, extremidades gruesas y redondeadas en blanco, accesorios en el color de acento. Tipo `persona` con `pose`: entrena · duerme · calambre · compra · relajado · recupera · toma · corre (`scripts/personajes_motion.py`).
- El personaje **siempre se mueve** (bucle): la barra sube y baja, da vueltas en la cama y suben las Z, tiembla con el rayo parpadeando, alarga el brazo y salta la etiqueta de precio, respira con ondas lentas, levanta los brazos mientras se carga la batería…
- El resto también se mueve: el producto flota, la aguja del medidor tiembla, las flechas de la cadena fluyen, las insignias encendidas laten y las órbitas giran despacio.
- Personaje para **acciones**; iconos en cadena para **causas y efectos**; molécula y comparativa para **el porqué**. Alterna para que no se repita.
- Una pose nueva se dibuja con el mismo estilo (pies en y 150, grosor 30, cabeza r 32) y se añade a `POSES`.
- El storyboard enseña los dibujos moviéndose (SVG animado). Al construir el vídeo, el mismo movimiento se pasa a GSAP en HyperFrames.

## 2a. Iconos que cuentan algo (poco texto)
- Cada fotograma es **una frase visual**, casi sin palabras: tipo `cadena` = icono → flecha → icono, con sello ✓ o ✗. Ej.: rayo «CALAMBRES» → bote «MAGNESIO»; gota «AGUA» → intestino ✗; «Gly» → cerebro ✓ «CALMA»; calendario «SEMANAS DURAS» → batería ✓ «RECUPERAS»; bote «10 TIPOS» → precio «EL MÁS BARATO».
- Como mucho **1-2 palabras por icono**; si el icono ya lo dice, sin palabra. En la comparativa, los criterios son iconos (estómago, luna, precio).
- Icono simple de línea, que se reconozca a la primera; si uno se puede confundir (un «músculo» que parece una mancha), cámbialo por otro más claro (batería = recuperar).

## 2b. Que no se vea vacío (sin llenarlo de cosas)
- **Rótulo de escena** arriba («01 · CITRATO», «TU SEMANA»), pequeño, en el color de acento y con dos filetes: campo `kicker` de la escena (o `titulo` del fotograma).
- **Iconos dentro de insignias de cristal** (círculo con brillo; la encendida con aro de acento).
- **Dos órbitas finas** detrás del motion, centradas en él (decoración: no llevan información).
- El motion **crece hasta llenar** la zona; si dos elementos estrechos caben más grandes uno junto al otro, se ponen lado a lado.
- Las esferas nunca quedan huecas: icono o símbolo dentro («Gly»).

## 3. Regla obligatoria: nada se solapa y todo cabe
Vale para **todo** vídeo con motion graphics, de este formato o de cualquier otro:
- **Dentro de la zona segura** (`zonas-seguras.md`). En el panel de arriba: x 192-888 (centrado en 540) e y 300-760, con 16 px de margen interior: así el motion queda dentro de la zona segura y prácticamente en el centro del panel (y 480). La luz del fondo se centra en el motion.
- **Nada se pisa:** cada elemento tiene su caja; los elementos de un fotograma se apilan sin tocarse (40 px entre ellos) y cada etiqueta vive en su columna. Las barras de la comparativa crecen hacia fuera desde la calle central, nunca hacia el texto.
- **Se lee en el móvil:** ningún texto por debajo de 26 px reales. Si no cabe, **se acorta el texto** («ENTRENAS DURO» → «ENTRENO»), no se encoge.
- **Máximo 3 elementos por fotograma.**
- `bocetos_motion.panel_svg(..., devolver_avisos=True)` lo comprueba y `storyboard_explicativo.py` enseña los avisos en la página y en la consola. **Con avisos no se enseña el storyboard: se arregla primero.** Después, revisa a ojo la tira de fotogramas con el recuadro azul de la zona segura.

## Cambios de pantalla y cortes
- **Los cambios de pantalla van en el corte de toma, no en la palabra.** Pasar de cámara a pantalla dividida (o al revés) en mitad de una toma, o unos fotogramas antes o después del corte, se nota como un doble salto. El storyboard avisa cuando un cambio cae en mitad de una toma y `construir_explicativo.py` pega solo cada cambio al corte más cercano (≤ 0,25 s, de `cortes.json`). Si no hay corte cerca: alarga la escena hasta el corte anterior o siguiente, o deja esa toma entera a cámara.
- Dentro de una escena dividida con varias tomas, el encuadre de la persona se vuelve a medir en cada corte (pelo siempre a 40 px de la costura).
- Los cambios de dibujo dentro de una escena sí van en la palabra, pero no a menos de ~0,6 s de un corte de toma (dos cambios seguidos): adelántalos o pásalos al corte.

## 4. Storyboard
Igual que en el formato con texto, pero cada escena B lleva `keyframes`:
```json
{"n": "GANCHO", "t0": 0.0, "t1": 4.4, "comp": "B", "voz": "…",
 "motion": [[0.0, "Si", "El producto entra con un barrido de luz"], [1.2, "nada", "Medidor que se queda en cero"]],
 "keyframes": [
   {"t": 0.0, "palabra": "Si", "elementos": [{"tipo": "producto"}]},
   {"t": 1.2, "palabra": "nada", "elementos": [{"tipo": "producto"}, {"tipo": "medidor", "valor": 0, "etiqueta": "EFECTO"}]}],
 "sonido": "whoosh suave · tic · golpe grave"}
```
```bash
python "{SKILL}/scripts/storyboard_explicativo.py" --trabajo 06_trabajo --storyboard storyboard-motion.json --salida storyboard-motion --estilo <estilo.json>
```
Cada tarjeta enseña el boceto final y la **tira de fotogramas clave** (en qué palabra cambia el dibujo), con la zona segura marcada.

## 5. Construir
Con el storyboard aprobado (y `cabeza.json`, que deja `storyboard_explicativo.py`):
```bash
python "{SKILL}/scripts/construir_explicativo.py" --trabajo 06_trabajo --storyboard storyboard-motion.json --estilo <estilo.json>
cd 06_trabajo/explicativo && npx hyperframes check . && npx hyperframes snapshot . --at <un tiempo por fotograma clave> --no-end
npx hyperframes render . -o ../con_motion.mp4
python "{SKILL}/scripts/mezclar.py" --video 06_trabajo/con_motion.mp4 --voz 06_trabajo/voz_cortada.wav --out 07_entrega/<tema>.mp4
```
- Escenas A a pantalla completa (zoom 1,12 si lo marca el storyboard); escenas B con el motion arriba y la persona abajo, pelo a 40 px de la costura; cortes secos.
- Los dibujos animados se colocan en el instante exacto de cada fotograma (protocolo `hf-seek` de HyperFrames): el vídeo se mueve igual que el storyboard.
- Cada fotograma clave entra en su palabra con fundido y desenfoque que se aclara (0,45 s). Debe quedarse en pantalla al menos 1 s: si `check` avisa de `line_unread`, adelanta su palabra en el storyboard.
- CTA: tarjeta oscura con «COMENTA» y la palabra en el color de acento entre comillas rectas (Anton no tiene «»), a la altura del pecho y dentro de la zona segura (ancho ≤ 480 px por la columna de botones).
- Aviso esperado de `check`: `container_overflow` de `#talento` (la toma sobresale a propósito por debajo del recorte). Cualquier otro aviso se arregla.
- Revisa la hoja de contacto con la regla del punto 3 antes de renderizar.
