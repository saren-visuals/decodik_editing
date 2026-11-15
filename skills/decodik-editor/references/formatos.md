# Formatos · una skill por formato

Cada formato de edición vive en su propia skill, junto a esta: `skills/decodik-formato-<nombre>/`, con un `SKILL.md` (qué es, qué grabar, receta de edición, reglas) y un `formato.json` (valores para los scripts). Se crean copiando `docs/plantilla-formato/`.

## Qué formatos hay

Busca las carpetas `decodik-formato-*` al lado de esta skill (`$SKILL/../decodik-formato-*/`). Hoy:

| Formato | Skill | Para |
|---|---|---|
| Hablando a cámara | `decodik-formato-hablando-a-camara` | Una idea, historia u opinión contada a cámara (el más usado) |

## Cuándo elegirlo (en la edición básica)

Después de transcribir (paso 4 de `edicion-basica.md`):

1. Si el talento ya dijo el formato, úsalo.
2. Si no, lee la transcripción y propón **el formato que encaja** en una línea («Es un vídeo hablando a cámara: lo edito con ese formato»). Si solo hay uno instalado que encaje, no preguntes: díselo y sigue.
3. Abre el `SKILL.md` de ese formato y su `formato.json`:
   - **Requisitos:** compruébalos antes de seguir (p. ej. recursos en `03_recursos/`). Si falta algo, pídeselo como diga el formato.
   - **Receta:** úsala en los pasos 6 a 6 quater (estilo de subtítulos, textos, recursos, encuadre).
   - **Reglas propias:** se suman a las de `decodik-editor`.
4. Si ningún formato encaja, edita con los valores por defecto (estilo `clave`, gancho y CTA, recursos si hay) y dile que ese formato aún no existe en DECODIK.

## Cómo usa los scripts el `formato.json`

| Campo | Qué haces |
|---|---|
| `subtitulos.estilo` | `subtitulos.py --estilo <estilo>` |
| `textos.gancho/cifras/cta` | Qué pones en `textos.json` |
| `recursos.requisito`, `minimo` | Si `03_recursos/` tiene menos, pídelos antes de editar (`minimo`: edita igual si no tiene; `obligatorio`: espera) |
| `recursos.cada_s`, `modos`, `partida_minimo_s` | Cómo repartes los recursos en `recursos.json` |
| `encuadre.alterno`, `zoom` | `encuadre.py --zoom <zoom>`, o `--quitar` si es `false` |
| `musica` | Si va música de `05_musica/` (pendiente en el motor) |
