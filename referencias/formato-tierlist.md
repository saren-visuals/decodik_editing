# Formato · TIERLIST

Para vídeos donde la persona **clasifica cosas por niveles**: deportes más o menos lesivos, ejercicios de peor a mejor, suplementos que sirven o no, zapatillas, comidas… Arriba queda fijo el título, a la altura del pecho una **tabla de niveles de colores**, y cada cosa que nombra aparece en **foto real** y **baja a su nivel** cuando da el veredicto. Se entiende sin sonido.

Nivel mínimo: **intermedio**. Se hace después del corte (`protocolo-corte.md`) y de la transcripción (`palabras.json`). Lleva subtítulos propios (no se queman con `quemar_subtitulos.py`).

## 1. Lo que se ve
| Pieza | Cómo es |
|---|---|
| **Título** (fijo, arriba) | Línea 1 serif en amarillo (`TIERLIST DE`). Línea 2 sans negra en blanco con la **palabra clave en rojo con halo** (`DEPORTES *LESIVOS*`). Si es una serie, «pt.2» en serif pequeño a la derecha, al lado de la cabeza |
| **Tabla** (bajo la barbilla) | 3-6 niveles. Columna de etiquetas de colores, de rojo (peor) a verde (mejor), letra negra de 26 px; pista casi negra. Centrada en x = 540 |
| **Foto grande** | Entra (sube y crece, 0,3 s) cuando se nombra la cosa. Se coloca en la parte de la pista que no tiene miniaturas: **nunca pisa una foto ya guardada** |
| **Guardado** | Cuando dice el veredicto, la foto se encoge y vuela a su nivel (0,45 s). Si cambia de opinión («entrenando, tranquilo… pero compitiendo, una lesión cada…»), la foto vuelve a moverse |
| **Subtítulos** | 1-3 palabras en minúscula, blanco con sombra, entre la barbilla y la tabla. Nunca acaban en «y», «la», «sin»… |
| **Fin de la tabla** | Destello rojo → naranja → blanco y el plano queda limpio para la conclusión |
| **CTA** | Píldora blanca con avatar y @usuario y botón «Follow» que pasa a «Following» |

No se toca el color de la persona ni se hace zoom. Sin música, salvo que la aporte el usuario.

## 2. Zona segura del formato
La tabla necesita más alto que la banda común de `zonas-seguras.md` (que acaba en y = 1248). Por eso este formato usa su propia zona (`plantillas/tierlist/estilo.json → zona`): **x 120-960, y 288-1450**. Queda fuera de la columna de botones de TikTok y Reels (x > 960) y del texto del post (y > 1450). Si el vídeo es solo para Shorts o hay menos niveles, se puede ajustar por vídeo.

- La barbilla se mide sola (detector de caras de OpenCV en 7 fotogramas). Subtítulo a 62 px bajo la barbilla y la tabla justo debajo.
- Si la cara está baja y las filas quedan por debajo de 92 px, el plan avisa: usa menos niveles.

## 3. Paso a paso
Todo en `06_trabajo/` del proyecto.

### 3.0 Tiempos de palabra exactos (obligatorio)
Los subtítulos y las fotos entran en la palabra, así que los tiempos tienen que cuadrar con la voz. Whisper acierta el texto, pero puede adelantar o retrasar palabras sueltas **hasta 0,6 s**, y se nota mucho.
1. Transcribe con tiempos por alineación (DTW). Con whisper.cpp:
   ```bash
   whisper-cli -m ggml-large-v3-turbo.bin -f audio16k.wav -l es -dtw large.v3.turbo -nfa -ojf -of 06_trabajo/whisper_dtw --prompt "<tema y nombres que salen>"
   ```
   `-nfa` es obligatorio: con flash attention el DTW no se calcula y todos los `t_dtw` salen a −1.
2. Ajusta los tiempos a la voz real:
   ```bash
   python "{SKILL}/scripts/alinear_palabras.py" --palabras 06_trabajo/palabras.json --audio 06_trabajo/cortado.mp4 --dtw 06_trabajo/whisper_dtw.json
   ```
   - Mide los tramos con voz del audio y corrige el retraso fijo de whisper.
   - Pega la primera palabra de cada tramo al arranque de la voz y coloca las demás dentro del tramo.
   - El original se queda en `palabras.whisper.json`.
   - Sin `--dtw`, ajusta los tiempos que ya tenga `palabras.json` (por ejemplo, los de `transcribir.py`).
3. Las `correcciones` del guion van por índice: haz el `--listar` **después** de alinear.

Los subtítulos se agrupan solos:
- 1-3 palabras, sin pasar de un punto;
- nunca acaban en «y», «el», «más»… (se estira a 4 palabras para cerrar con la palabra con contenido);
- ninguno dura menos de 0,35 s (se une al de al lado).

### 3.1 Guion de la tier list (lo escribe Claude leyendo la transcripción)
```bash
python "{SKILL}/scripts/tierlist_plan.py" --trabajo 06_trabajo --listar
```
Enseña las palabras con su índice y su tiempo. Con eso escribe `06_trabajo/tierlist-guion.json`:
```json
{
 "video": "cortado.mp4",
 "correcciones": {"32": "ahí", "33": "sí."},
 "titulo": {"lineas": ["TIERLIST DE", "DEPORTES *LESIVOS*"], "parte": "pt.2"},
 "niveles": ["MUY LESIVO", "BASTANTE LESIVO", "MODERADO", "POCO LESIVO", "PARA NADA LESIVO"],
 "elementos": [
  {"id": "natacion", "nombre": "Natación", "dice": "natación", "busqueda": "freestyle swimmer swimming pool",
   "veredictos": [{"nivel": "MODERADO", "dice": "moderado"}]},
  {"id": "boxeo", "nombre": "Boxeo", "dice": "boxeo", "busqueda": "boxing sparring boxers gloves",
   "veredictos": [{"nivel": "POCO LESIVO", "dice": "tranquilo"}, {"nivel": "BASTANTE LESIVO", "dice": "una lesión"}]}
 ],
 "seguir": {"usuario": "@usuario", "avatar": "../04_marca/avatar.png"}
}
```
- **Niveles:** de peor a mejor (el primero sale rojo y el último verde). Usa las palabras que dice la persona. Si no las dice, los de la escala más natural del tema.
- **`dice`:** las palabras exactas (como en la transcripción) en que entra la foto o en que baja a su nivel. Se buscan en orden. Si el veredicto no se dice con palabras de nivel («uno tranquilo»), elige el nivel por el sentido y pon en `dice` la palabra en que se entiende.
- **`busqueda`:** 3-5 palabras **en inglés** que describan una foto de acción reconocible (hay muchas más fotos libres en inglés).
- **`correcciones`:** solo palabras mal oídas, por índice. **`fin_dice`** (opcional): palabras en que se quita la tabla. Si no se pone, se quita al empezar la frase siguiente al último veredicto.
- **Avatar:** la foto de perfil del usuario en `04_marca/avatar.png`. Si no la da, un recorte cuadrado de su cara en el vídeo.

Enseña al usuario el guion en una tabla corta (elemento → nivel → en qué palabra) y espera su «ok».

### 3.2 Fotos (las busca la skill)
```bash
python "{SKILL}/scripts/tierlist_fotos.py" buscar --trabajo 06_trabajo
```
- Busca 8 candidatas por elemento en **Openverse** (fotos con licencia libre para uso comercial) y **Wikimedia Commons**. Si existe la variable `PEXELS_API_KEY`, también en Pexels.
- Las guarda en `03_recursos/tierlist/candidatos/<id>/` y hace la hoja `candidatos/_hoja.jpg`.
- Descarta licencias **ND** (no dejan recortar) y **NC** (no dejan uso comercial), y fotos de menos de 700 px.

**Mira la hoja** y elige por elemento la foto que mejor se entiende en pequeño:
- acción del deporte o la cosa, no retratos;
- un solo protagonista, fondo limpio y color;
- nada de carteles, logos grandes ni fotos antiguas;
- que funcione recortada en vertical (la grande es 3:4 y la miniatura cuadrada).
```bash
python "{SKILL}/scripts/tierlist_fotos.py" elegir --trabajo 06_trabajo natacion=3 boxeo=1 rugby=3@0.5,0.35
```
- `@x,y` mueve el centro del recorte (0-1) si el protagonista no está en medio.
- Si ninguna sirve, cambia la `busqueda` y repite solo ese elemento con `buscar --solo <id>`.
- Si el usuario tiene sus propias fotos, van en `03_recursos/tierlist/<id>.jpg` y mandan sobre las buscadas.
- Los créditos se apuntan en `07_entrega/creditos-fotos.txt`. **Las CC BY y CC BY-SA piden citar al autor:** dile al usuario que los pegue en la descripción del post.

### 3.3 Plan y pruebas
```bash
python "{SKILL}/scripts/tierlist_plan.py" --trabajo 06_trabajo
python "{SKILL}/scripts/construir_tierlist.py" --trabajo 06_trabajo --fotos 0.2,<entrada de cada foto>,<cada veredicto + 0.6>,<CTA + 1.5>
```
- El plan calcula los tiempos, la barbilla, la tabla, dónde se presenta cada foto grande y las posiciones de las miniaturas. Escribe `tierlist-plan.json`.
- Corrige **todos** los avisos antes de seguir: palabras no encontradas, dos fotos grandes a la vez, nivel lleno, título sobre la frente, subtítulo fuera de zona.
- Mira `06_trabajo/tierlist-pruebas/_hoja.jpg`. Comprueba que nada se pisa, que la cara está libre y que cada foto está en el nivel que dice.

### 3.4 Render
```bash
python "{SKILL}/scripts/construir_tierlist.py" --trabajo 06_trabajo --salida ../07_entrega/tierlist-v1.mp4
```
- 1080×1920 a 30 fps, voz a −14 LUFS. Un vídeo de 55 s tarda unos 3 min.
- **Efectos:** si el usuario deja en `05_musica/efectos/` un archivo con `whoosh`/`entrada` en el nombre y otro con `pop`/`clic`/`guardar`, suenan al entrar cada foto y al guardarla (el plan los detecta). Si no hay, va sin efectos.
- Saca la hoja de contacto (`control-calidad.md`) y entrega con `creditos-fotos.txt`.

## 4. Reglas
- **Una foto grande cada vez.** Si el talento encadena dos elementos sin veredicto, el plan avisa: adelanta el veredicto o junta los dos en un nivel.
- **Fotos reales siempre:** nada de iconos, emojis ni imágenes generadas. Si no hay foto libre buena, pide una al usuario.
- **Lo que no se dice no se clasifica.** Ningún elemento ni nivel que la persona no haya nombrado o dado a entender.
- **Una palabra clave en rojo en el título,** nada más en rojo salvo el primer nivel.
- Las notas del usuario se aplican a todo el vídeo y, si sirven para el formato, se apuntan aquí.
