# DECODIK · Edición con IA

Skills y recursos del **Módulo de Edición con IA** de DECODIK, para talentos apasionados del deporte que crean contenido y colaboran con marcas.

## Qué hay aquí

| Skill | Para qué sirve | Cómo se pide |
|---|---|---|
| `decodik-perfil` | Crea tu perfil (quién eres, cómo hablas, tu audiencia, tus marcas) para que todo suene a ti | «crea mi perfil» |
| `decodik-edicion` | De la idea al vídeo: plantilla, guion, 3 ganchos, qué grabar, edición paso a paso en CapCut y revisión con el Sello DECODIK | «quiero hacer un vídeo sobre…» |
| `decodik-marca` | Colaboraciones: ordena el brief, revisa que lo cumples y prepara la entrega a la marca | «tengo un brief de…» |

**Plantillas de vídeo (v1):** Reacción · Ranking por niveles · Explicación con pizarra · Lista rápida · Debate · Historia o curiosidad · Antes y ahora · Vlog de experiencia · Integración de marca.

## Instalación

### Nivel 1 · App de Claude (sin terminal)
1. Descarga los archivos `.zip` de cada skill que te da DECODIK.
2. En Claude: **Configuración → Capacidades → Skills → Subir skill** y sube cada `.zip`.
3. Crea un **Proyecto** llamado «Mi contenido DECODIK».
4. Dentro del proyecto escribe: **«crea mi perfil»** y sube el `perfil-talento.md` resultante al conocimiento del proyecto.
5. Listo: «quiero hacer un vídeo sobre…».

### Nivel 3 · Claude Code
```
/plugin marketplace add saren-visuals/decodik_editing
/plugin install decodik@decodik
```

## Estructura
```
.claude-plugin/        manifiestos del plugin
skills/
  decodik-perfil/      entrevista + plantilla de perfil
  decodik-edicion/     flujo completo + referencias (contexto, catálogo, calidad, CapCut)
  decodik-marca/       brief + revisión + entrega
modulo/                mapa del módulo y guiones de las lecciones (Loom)
```

## Propiedad intelectual
Todo el contenido de este repositorio es original de DECODIK. Material de formaciones de terceros se usa solo como referencia de investigación y **nunca** se copia aquí (`referencias/` está en `.gitignore`).

© DECODIK · Todos los derechos reservados. Uso exclusivo de talentos DECODIK.
