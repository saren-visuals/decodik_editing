# Skill `decodik-editor` · Decodik

**Versión 1.5 · 24-11-2026** · `version: 1.5` · la 1.0 (22-11-2026) es la que se grabó para los alumnos; los cambios están en `CHANGELOG.md`.

Con esta skill, Claude Code edita tus vídeos verticales sin que tengas que abrir ningún editor. Corta silencios, muletillas y tomas falsas, pone subtítulos y, según tu nivel, añade estilos, gráficos animados y tu música con la marca Decodik.

## Lo que necesitas
- Claude **Pro** o superior (Claude Code no está en el plan gratuito).
- La app de escritorio de Claude, en la pestaña **Code**, en Windows o Mac.
- Unos 3 GB libres para el básico. Con tarjeta NVIDIA todo va mucho más rápido.

## 1 · Instalarla (y actualizarla)
Abre la app de Claude, pestaña **Code**, y pega este prompt. Sirve para instalarla la primera vez y para actualizarla cuando haya versión nueva:

> Instala la skill de Decodik desde GitHub: descarga https://github.com/saren-visuals/decodik_editing/archive/refs/heads/main.zip, descomprímela y copia el contenido de la carpeta `decodik_editing-main` en `~/.claude/skills/decodik-editor` (si ya existe, sustitúyela), de forma que quede `~/.claude/skills/decodik-editor/SKILL.md`. Después dime qué versión ha quedado instalada (la pone en LEEME.md).

Escribe `/` y comprueba que aparece **decodik-editor**. Si no aparece, abre una sesión nueva o escribe `/reload-skills`.

**A mano:** descarga el zip desde el botón verde **Code → Download ZIP** de esta página, descomprímelo, renombra la carpeta `decodik_editing-main` a `decodik-editor` y cópiala en `C:\Users\<tu usuario>\.claude\skills\` (Windows) o `~/.claude/skills/` (Mac). Tiene que quedar `.claude/skills/decodik-editor/SKILL.md`.

## 2 · Primera vez
Escríbele:

> /decodik-editor es mi primera vez, prepara mi equipo y mi carpeta.

Claude comprueba qué tienes, te pide permiso antes de instalar cada cosa y te crea la carpeta `Decodik`. **Abre Claude Code siempre en esa carpeta.**

## 3 · Editar
> /decodik-editor quiero editar mi última toma

Te preguntará qué quieres hacer:

| Opción | Para qué |
|---|---|
| **Solo cortar** | Quitar silencios, muletillas y tomas falsas |
| **Marca personal** | Tu contenido, con un estilo Decodik o el tuyo |
| **Vídeo para una marca** | Un UGC a partir del brief de la marca |
| **Ordenar recursos** | Ordenar tus clips y fotos |
| **Crear mi estilo** | Que edite siempre a tu manera, a partir de tus referencias o de unas preguntas |
| **Replicar un estilo** | Editar como un vídeo que te gusta: trae 1-3 referencias, te dice qué se puede copiar, lo guarda con nombre y te enseña una comparación lado a lado |

Y luego irá pasada a pasada, enseñándote una vista previa en cada una. Antes de cortar te enseña un storyboard con cada corte y su motivo, y cómo quedaría. Si algo no te gusta, díselo con tus palabras.

## Niveles
| Nivel | Qué hace |
|---|---|
| **Básico** | Cortes + subtítulos estilo TikTok + sonido limpio |
| **Intermedio** | + estilos Golpe, Editorial, Espacial, Premium y Neón lima, formatos Tierlist y explicativos, gráficos, B-roll, tu música, versiones |
| **Avanzado** | + palabra detrás de la cabeza, pantalla dividida, recuadro, 4K |

Empieza en básico. Cuando lo domines, pídele subir de nivel: instalará solo lo que falte.

## Estilos
- **Minimal** (básico): subtítulos estilo TikTok, 1-2 palabras en blanco con contorno negro, sin palabra clave.
- **Golpe**: deportivo, palabra clave gigante en amarillo, cortes secos.
- **Editorial crema**: tarjetas crema, capturas reales, sin olor a IA.
- **Espacial**: el look de Decodik, cristal oscuro y degradado menta→cian.
- **Premium**: editorial. Fondos noche y crema con grano, etiqueta en mayúsculas + palabra serif gigante que aparece cuando la dices, llamadas en caja menta, barridos suaves y efectos sincronizados.
- **Neón lima**: bloques de tres pisos con una palabra protagonista enorme en verde lima con resplandor y las demás pequeñas en blanco; cinco entradas animadas distintas y tachado rojo para negaciones («antes/ahora»).

Y si te gusta el estilo de otro vídeo, pídele que lo replique: lo guarda en tu biblioteca de estilos junto al tuyo.

## Formatos
El formato decide dónde va cada cosa; el estilo, cómo se ve. Se combinan.
- **Pantalla completa** (básico): tú a pantalla completa con subtítulos.
- **Mi historia** (básico): cuentas tu historia y tus fotos y vídeos de archivo entran encima en cada frase que nombra algo.
- **Tierlist** (intermedio): tabla de niveles de colores; cada cosa que nombras aparece en foto real y baja a su nivel cuando das el veredicto. Las fotos las busca la skill con licencia libre.
- **Explicativo con texto** (intermedio): cuando explicas algo, la pantalla se divide con una palabra protagonista arriba y tú abajo.
- **Explicativo con motion graphics** (intermedio): igual, pero arriba se explica con dibujos animados que cambian con tu voz.
- **Pantalla dividida** y **recuadro** (avanzado): tus recursos o una grabación de pantalla junto a ti.

Los montajes también se pueden exportar como borrador editable de **CapCut**.

## Color de cine
LUTs propios de Decodik (`color/`: cine, cine suave y noche) con grano, viñeta y halación. Pídeselo así: «aplícale el look de cine». Los `.cube` también sirven en DaVinci, CapCut y Blackmagic Camera.

## Qué incluye
- `SKILL.md`: las instrucciones que sigue Claude.
- `flujos/`: un archivo por cada opción.
- `referencias/`: niveles, protocolo de corte, subtítulos, gráficos, sonido, zonas seguras, control de calidad, versiones, avanzado y estilo propio.
- `estilos/`: catálogo y los 5 estilos.
- `marca/decodik.json`: la paleta y las tipografías de Decodik.
- `plantillas/hyperframes/`: referencia de diseño (`decodik.css`) y GSAP local (`gsap.min.js`, licencia estándar gratuita de GreenSock).
- `scripts/`: comprobar equipo, crear proyecto, preparar, transcribir, analizar, cortar, subtítulos, quemar subtítulos, construir la composición de gráficos, animaciones explicativas (`motions.py`), color de cine, mezclar, revisar, inventario, recorte del sujeto y composición de la base.
- `fonts/`: Figtree, Anton, Bebas Neue e Instrument Serif (licencia SIL Open Font License).
- `color/`: LUTs de Decodik.

## Licencias
- Skill, scripts, estilos y plantillas: © Decodik. Uso para alumnos de Decodik.
- Fuentes: SIL Open Font License (`fonts/LICENCIA-OFL.txt`).
- GSAP (`plantillas/hyperframes/gsap.min.js`): licencia estándar gratuita de GreenSock (gsap.com/standard-license).
- El modelo de recorte RobustVideoMatting (solo avanzado) **no viene en el paquete**: tiene licencia GPL-3.0 y Claude lo descarga de su repositorio oficial la primera vez, con tu permiso.
- **Música y efectos**: el paquete no incluye ninguno. Usa los tuyos, los de la marca o música libre de derechos que descargues tú (Pixabay Music, biblioteca de audio de YouTube).

## Estado de las pruebas
- ✅ Básico con un vídeo real (iPhone, Dolby Vision): corte desde cero de 94 s a 24,5 s sin pausas de más de 0,25 s ni palabras perdidas, retranscripción tras el corte, Minimal estilo TikTok, sonido a −14 LUFS.
- ✅ Intermedio con el mismo vídeo: Espacial con lista, cifra, tarjeta y llamada final; subtítulos animados centrados; check de HyperFrames sin errores.
- ✅ Avanzado: recorte del sujeto con tarjeta NVIDIA, palabra detrás de la cabeza, pantalla dividida y recuadro con animaciones explicativas.
- ✅ Color de cine en Windows (graduado en RGB, sin tinte rosa).
