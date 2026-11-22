# Flujo A · Solo cortar

Objetivo: quitar silencios, muletillas y tomas falsas, sin añadir nada más. Siempre es nivel básico.

## 1. Proyecto
Pregunta (AskUserQuestion, máximo 2 preguntas):
1. **¿Qué vídeo?** Ofrece los más recientes de `Decodik/_tomas-sueltas/` o de la última carpeta usada, o que arrastre o pegue la ruta.
2. **¿Cuánto cortar?** Natural (recomendado: deja respiraciones, pausas de hasta 0,4 s) · Ajustado (pausas de hasta 0,25 s, ritmo de reel rápido). **No lo preguntes** si `Decodik/_mi-estilo/reglas.md` ya lo dice: aplícalo y menciónalo en una línea. Si no lo pregunta nadie, usa natural y dilo al enseñar la propuesta.

Crea el proyecto:
```bash
python "{SKILL}/scripts/crear_proyecto.py" --raiz "<Decodik>" --nombre "<tema corto>" --caso cortar --nivel basico --toma "<ruta del vídeo>"
```
Copia la toma a `02_tomas/` (el script lo hace) y trabaja siempre en `06_trabajo/`.

## 2. Preparar
```bash
python "{SKILL}/scripts/preparar.py" --src "<proyecto>/02_tomas/<toma>" --trabajo "<proyecto>/06_trabajo"
```
Si el script se para porque el vídeo es horizontal, mira `06_trabajo/fotograma.jpg`:
- La persona sale tumbada → repite con `--rotar 90` (o `270`).
- La persona sale derecha → repite con `--recorte 0.5` (0 = izquierda, 1 = derecha; ajusta para que quede centrada y compruébalo con otro fotograma).
- Si el usuario quiere conservar el horizontal, usa `--mantener`.

## 3. Cortar
Sigue `{SKILL}/referencias/protocolo-corte.md` entero. Resumen:
1. Transcribir → 2. analizar → 3. enseñar transcripción y propuesta de cortes → 4. el usuario corrige → 5. `cortar.py` → 6. comprobar que no se pierde ninguna palabra.

## 4. Entrega
```bash
python "{SKILL}/scripts/subtitulos.py" --palabras "06_trabajo/palabras.json" --solo-srt --out "07_entrega/<tema>.srt"
python "{SKILL}/scripts/mezclar.py" --video "06_trabajo/cortado.mp4" --voz "06_trabajo/voz_cortada.wav" --out "07_entrega/<tema> - cortado.mp4"
python "{SKILL}/scripts/revisar.py" --video "07_entrega/<tema> - cortado.mp4"
```
Entrega `07_entrega/<tema> - cortado.mp4` y el `.srt` (subtítulos para subir a la red o importar en CapCut). Di cuánto duraba y cuánto dura ahora.
