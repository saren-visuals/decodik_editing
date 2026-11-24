# Flujo B · Vídeo para mi marca personal

Objetivo: un vídeo con el estilo del talento o un estilo del catálogo Decodik, editado por pasadas.

## 1. Entrevista
Usa AskUserQuestion en **dos tandas de como máximo 4 preguntas**, con tu recomendación primero. No preguntes lo que ya sabes (mira `_mi-estilo/`, `02_tomas/` y el último `proyecto.json`).

**Tanda 1**
1. **¿Qué toma?** Las más recientes o la ruta que dé.
2. **Nivel:** el guardado en el último `proyecto.json`; si no hay, recomienda Básico la primera vez. Ver `{SKILL}/referencias/niveles.md`.
3. **Estilo:** si existe `_mi-estilo/reglas.md` con estilo propio, ofrécelo primero. Después, los estilos guardados en `_estilos/<nombre>/estilo.json` (replicados de una referencia, ver `{SKILL}/referencias/replicar-estilo.md`), con su nombre. Si no hay ninguno, muestra los estilos de `{SKILL}/estilos/catalogo.json` permitidos para su nivel, con su `queSeVe` en una línea.
4. **Revisión:** guiada (recomendado: vista previa tras cada pasada) · rápida (solo apruebas transcripción, palabras clave y plan de gráficos).

**Tanda 2** (solo intermedio y avanzado)
1. **Formato:** los de `catalogo.json` permitidos para su nivel. Recomienda Pantalla completa. Si el vídeo **explica** algo (producto, dato, dos opciones), ofrece **Explicativo con texto · pantalla dividida** (`{SKILL}/referencias/formato-explicativo-texto.md`) o **Explicativo con motion graphics · pantalla dividida** (`{SKILL}/referencias/formato-explicativo-motion.md`), con storyboard visual antes de construir. Si **clasifica cosas por niveles** (de más a menos, de peor a mejor), ofrece **Tierlist** (`{SKILL}/referencias/formato-tierlist.md`): la skill busca las fotos. Si cuenta **su historia** y tiene fotos y vídeos de archivo, ofrece **Mi historia · B-roll encima con subtítulos** (`{SKILL}/referencias/formato-mi-historia.md`).
2. **Cantidad de gráficos:** pocos (2-3 tarjetas) · equilibrado (recomendado, lo que diga el estilo) · muchos.
3. **Música:** la mía (`05_musica/`) · sin música. Si no tiene, explica que puede usar la biblioteca de audio de Instagram o TikTok al publicar.
4. **Red:** Instagram · TikTok · YouTube Shorts · todas (cambia la zona segura y la duración).
En avanzado, añade: **¿palabra detrás de la cabeza?** (sí avisa de que tarda más) y **calidad** 1080p (recomendado) o 4K (solo con tarjeta NVIDIA).

Crea el proyecto con `crear_proyecto.py --caso marca-personal --nivel <nivel> --toma <ruta>` y guarda todas las respuestas en `proyecto.json`.

## 2. Pasadas

| Pasada | Básico | Intermedio | Avanzado | Cómo |
|---|---|---|---|---|
| 0 · Preparar | ✅ | ✅ | ✅ | `preparar.py` (ver flujo A, paso 2). En avanzado y 4K: `--res 4k` |
| 1 · Corte | ✅ | ✅ | ✅ | `{SKILL}/referencias/protocolo-corte.md` |
| 1b · Color de cine | si lo pide | si lo pide | si lo pide | `{SKILL}/referencias/color.md` |
| 2 · Recorte del sujeto | — | — | si lo pidió | `{SKILL}/referencias/avanzado.md` |
| 3 · Subtítulos | ✅ | ✅ | ✅ | `{SKILL}/referencias/subtitulos.md` |
| 4 · Gráficos y B-roll | — | ✅ | ✅ | `{SKILL}/referencias/graficos.md` |
| 5 · Sonido | ✅ voz limpia | ✅ + música y efectos | ✅ | `{SKILL}/referencias/sonido.md` |
| 6 · Control de calidad | ✅ | ✅ | ✅ | `{SKILL}/referencias/control-calidad.md` |
| 7 · Versiones | — | si lo pide | si lo pide | `{SKILL}/referencias/versiones.md` |

En revisión guiada, al acabar cada pasada enseña la vista previa y espera «siguiente». En revisión rápida, para solo en: transcripción y cortes, palabras clave y plan de gráficos.

## 3. Estilo
- Toda decisión visual sale del archivo de estilo elegido (`{SKILL}/estilos/<id>.json`) o de `_mi-estilo/reglas.md`, y los colores de `{SKILL}/marca/decodik.json`.
- Si el talento tiene logo, tipografías o colores propios en `_mi-estilo/`, **mandan sobre los de Decodik**, pero se mantienen las reglas de oficio (cara libre, zona segura, una idea a la vez).
- Si quiere crear su estilo propio a partir de vídeos que le gustan, sigue `{SKILL}/referencias/mi-estilo.md`.

## 4. Entrega
`07_entrega/<tema>.mp4`, `07_entrega/<tema>.srt` y `07_entrega/portada.png` (un fotograma con la palabra clave del gancho en grande, en el estilo elegido).
