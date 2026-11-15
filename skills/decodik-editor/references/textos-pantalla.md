# Textos en pantalla · gancho, cifras y CTA

Lo que convierte el vídeo subtitulado en un reel: un **gancho** escrito desde el fotograma 0, **cifras grandes** cuando se dice un número que importa, y un **CTA** al final. Sale de los reels de referencia (`docs/investigacion-estilos-marca-personal.md`).

## Qué escribes tú (Claude)

Después de cortar, lee `06_entrega/trabajo/transcripcion.md` y propón `06_entrega/trabajo/textos.json`:

```json
{
 "gancho": {"texto": "No eligió una sola etiqueta", "clave": "una sola"},
 "cifras": [{"texto": "62", "detalle": "créditos", "en": "62"}],
 "cta":    {"texto": "Guárdalo para cuando te pregunten qué eres", "clave": "qué eres"}
}
```

**Enséñaselo al talento en 3 líneas antes de renderizar** («Gancho: … · Cifras: … · Final: …») y espera su «ok» o sus cambios. Son textos que hablan por él.

### Gancho
- 3-7 palabras, en mayúsculas automáticas, arriba, desde el fotograma 0 hasta que acaba su primera frase (2-4 s).
- Resume la promesa o el giro del vídeo, **con sus palabras**; no lo conviertas en anuncio. Si la primera frase ya engancha, el gancho puede ser una versión más corta de ella.
- `clave`: el trozo que va en color (la promesa, la cifra, el contraste).
- `hasta`: segundos, solo si quieres fijar a mano cuánto dura.

### Cifras
- Solo números que **cuentan la historia** (resultados, contrastes, récords): 1-3 por vídeo como mucho. Nunca una cifra que no esté en lo que dice el talento o en el brief.
- `texto`: lo que se ve en grande («62», «85 %», «1,5M»). `detalle`: 1-3 palabras debajo («créditos»).
- `en`: la palabra de la transcripción en la que aparece (admite «palabra#2» y varias palabras). Si el script dice que no la encuentra, copia la palabra tal cual sale en la transcripción.
- La cifra sale grande debajo de la cara, entra con un golpe de escala y dura ~1,3 s (`dura` para cambiarlo). **Mientras se ve, el subtítulo se aparta.**

### CTA
- Una sola acción: guardar, comentar una palabra, seguir, o la del brief si es de marca. Sale arriba los últimos 2,5 s (`segundos` para cambiarlo).
- Mejor si retoma la idea del vídeo («Guárdalo para cuando te pregunten qué eres») que un «sígueme» genérico.
- `clave`: lo que va en color (la palabra a comentar, la acción).

## Comando

```
uv run "$SKILL/scripts/textos.py" "<carpeta del vídeo>" [--color-clave HEX]
```

Escribe `textos.ass` y `textos-huecos.json`; `render.py` los pinta solo encima de los subtítulos. Si no hay `textos.json`, el vídeo sale sin estos textos. El color de lo resaltado es amarillo por defecto (el mismo que la palabra clave de los subtítulos); con color de marca, usa `--color-clave`.
