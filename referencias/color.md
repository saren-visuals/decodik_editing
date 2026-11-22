# Pasada de color (look de cine)

Opcional en todos los niveles. Va **después del corte y antes de los gráficos** (los gráficos no se colorean).

## LUTs de Decodik (`{SKILL}/color/`)
| LUT | Look | Para qué |
|---|---|---|
| `decodik-cine` | Contraste suave, negros levantados, sombras hacia petróleo, luces cálidas tipo crema, saturación contenida | Intro cinematográfica, marca personal premium |
| `decodik-cine-suave` | Lo mismo, más discreto | Lecciones y vídeos largos |
| `decodik-noche` | Más contraste, sombras profundas y luces frías menta | Contenido nocturno, tecnología |

Los `.cube` sirven también en DaVinci, CapCut PC y Blackmagic Camera (para ver el look mientras grabas).

## Uso
```bash
# 1 · Prueba con un fotograma (barato: compara antes y después)
python "{SKILL}/scripts/color.py" --entrada 06_trabajo/cortado.mp4 --salida 06_trabajo/color --prueba 3.0
# 2 · Aplica a todo el vídeo
python "{SKILL}/scripts/color.py" --entrada 06_trabajo/cortado.mp4 --salida 06_trabajo/cortado_color.mp4 --lut decodik-cine
```
- Toma en **Apple Log** (iPhone): añade `--log-apple` y deja el LUT oficial «Apple Log to Rec.709» de Apple en `{SKILL}/color/AppleLogToRec709.cube`.
- Ajustes: `--intensidad 0.6` (mezcla con el original), `--grano 0.05`, `--vineta 0.3`, `--halacion 0.25` (brillo cálido en las luces). Pon `0` para quitar cualquiera.
- Enseña al usuario el antes y el después del fotograma y espera su OK antes de aplicarlo a todo el vídeo.
- Para gastar pocos tokens: mira solo 2-3 fotogramas de prueba; el resto lo hace ffmpeg.

## Límites
No hace correcciones por zonas con seguimiento (aislar la piel o una cara que se mueve). Para eso, DaVinci con el mismo LUT.
