# Motor de edición

Lo que necesita el equipo del talento para que `decodik-editor` edite vídeo, y cómo comprobarlo.

**Stack:** ffmpeg (corte, montaje, subtítulos y render) + whisper (transcripción con tiempos por palabra, con faster-whisper). Sin Remotion.

## Qué hay que instalar

| Programa | Para qué | Windows | Mac | Linux |
|---|---|---|---|---|
| **ffmpeg** (con ffprobe) | Cortar, montar, subtitular y renderizar | `winget install Gyan.FFmpeg` | `brew install ffmpeg` | `sudo apt install ffmpeg` |
| **uv** | Trae Python y las librerías de transcripción. No hace falta instalar Python aparte | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | igual que Mac |

En Windows, después de instalar algo hay que **cerrar y volver a abrir** Claude (o la terminal) para que lo encuentre.

No hace falta ninguna clave de API. Todo funciona en el equipo del talento, sin coste.

## Comprobar el equipo

Antes del primer vídeo, o si algo falla:

```
uv run scripts/revisar_equipo.py --whisper --prueba 06_entrega
```

- Responde con ✓ y ✗, y debajo de cada ✗ el comando que lo arregla.
- `--whisper` prepara la transcripción. La primera vez descarga Python 3.12 y faster-whisper (unos minutos con internet).
- `--prueba 06_entrega` renderiza `prueba-motor.mp4`: 5 s en vertical 1080×1920 con audio. Si sale, el motor funciona.
- Termina con «Todo listo para editar.» (código 0) o «Falta algo…» (código 1).

**Cómo se lo cuentas al talento:** no le enseñes la salida entera. Dile en una línea si está todo listo; si falta algo, dale solo el comando del ✗, explica que lo pegue en la terminal y espera a que te diga «hecho».

## Lo que tarda

- **La primera vez:** descarga las librerías (aquí) y, en el primer vídeo, el modelo de voz (cientos de MB). Avisa al talento antes para que no piense que se ha colgado.
- **Después:** no descarga nada.
- Sin tarjeta gráfica NVIDIA se transcribe con el procesador: más lento en vídeos largos, pero funciona igual.

## Licencias

- ffmpeg: LGPL/GPL según la compilación.
- faster-whisper: MIT. Modelos Whisper de OpenAI: MIT.
- uv: MIT / Apache-2.0.

Se instalan desde sus fuentes oficiales; el repo no incluye ninguno.
