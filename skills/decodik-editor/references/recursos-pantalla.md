# Recursos en pantalla · B-roll y tarjetas

Las fotos, capturas y clips del talento (en `03_recursos/`) aparecen **cuando los nombra**: es lo que más ritmo da a un vídeo hablado a cámara (la mitad de los reels de referencia lo hacen; ver `docs/investigacion-estilos-marca-personal.md`).

**Solo material del talento o con permiso** (`CLAUDE.md`): la skill no busca, descarga ni genera imágenes de terceros (jugadas, retransmisiones, fotos de famosos, logos). Si el talento quiere un recurso que no tiene, díselo y propón grabarlo o hacer una captura propia.

## Dos maneras

| Modo | Cómo se ve | Cuándo |
|---|---|---|
| `completo` | El recurso ocupa toda la pantalla 1-3 s mientras sigue la voz (corte a B-roll) | Lugares, entrenos, partidos, el producto en uso. **Si la cara del talento está baja en el plano**, mejor este que una tarjeta |
| `tarjeta` | Tarjeta con esquinas redondeadas sobre el pecho, entre la cara y los subtítulos; entra subiendo con un fundido | Fotos, capturas de pantalla, datos, portadas, el producto |

## Qué escribes tú (Claude)

1. Mira qué hay en `03_recursos/` y lee `06_entrega/trabajo/transcripcion.md`.
2. Empareja cada recurso con **la palabra en la que el talento lo nombra** o habla de ello. Uno cada 4-8 s como mucho; no hace falta usarlos todos.
3. Escribe `06_entrega/trabajo/recursos.json` y enséñaselo al talento en una lista corta («En "Stanford": foto de la residencia, en tarjeta…»):

```json
{"recursos": [
  {"archivo": "podio.jpg",   "en": "oro#1",      "modo": "tarjeta",  "dura": 2.0},
  {"archivo": "entreno.mov", "en": "periodista", "modo": "completo", "dura": 2.0}
]}
```

- `en`: la palabra de la transcripción del vídeo cortado (admite «palabra#2» y varias palabras).
- `dura`: segundos (por defecto 2). Que no se solapen dos recursos ni una tarjeta con una cifra grande (`textos.json`): el script avisa.
- Los clips se usan **sin su sonido**: la voz del talento sigue.

## Comando

```
uv run "$SKILL/scripts/recursos.py" "<carpeta del vídeo>"
```

Prepara las imágenes (tamaño, esquinas, color) en `06_entrega/trabajo/recursos/` y escribe `recursos-plan.json`; `render.py` los pone encima del vídeo, debajo de subtítulos y textos.

## Color

- Fotos y capturas (siempre «normales», SDR) se convierten para que se vean igual dentro de un vídeo HDR: blanco al nivel de referencia, colores en BT.2020 + HLG (como los textos).
- Los clips tienen que estar grabados igual que el vídeo (HDR con HDR del mismo tipo, o normal con normal). Si no, el script lo dice y propone usar una foto o captura de ese momento.
