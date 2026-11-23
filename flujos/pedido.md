# Flujo P · Armar un pedido de la landing «Pide tu edición»

Para el editor (no para el talento). Se usa con «arma el pedido DK-0007», «monta el pedido 7» o «prepara el pedido de …».
Lee la fila del pedido en el Google Sheet de la landing, trae los brutos y el archivo, crea el proyecto, pasa el
pipeline del formato pedido y termina con un **borrador en CapCut**. Escribe el estado en la fila.

`{SKILL}/scripts/pedido.py` hace la parte mecánica; Claude lee y escribe el Sheet con el conector de Google Sheets
y pone el criterio (corte, B-roll por frase, palabras clave). **El storyboard se enseña antes de construir.**

## 0. Configuración (una vez)
`<Decodik>/_mi-estilo/pedidos.json` (fuera de la skill, es del editor):
```json
{"sheet_id": "<id del Sheet>", "hoja": "Pedidos",
 "plantilla_capcut": "<carpeta de un borrador de CapCut que abre bien>", "plantilla_audio": null}
```
Si no existe, pregunta el Sheet (búscalo con el conector de Drive) y el borrador de CapCut que hace de plantilla.
`<Decodik>` es la carpeta que tiene `proyectos/`.

## 1. Leer el pedido
1. Con el conector de Google Sheets: `get_values` de `Pedidos!A1:Z` en `sheet_id`. Guarda la respuesta tal cual en
   `<Decodik>/_mi-estilo/.pedidos/tabla.json` (no en la skill).
2. `python "{SKILL}/scripts/pedido.py" leer --codigo DK-0007 --tabla <tabla.json> --out <…>/DK-0007.json`
   → fila, flujo, estilo, enlaces y columnas que faltan en la hoja. La columna «Clave» nunca se copia.
3. Resume el pedido en 3-4 líneas (talento, formato, estilo, material) y sigue sin preguntar, salvo que falte
   algo imprescindible.

| `flujo` | Sale de «Estilo» | Qué se hace |
|---|---|---|
| `mi-historia` | «… + Mi historia · B-roll encima con subtítulos» | Todo este documento, hasta CapCut |
| `explicativo-texto` / `explicativo-motion` | «… + Explicativo con …» | Proyecto y material; después su referencia (`formato-explicativo-*.md`). Aún no exporta a CapCut |
| `solo-cortar` | Tipo «Solo corte limpio» | Proyecto y material; después `flujos/solo-cortar.md` |
| `manual` | Sin formato de edición | Proyecto y material; pregunta cómo seguir |

Si el estilo no lo dice pero el pedido es claramente otro, `--flujo` lo fuerza.

## 2. Estado «en edición»
`python "{SKILL}/scripts/pedido.py" estado --pedido <DK-0007.json> --fase en-edicion --proyecto <ruta>`
imprime las celdas: escríbelas una a una con `update_values` (las cabeceras que falten, «Estado» = «En edición» —lo ve
el deportista—, «Edición (interno)» y «Proyecto en el ordenador»). Hazlo después del paso 3, cuando ya hay ruta.
Solo se escriben esas columnas: nunca la nota, los enlaces de versión o entrega ni nada que vea el deportista
además del «Estado».

## 3. Proyecto y material
```bash
python "{SKILL}/scripts/pedido.py" preparar --pedido <DK-0007.json> --raiz "<Decodik>" [--tema "<2-3 palabras>"]
```
- Crea `proyectos/<fecha>_<talento>-<tema>/` (o reutiliza el de ese pedido: se puede relanzar).
- Descarga la carpeta del «Enlace de Drive» y el enlace de «Archivo de fotos y vídeos» si es de Drive. Tienen que
  estar compartidos con «Cualquier persona con el enlace». Vídeos sueltos → `02_tomas/`; subcarpeta «Archivo»
  (o «recursos», «fotos»…) y el enlace de archivo → `03_recursos/videos|fotos|capturas`; documentos → `01_brief/`.
  Queda el registro en `01_brief/material.json` y el pedido en `01_brief/pedido.md`.
- Si Drive no deja (enlace privado, WeTransfer, Google Fotos), pide al editor que lo descargue y relanza con
  `--material <carpeta o .zip>` (y `--archivo-local <carpeta>` para el archivo). Los originales no se tocan.
- Lee los `avisos`: sin toma, varias tomas (pregunta cuál), «Mi historia» sin archivo, fotos HEIC (pásalas a JPG).
- Solo se descarga al ordenador: nada se sube a ningún sitio.

## 4. Pipeline «Mi historia» (`referencias/formato-mi-historia.md`)
Trabaja en `<proyecto>/06_trabajo`. Una pasada cada vez.
1. **Preparar y corte:** `preparar.py` y `referencias/protocolo-corte.md` (si la toma ya viene cortada, solo
   `preparar.py` y `cortar.py` con un keep de todo). Deja `cortado.mp4`, `voz_cortada.wav`.
2. **Palabras:** `transcribir.py` (faster-whisper) sobre la voz cortada → `palabras.json`. Los tiempos de
   whisper.cpp no valen para subtítulos.
3. **Recursos:** `analizar_recursos.py --proyecto <proyecto>` → `03_recursos/indice-recursos.json`. Mira 3 fotogramas
   de cada recurso para saber qué se ve.
4. **Storyboard (criterio de Claude):** escribe `storyboard-historia.json` eligiendo el B-roll de cada frase que nombra
   algo (sección 2 de la referencia), con `"in": "auto"` y `"modo": "auto"`. Después
   `storyboard_historia.py --trabajo 06_trabajo` (y `--ajustar` si avisa de cortes dentro de palabras).
   **Enséñaselo al editor con `servir.py --carpeta 06_trabajo --abrir storyboard-historia.html` y espera el OK.** Con avisos no se enseña: se arregla.
5. **Subtítulos (criterio de Claude):** `frases.txt` con una palabra clave por frase y `subtitulos.py` con el estilo
   del pedido o el del editor (`_mi-estilo/`).
6. **Montaje de referencia:** `construir_historia.py` (sirve para revisar y para la hoja de primer/último fotograma).
7. **CapCut**, con CapCut cerrado del todo:
   `python "{SKILL}/scripts/pedido.py" capcut --proyecto <proyecto> --raiz "<Decodik>"`
   → llama a `exportar_capcut.py` con la plantilla de la configuración y el nombre «DK-0007 <talento>-<tema>», y comprueba
   que el borrador queda registrado. Estructura por defecto: la toma entera en la pista principal y los recursos
   como superposiciones (horizontales y HDR como copias preparadas en `03_recursos/capcut/`).

## 5. Estado «borrador en CapCut»
`pedido.py estado --pedido <DK-0007.json> --fase borrador-capcut --proyecto <proyecto>` y escribe las celdas.
«Estado» no cambia (sigue «En edición» para el deportista hasta que el editor suba la versión).
Si algo se rompe y no se puede seguir: `--fase revisar --nota "<qué pasa>"`.

## 6. Al terminar
Di en tres líneas: carpeta del proyecto, nombre del borrador en CapCut y qué queda por retocar a mano (zooms de
fotos, color de clips HDR). Pide al editor que abra CapCut y compruebe que el borrador abre.
