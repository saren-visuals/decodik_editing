# Pasada de gráficos y B-roll (intermedio y avanzado)

Todo es código y determinista: tú escribes el plan en JSON, el script genera el proyecto HyperFrames y HyperFrames lo renderiza fotograma a fotograma. **No improvises HTML a mano**: si necesitas un gráfico que el script no tiene, añádelo al script.

## 1. Primero el plan, sin construir
Escribe `06_trabajo/plan.json` y enséñalo al usuario como tabla (lo que dice · tiempo · qué aparece · por qué). **Espera la aprobación** (en guiada y en rápida). Cambiar una fila cuesta una frase; cambiar un render cuesta una pasada.

Tipos disponibles (formato completo en la cabecera de `{SKILL}/scripts/construir_composicion.py`):

| Tipo | Qué es | Campos |
|---|---|---|
| `tarjeta` | Titular + texto corto | `titulo`, `texto` |
| `lista` | Lista con checks que se marcan al decirlos | `titulo`, `items` [{`texto`, `ancla` o `t`}] |
| `cifra` | Número grande + texto | `valor`, `texto` |
| `pildora` | Etiqueta pequeña (Día 1, Nuevo, En directo) | `texto` |
| `titular` | Palabra o frase gigante (gancho) | `texto` |
| `imagen` | Captura o foto real con pie | `src`, `pie` |
| `broll` | Clip a pantalla completa (la voz sigue) | `src` |
| `escena` | Pantalla completa con fondo de marca y lista | `titulo`, `items` |
| `cta` | Llamada a la acción final | `texto`, `sub` |
| `palabra_detras` | Palabra gigante detrás de la cabeza (avanzado) | `texto` |
| `escena_texto` | **Premium.** Pantalla completa (noche o crema con grano, alternando) con etiqueta en mayúsculas + palabra serif gigante; cada palabra entra **cuando se dice** | `lineas` [{`texto`, `rol`: etiqueta · clave · linea3, `acento`}], `fondo`, `alineacion` |
| `llamada` | **Premium.** Frase pequeña + palabra serif en caja menta, junto a la cabeza (nunca sobre la cara) | `frase`, `clave` |
| `capitulo` | **Premium.** Tarjeta «PARTE 01 · Título» a pantalla completa (long form) | `etiqueta`, `titulo` |
| `final` | **Premium.** Tarjeta noche «SIGUE PARA MÁS» al terminar | `texto` |

Reglas del plan:
- **Ancla cada gráfico a una palabra** con `"ancla": "palabra"` (el tiempo sale de `palabras.json`). Usa `t` solo si no hay palabra.
- La cantidad sale de la entrevista y de `graficos.densidad` del estilo. Tipos permitidos: los de `graficos.tipos` del estilo + imagen, broll, cta.
- El gancho (0-2 s) siempre lleva algo: `titular`, `pildora` o el zoom de entrada.
- **Tiempo en pantalla**: al menos 0,5 s + 0,3 s por palabra; la última línea del vídeo, al menos 2 s. En Espacial, la entrada dura 1,1 s: no hagas tarjetas de menos de 1,6 s.
- **Centro horizontal:** gráficos y subtítulos se centran en `subtitulos.centro_x` del estilo (o `graficos.centro_x` si existe). **Regla de Decodik: todo centrado (540) en todos los estilos.** `check` puede avisar de que un elemento ancho roza la columna de botones de TikTok: es esperado; si molesta, acorta el texto antes que descentrar. 450 (banda 120-780) solo si el usuario lo pide expresamente.
- Mientras hay un gráfico «pecho», los subtítulos se ocultan solos. Si un gráfico es solo decoración, ponlo «arriba».
- Imágenes y vídeos: solo del usuario, de la marca o con licencia. Rutas relativas a `06_trabajo/`.

## 2. Construir
```bash
python "{SKILL}/scripts/subtitulos.py" --palabras 06_trabajo/palabras.json --frases 06_trabajo/frases.txt --estilo "{SKILL}/estilos/<id>.json" --out 06_trabajo/subtitulos
python "{SKILL}/scripts/construir_composicion.py" --trabajo 06_trabajo --estilo "{SKILL}/estilos/<id>.json" --modo final
cd 06_trabajo/graficos
npx hyperframes check .
```
- `check` revisa zona segura, solapes, contraste y tiempos de lectura. **Errores = arréglalos** (cambia el plan, no el HTML). Los avisos de contraste sobre fondos muy claros se arreglan pasando el gráfico a `arriba` o usando tarjeta.
- Revisión visual: `npx hyperframes snapshot . --at <tiempo de cada gráfico> --no-end` y mira la `contact-sheet.jpg` con la lista de `control-calidad.md`.
- En revisión guiada, enséñale la hoja de contacto y espera «siguiente».

## 3. Render
```bash
npx hyperframes render . -o ../con_graficos.mp4
```
Después, `mezclar.py` con `--video 06_trabajo/con_graficos.mp4` (ver `sonido.md`).

## Estilo Premium: reglas extra
- Escenas de texto el 30-40 % del tiempo; nunca dos seguidas con el mismo fondo (el script alterna noche/crema solo).
- Cada escena de texto entra con un **barrido de color suave (0,22 s)** de abajo arriba. Entre planos de cámara, corte.
- El texto de la escena **es la voz**: escribe en `lineas` las palabras tal como se dicen (las etiquetas que no se dicen entran justo después).
- Ritmo short form: 16-20 cambios de escena por minuto, plano mediano ≈ 2,8 s. Long form: bloques cámara/gráfico de ≈ 8 s, capítulos con `capitulo`.
- El script deja `06_trabajo/efectos_sugeridos.json` (whoosh en cada barrido, clic en cada palabra serif, impacto en capítulos): quita los efectos que el usuario no tenga en `05_musica/efectos/` (ver `sonido.md`) y pásalo a `mezclar.py --efectos`.

## Regla para todo gráfico o motion graphic
Ningún icono, texto ni gráfico se pisa con otro, y todo entra en pantalla y en la zona segura, con margen. Ningún texto por debajo de 26 px: si no cabe, se acorta. Se comprueba en el storyboard (avisos automáticos) y otra vez en la hoja de contacto del vídeo.

## Formato «Explicativo con motion graphics · pantalla dividida»
Igual que el de texto, pero arriba explica un dibujo animado (producto, medidor, molécula, iconos, comparativa…): ver `{SKILL}/referencias/formato-explicativo-motion.md`.

## Formato «Explicativo con texto · pantalla dividida»
Tiene sus propias reglas (texto protagonista arriba sobre la toma desenfocada, cabeza pegada a la costura, fichas y comparativa): ver `{SKILL}/referencias/formato-explicativo-texto.md`.

## Pantalla dividida: panel explicativo
En pantalla dividida el panel de arriba se rellena con capturas o vídeos reales si el usuario los tiene; si no, con los motions explicativos de `scripts/motions.py`. Ver `avanzado.md`.

## 4. Zooms
Si el estilo tiene `ritmo.zoom_max`, el script mete un punch-in suave en el gancho. Para más, añade al plan `"zooms": [{"t": 7.0, "a": 1.05, "dur": 1.6}, {"t": 9.3, "a": 1.0, "dur": 1.4}]`: curvas, nunca saltos, sin pasar del máximo del estilo.

## 5. Avanzado: palabra detrás de la cabeza
Ver `avanzado.md`. Orden: recorte del sujeto → `construir_composicion.py --modo detras` → render `.mov` → `componer_base.py` → `construir_composicion.py --modo final` (usa la base nueva sola) → render.

## Trampas conocidas de HyperFrames
- No edites a mano el HTML generado: el siguiente `construir_composicion.py` lo sobrescribe.
- Las fuentes y GSAP van en `graficos/assets/`: el render no necesita internet.
- Si el render se queda colgado en un ordenador sin tarjeta gráfica, prueba con menos efectos de desenfoque (estilo Golpe o Editorial) o en 1080p.
