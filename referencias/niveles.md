# Niveles

| | Básico | Intermedio | Avanzado |
|---|---|---|---|
| **Corte** (protocolo completo) | ✅ | ✅ | ✅ |
| **Encuadre vertical** (rotar o recortar un horizontal) | ✅ | ✅ | ✅ |
| **Subtítulos** | ✅ estilo TikTok (Minimal), quemados con ffmpeg | ✅ animados con HyperFrames, con palabra clave | ✅ |
| **Estilos** | Minimal | + Golpe, Editorial, Espacial, Premium | todos |
| **Color de cine** (LUTs Decodik) | ✅ | ✅ | ✅ |
| **Formatos** | Pantalla completa | Pantalla completa | + Pantalla dividida, Recuadro |
| **Gráficos** (tarjetas, listas, cifras, capturas) | — | ✅ | ✅ |
| **B-roll y fotos** de `03_recursos/` | — | ✅ | ✅ |
| **Zooms** suaves | — | ✅ | ✅ |
| **Música y efectos** (tuyos o libres de derechos que descargas tú) | solo voz limpia | ✅ | ✅ |
| **Palabra detrás de la cabeza** | — | — | ✅ |
| **Versiones** (gancho, formato, duración) | — | ✅ | ✅ |
| **Calidad** | 1080p | 1080p | 1080p o 4K |

## Qué instala cada nivel
`python "{SKILL}/scripts/comprobar_equipo.py" --nivel <nivel>` lo comprueba y da los comandos. Pide permiso antes de cada instalación y explica para qué sirve.

- **Básico:** ffmpeg (cortar, montar, exportar) · Python 3.10+ con `faster-whisper` y `numpy` (escuchar y transcribir). Unos 2 GB con el modelo de transcripción.
- **Intermedio:** + Node.js 22+ y HyperFrames (`npx hyperframes`) para dibujar gráficos y subtítulos animados. La música y los efectos los aporta el usuario (ver `sonido.md`).
- **Avanzado:** + PyTorch (con CUDA si hay tarjeta NVIDIA) y el modelo de recorte RobustVideoMatting (~100 MB, licencia GPL-3.0, se descarga de su página oficial). Recomendado: tarjeta NVIDIA. En Mac o sin tarjeta, funciona pero es lento: avísalo.

## Subir de nivel
Cuando un usuario domina un nivel (ha entregado 2-3 vídeos sin problemas), puedes sugerirle el siguiente en una línea al terminar. Nunca le subas de nivel sin preguntar.
