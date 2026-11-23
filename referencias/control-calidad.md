# Control de calidad (antes de entregar)

## Técnico (automático)
```bash
python "{SKILL}/scripts/revisar.py" --video 07_entrega/<tema>.mp4 --red <instagram|tiktok|shorts|todas>
```
Comprueba resolución, 30 fps, duración, que hay audio, volumen (−14 LUFS ± 1, pico < −1 dB) y genera `07_entrega/hoja-de-contacto.jpg` (12 fotogramas con la zona segura dibujada).

## Visual (lo haces tú mirando la hoja de contacto y los fotogramas clave)
- [ ] El gancho engancha en los 2 primeros segundos (algo se mueve o golpea).
- [ ] Nada tapa la cara ni la barbilla, también con el zoom máximo.
- [ ] Todo lo importante está dentro de la zona segura.
- [ ] Una sola idea en pantalla cada vez; ningún subtítulo duplica un gráfico.
- [ ] Ningún texto cortado por los bordes.
- [ ] **Motion graphics:** ningún icono, texto ni gráfico se pisa con otro; todo entra en pantalla y en la zona segura; ningún texto por debajo de 26 px (si no cabe, se acorta). Ver el punto 3 de `formato-explicativo-motion.md`.
- [ ] Subtítulos sin faltas de ortografía (relee `subtitulos.srt` entero).
- [ ] Logos y capturas reales; colores y fuentes del estilo elegido.
- [ ] Hay una llamada a la acción clara (si el vídeo la necesita).
- [ ] En vídeos de marca: `checklist-brief.md` completo.

Si algo falla, arréglalo antes de entregar. Di en una línea qué comprobaste.

## Lo que hace el usuario
Pídele que lo vea dos veces en el móvil: **con sonido y sin sonido**.
