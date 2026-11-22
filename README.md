# decodik-editor · Skill de edición de vídeo con IA de Decodik

Skill para **Claude Code** que edita tus vídeos verticales sin abrir ningún editor: corta silencios, muletillas y tomas falsas, subtitula y, según tu nivel, añade estilos, gráficos animados y música con la marca Decodik.

Forma parte del módulo **«El futuro de la edición»** de Decodik.

## Instalar o actualizar (un solo prompt)
Abre la app de escritorio de Claude, pestaña **Code**, y pega:

> Instala la skill de Decodik desde GitHub: descarga https://github.com/saren-visuals/decodik_editing/archive/refs/heads/main.zip, descomprímela y copia el contenido de la carpeta `decodik_editing-main` en `~/.claude/skills/decodik-editor` (si ya existe, sustitúyela), de forma que quede `~/.claude/skills/decodik-editor/SKILL.md`. Después dime qué versión ha quedado instalada (la pone en LEEME.md).

Después escribe `/` y comprueba que aparece **decodik-editor**. Si no aparece, abre una sesión nueva o escribe `/reload-skills`.

Para actualizar, pega el mismo prompt otra vez. Los cambios de cada versión están en [CHANGELOG.md](CHANGELOG.md).

## Requisitos
- Plan Claude **Pro** o superior y la app de escritorio (Windows o Mac), pestaña **Code**.
- Unos 3 GB libres. Con tarjeta NVIDIA todo va más rápido.

## Usarla
```
/decodik-editor edita mi última toma para mi marca personal
```
Guía completa en [LEEME.md](LEEME.md).
