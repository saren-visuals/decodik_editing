# Formato · Mi historia · B-roll encima con subtítulos

La persona cuenta su historia a cámara (de dónde viene, qué le enseñó cada etapa, dónde está hoy) y, en cada frase que nombra algo que se puede **enseñar**, entra su material de archivo **encima de ella** a pantalla completa: fotos y vídeos suyos. La voz sigue siempre. Subtítulos simples durante todo el vídeo.

Nivel mínimo: **básico** (todo es ffmpeg). Se hace sobre el corte (`protocolo-corte.md`) o sobre un vídeo que el usuario ya trae cortado.

## 1. Material
- `02_tomas/`: la toma (o el vídeo ya cortado → `06_trabajo/cortado.mp4`).
- `03_recursos/videos`, `fotos`, `capturas`: el archivo de la persona, **solo suyo o con permiso**. Cataloga cada recurso con 3 fotogramas antes de escribir el storyboard: qué se ve, si es vertical u horizontal, si es HDR.

## 2. Qué va encima y cuándo
- **B-roll** en las frases con algo concreto: un deporte, un lugar, una persona, un logro, una etapa («la gimnasia», «bombera», «ser mamá», «a nivel laboral»). Entra en la palabra que lo nombra.
- **A cámara** en lo emocional y en las reflexiones (miedo, aprendizaje, opinión) y en el CTA: ahí tiene que verse la cara.
- **Empieza a cámara:** la primera frase siempre se ve la cara (quien mira tiene que saber de quién es la historia). Después, si el gancho resume la historia en 2-3 etapas → un B-roll por etapa, cortes rápidos.
- **Enumeraciones** («competiciones, entrenamientos, preparaciones»; «deportivo, laboral, familiar») → un B-roll por palabra.
- Planos de B-roll de **0,8 s como mínimo**; lo normal, 1-3 s. Entre un 35 y un 55 % del vídeo con B-roll.
- Orden de vida: fotos de niña o de joven para el pasado; vídeos actuales para el presente.

## 3. Cómo se coloca cada recurso
| Recurso | Cómo sale |
|---|---|
| Vídeo vertical | A pantalla completa (recorte 9:16 centrado) |
| Vídeo horizontal o captura | En **recuadro** a lo ancho en la parte de arriba (y = 22 %), sobre una copia suya desenfocada y oscurecida. Así el subtítulo queda debajo, sobre el fondo, sin tapar el clip |
| Foto | A pantalla completa con un **zoom lento** (1,00 → 1,08) |
| Clip HDR del iPhone | Se pasa a SDR (si no, sale lavado) |
Cortes secos. Si un clip se queda corto, se congela su último fotograma (nunca negro), pero el storyboard ya avisa antes.

## 4. Subtítulos (simples)
- Fuente que pida el usuario (por defecto la del estilo). **En el `.ass` va el nombre de familia interno de la fuente**, no el del archivo ni el que enseña Windows: p. ej. «HelveticaNowDisplay ExtraBold» (sin espacio). Si no coincide, libass pone otra fuente sin avisar: compruébalo siempre en un recorte del subtítulo. Pasa la carpeta de la fuente con `quemar_subtitulos.py --fuentes`.
- Blancos, 1-3 palabras, en minúscula, a la altura del pecho (y ≈ 1150), centrados. Una palabra clave por frase en el color de acento **del mismo tamaño** (simple). Sombra suave y contorno fino (1-2 px) para que se lea sobre paredes claras; sin caja.
- Iguales sobre la persona y sobre el B-roll.

## 4b. Tiempos de las palabras (subtítulos en tiempo y cortes entre palabras)
- Los tiempos por palabra salen de **faster-whisper** (`transcribir.py`, el modelo más grande que aguante el equipo). Los de whisper.cpp con `-ml 1` son contiguos y se desvían hasta ~0,7 s: los subtítulos se ven fuera de tiempo y los cortes caen dentro de palabras.
- Si el texto bueno viene de otra transcripción, quédate con su texto y empareja palabra a palabra para tomar los tiempos de faster-whisper.
- Tras cambiar los tiempos, `storyboard_historia.py --ajustar` mueve cada cambio de plano al borde de palabra más cercano y lo guarda.

## 5. Storyboard → montaje
1. Escribe `06_trabajo/storyboard-historia.json` (formato en la cabecera de `scripts/storyboard_historia.py`): un plano por tramo, `camara` / `broll` (con `src`, `in` y `modo`: completo · recuadro) / `foto`.
2. `python "{SKILL}/scripts/storyboard_historia.py" --trabajo 06_trabajo` → `storyboard-historia.html`. Avisa si un cambio de plano cae **dentro de una palabra** (muévelo al principio de la palabra que lo nombra), si un clip dura menos que su plano o si un B-roll dura menos de 0,8 s. Con avisos no se enseña: se arregla.
3. Enseña el storyboard (sírvelo por http) y **espera el OK**.
4. Subtítulos: `frases.txt` + `subtitulos.py` con el estilo.
5. Montaje:
```bash
python "{SKILL}/scripts/construir_historia.py" --trabajo 06_trabajo
python "{SKILL}/scripts/quemar_subtitulos.py" --video 06_trabajo/historia_base.mp4 --ass 06_trabajo/subtitulos/subtitulos.ass --out 06_trabajo/historia_subs.mp4 --fuentes <carpeta de la fuente>
python "{SKILL}/scripts/mezclar.py" --video 06_trabajo/historia_subs.mp4 --voz 06_trabajo/voz_cortada.wav --out 07_entrega/<tema>.mp4
python "{SKILL}/scripts/revisar.py" --video 07_entrega/<tema>.mp4 --red todas
```
6. Control de calidad (`control-calidad.md`) y un recorte del subtítulo para confirmar la fuente.

## 7. Recursos: el tramo más activo y estable
- `python "{SKILL}/scripts/analizar_recursos.py" --proyecto <proyecto>` antes del storyboard: orientación real, HDR, actividad cada 0,5 s, cortes internos y «huellas» del encuadre (`03_recursos/indice-recursos.json`).
- En el storyboard pon `"in": "auto"` y `"modo": "auto"` (`scripts/tramos.py`): cada plano coge el tramo **más activo** del clip (la mitad de la acción, no el arranque) que sea un **plano estable** (mismo encuadre al principio, mitad y final), sin cruzar cortes internos ni barridos de cámara y sin repetir trozo; lo horizontal (vídeo o foto) va en recuadro, nunca recortado.
- **Más B-roll seguido:** encadena recursos mientras habla (60-70 % del vídeo); la cara, al empezar, al abrir cada idea nueva, en lo emocional y en el CTA.
- Revisión obligatoria: hoja con el primer y el último fotograma de cada plano. Si en algún plano no coinciden, la imagen «se corta» en el cambio: cambia de clip o de tramo.

## 8. Llevarlo a CapCut (opcional)
`python "{SKILL}/scripts/exportar_capcut.py" --trabajo 06_trabajo --nombre "<nombre>" --plantilla <un borrador del usuario> [--plantilla-audio <borrador con un audio importado>]`, **con CapCut cerrado** (si el proyecto está abierto, sus archivos están en uso y no se puede reemplazar).
- **Estructura (por defecto «superposiciones»):** pista principal = la toma ENTERA, sin cortar y con su sonido. Superposición 1 = los B-roll y fotos verticales a pantalla completa y, para cada horizontal, una copia escalada a pantalla completa con «Desenfocar» aplicado al clip (copiado de un borrador del usuario que lo use así). Superposición 2 = el ORIGINAL de cada horizontal, a lo ancho y arriba. Pista de texto = un texto por subtítulo con el estilo del borrador plantilla y la clave en el color de acento. Los HDR del iPhone van como copia SDR en `03_recursos/capcut/`. (`--estructura secuencia`: todo seguido en la pista principal y la voz aparte.)
- **Carpeta del borrador:** se copia la carpeta ENTERA de la plantilla (CapCut necesita sus archivos internos y su línea de tiempo) y se quitan solo `draft.extra` y las copias `template*.tmp`, que guardan el montaje viejo y hacen que CapCut se niegue a abrirlo. El de plantilla no se toca; se guarda copia de `root_meta_info.json`.
- En CapCut se retocan los zooms de las fotos.
