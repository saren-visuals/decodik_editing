# Flujo C · Vídeo para una marca (UGC)

Objetivo: entregar a una marca un vídeo que cumple su brief. **Aquí manda la marca**: su guía visual va por encima de los estilos Decodik. El talento no improvisa el mensaje.

## 1. Material
Crea el proyecto con `crear_proyecto.py --caso marca --nivel <nivel>` y pide que deje:
- `01_brief/`: el brief (PDF, documento o texto), el guion si lo hay y la guía de marca si la hay.
- `02_tomas/`: las tomas grabadas.
- `03_recursos/`: fotos del producto, capturas, B-roll.
- `04_marca/`: logo, tipografías y colores de la marca.

## 2. Leer el brief
Lee todo `01_brief/` y escribe `01_brief/resumen-brief.md` con:

| Campo | Lo que dice el brief |
|---|---|
| Marca y producto | |
| Objetivo del vídeo | (awareness, venta, descarga…) |
| Red y formato | (9:16, duración máxima) |
| Mensajes obligatorios | (lo que tiene que decirse sí o sí) |
| Prohibido | (palabras, comparaciones, competidores, afirmaciones de salud…) |
| Llamada a la acción | (texto exacto, código, enlace) |
| Look | (colores, tipografía, logo, música, subtítulos) |
| Entregables | (versiones, con/sin subtítulos, con/sin música, archivos) |
| Fecha de entrega | |

Si falta un dato importante (duración, CTA, entregables), **pregúntalo antes de editar**. Enseña el resumen y espera el OK.

## 3. Comprobar tomas contra el guion
Tras transcribir (protocolo de corte, pasos 1-2), compara la transcripción con el guion y los mensajes obligatorios:
- ✅ dicho · ⚠️ dicho distinto · ❌ no está.
Si falta un mensaje obligatorio o se dice algo prohibido, **avísalo antes de cortar**: puede que haya que regrabar. Elige la mejor toma de cada frase si hay varias.

## 4. Estilo
- Si la marca tiene guía: crea `04_marca/estilo-marca.json` copiando la estructura de `{SKILL}/estilos/minimal.json` (básico) o del estilo Decodik más parecido (intermedio y avanzado) y **sustituye colores, tipografías y reglas por los de la marca**. Las fuentes de la marca van en `04_marca/` y se pasan con `--fuentes`.
- Si la marca no tiene guía: usa Minimal y pregunta si quiere otro estilo Decodik.
- El logo de la marca solo aparece donde el brief lo pide. Nunca se recrea: se usa el archivo de `04_marca/`.

## 5. Pasadas
Las mismas que en `{SKILL}/flujos/marca-personal.md` (tabla de la sección 2), con estas reglas extra:
- En el plan de gráficos, cada mensaje obligatorio y el CTA tienen su momento visual.
- Los textos en pantalla salen del brief o del guion, palabra por palabra. Nada de afirmaciones que no estén en el brief.
- Música: solo la que dé la marca o música con licencia comercial. Si no hay, entrega sin música y dilo.

## 6. Entrega
Además de `control-calidad.md`, rellena `07_entrega/checklist-brief.md`:
- Cada mensaje obligatorio: ✅ con el segundo en que aparece.
- CTA exacto: ✅ / ❌.
- Nada prohibido: ✅.
- Duración, formato y entregables: ✅.

Entrega todos los archivos que pida el brief (por ejemplo, con y sin subtítulos, con y sin música) con nombres claros: `<marca>_<tema>_v1_9x16.mp4`.
