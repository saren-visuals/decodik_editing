# Carpetas · un vídeo, una carpeta

Cada vídeo vive en su propia carpeta, dentro de la carpeta del talento. Así nunca se mezclan clips de vídeos distintos y todo queda en orden de fecha.

```
<carpeta del talento>/
  perfil-talento.md                  uno solo, sirve para todos los vídeos
  2026-11-15 Eileen Gu/
    01_brief/  02_brutos/  03_recursos/  04_marca/  05_musica/
    06_entrega/
      video-v1.mp4   video-v2.mp4    versiones de ESE vídeo
  2026-11-20 Zancada Brisa 3/
    ...
```

- **Carpeta del talento** = la carpeta de trabajo (la que tiene conectada o desde la que te habla). Si no tienes carpeta de trabajo, pregúntale: «¿En qué carpeta guardas tus vídeos?».
- **Carpeta del vídeo** = `AAAA-MM-DD Nombre`. La fecha la pone el script; el talento solo elige el nombre. Si repite nombre el mismo día, sale `… (2)`.
- Todos los pasos de edición (y de UGC) trabajan **dentro de la carpeta del vídeo**: sus `01_brief/`, `02_brutos/` y `06_entrega/`.
- `$SKILL` = la carpeta de esta skill. Los comandos están en `$SKILL/scripts/videos.py`.

## Al empezar (después de elegir el modo)

1. Mira qué vídeos tiene:
   ```
   uv run "$SKILL/scripts/videos.py" lista "<carpeta del talento>"
   ```
2. **Si no tiene ninguno**, o su mensaje deja claro que es uno nuevo, ve directo al paso 3.
   **Si tiene alguno**, pregunta una sola cosa, con los 3 más recientes como opciones:
   > ¿Es un vídeo nuevo o seguimos con uno de estos?
   > 1. 2026-11-15 Eileen Gu (entregado: video-v1.mp4)
   > 2. …
   > O dime «nuevo».
3. **Vídeo nuevo:** «¿Cómo quieres llamar a este vídeo?» (un nombre corto: «Eileen Gu», «Rutina de pierna»). Luego:
   ```
   uv run "$SKILL/scripts/videos.py" nuevo "<carpeta del talento>" "<nombre>"
   ```
   La última línea es la ruta de la carpeta nueva. Dile:
   > Te he creado la carpeta «2026-11-15 Eileen Gu». Deja tus clips en `2026-11-15 Eileen Gu/02_brutos/`, tal cual salen del móvil, y dime «listo».
4. **Vídeo anterior:** trabaja en su carpeta. Si ya tiene vídeo entregado y pide cambios, el render saca la versión siguiente (`video-v2.mp4`) sin tocar la anterior.

## Clips sueltos

Si hay vídeos fuera de una carpeta de vídeo (sueltos en la carpeta del talento, o un `02_brutos/` directamente en ella), **no los mezcles ni los muevas por tu cuenta**. Pregunta: «He visto X clips sueltos. ¿Creo un vídeo nuevo con ellos?». Si dice que sí, crea la carpeta con `videos.py nuevo` y muévelos a su `02_brutos/` (moverlos, no copiarlos: así no ocupan el doble). Antes de mover nada, dile qué vas a mover y adónde.
