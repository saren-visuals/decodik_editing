# Tu estilo · el estilo de edición del talento (marca personal)

Paso «4 ter» de `references/edicion-basica.md`, después de elegir el formato y antes de cortar. Sirve para que el vídeo salga como a él le gusta, y para que ese estilo se quede guardado para los siguientes vídeos.

Solo en **marca personal**. En UGC el estilo lo decide la ficha de estilo (`references/ficha-estilo.md`): manda la marca.

`$SKILL` = la carpeta de esta skill. `<carpeta del vídeo>` = la ruta de `AAAA-MM-DD Nombre`.

## 1. Mira si ya tiene estilo guardado
```
uv run "$SKILL/scripts/estilo.py" ver "<carpeta del vídeo>"
```

**Si tiene estilo guardado**, pregunta solo esto, con la tabla que sale:
> ¿Uso tu estilo de siempre?
> <tabla>
> Si quieres otro para este vídeo, pásame un vídeo que te guste o dime qué cambiar.

- «Sí» → ve al paso 4 de esta guía (aplicar).
- Quiere cambiar algo concreto («subtítulos en rosa», «sin cambio de encuadre») → escribe `estilo.json` con ese cambio (paso 3) y aplica.
- Trae una referencia → paso 2.

**Si no tiene estilo guardado**, pregunta una sola cosa:
> ¿Quieres que lo edite como un vídeo que te guste? Déjalo en `<nombre de la carpeta>/03_recursos/referencia/` (mejor el vídeo descargado o 2-3 capturas que un enlace) y dime «listo».
> Si no, lo edito con el estilo Decodik.

- «No» / «el de Decodik» → paso 4 (sale el estilo DECODIK por defecto).
- Solo da un enlace: intenta abrirlo. Si no puedes descargar el vídeo (Instagram y TikTok casi nunca dejan), díselo en una línea y pídele el archivo o capturas. No pares el vídeo por esto: si no puede, sigue con el estilo Decodik.

## 2. Saca el estilo de la referencia
```
uv run "$SKILL/scripts/referencia.py" "<carpeta del vídeo>"
```
Mira **tú** las hojas `06_entrega/trabajo/referencia/hoja-N.jpg` y lee `referencia.json`. Fíjate en:

| Qué miras | Qué decides | Cómo |
|---|---|---|
| Letra, tamaño y cuántas palabras salen a la vez | `subtitulos` | El más parecido de los 8 (`references/estilos-subtitulos.md`). Cursiva serif → `serif`; mayúsculas con contorno → `impacto`; texto sobre caja → `caja`; frase entera pequeña → `frase` o `minimo`; 1-3 palabras con una de color → `clave` o `condensada` |
| Colores del texto y de la palabra resaltada | `colores` | Hex aproximado de `clave` y `texto` (y `caja` si hay caja). El script los pasa al tono DECODIK más cercano |
| `segundos_por_plano` y `ritmo` del JSON | `pausa_max` | Rápido → 0.2 · medio → 0.3 · pausado → 0.45 |
| Texto grande arriba al empezar, números grandes, llamada a la acción al final | `gancho`, `cifras`, `cta` | `true` si los ves |
| Fotos o clips encima: a toda pantalla, en tarjeta o partida arriba/abajo | `recursos` | `completo`, `tarjeta`, `partida` o `mixto` si combina |
| Planos que se acercan en los cortes | `encuadre` | `true` si cambia el tamaño del plano |

Si la referencia hace algo que el motor no tiene (música, transiciones, efectos, emojis), apúntalo en `notas` y díselo en una línea: «Eso todavía no lo hago; lo puedes añadir en CapCut».

**Solo se imita el estilo**, nunca el contenido: ni frases, ni música, ni imágenes del vídeo de referencia.

## 3. Escribe `06_entrega/trabajo/estilo.json`
```json
{
  "origen": "referencia: reel-jesus.mp4",
  "subtitulos": "serif",
  "colores": {"clave": "F7CE07", "texto": "F8F2E9"},
  "pausa_max": 0.2,
  "gancho": true,
  "cifras": true,
  "cta": false,
  "recursos": "partida",
  "encuadre": true,
  "notas": "La referencia lleva música y emojis: no los hago todavía."
}
```
- Las claves que no pongas se quedan como en el estilo DECODIK.
- `colores` admite `texto`, `contorno`, `clave`, `caja`, `texto_caja`, `acento2`.
- Si el talento pide un color exacto («este hex, no el de Decodik»), añade `"colores_exactos": true`.

Enséñale la tabla que saca el paso 4 y espera su «ok». Si cambia algo, edita `estilo.json` y vuelve a aplicar.

## 4. Aplica
```
uv run "$SKILL/scripts/estilo.py" aplicar "<carpeta del vídeo>"
```
- Escribe `marca.json` con los colores y dice qué opciones usar en cada paso. Úsalas tal cual:
  - paso 5 `cortar.py --pausa-max …`
  - paso 6 `subtitulos.py --estilo …`
  - paso 6 bis: en `textos.json` pon solo lo que el estilo lleva (gancho, cifras, CTA)
  - paso 6 ter: en `recursos.json` usa el modo preferido cuando quepa (las reglas de cara y de cortes de `recursos-pantalla.md` mandan)
  - paso 6 quater: `encuadre.py` con o sin `--quitar`
- Si el talento pide algo en un paso concreto («aquí no pongas CTA»), se hace en ese vídeo; no cambies `estilo.json` por eso.

## 5. Al entregar: ¿lo guardo?
En el mensaje de entrega (paso 8 de `edicion-basica.md`), si el estilo de este vídeo **no** es el que ya tenía guardado, añade una línea:
> ¿Te gusta cómo ha quedado? Si quieres, guardo este estilo y tus próximos vídeos saldrán así.

Con su «sí»:
```
uv run "$SKILL/scripts/estilo.py" guardar "<carpeta del vídeo>"
```
Se guarda en `<carpeta del talento>/estilo-talento.json`, junto a `perfil-talento.md`. Si ya tenía otro, el anterior queda en `estilo-talento-anterior.json`.

No lo guardes sin preguntar, y no vuelvas a preguntarlo si ya ha dicho que no en este vídeo.
