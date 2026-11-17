# Créditos y licencias de terceros

`decodik-editor` no incluye en el repo programas, modelos ni fuentes de terceros: los scripts los descargan de su fuente oficial la primera vez que hacen falta.

| Qué | Para qué | Licencia | De dónde se descarga |
|---|---|---|---|
| [ffmpeg](https://ffmpeg.org) | Cortar, montar, subtitular y renderizar | LGPL/GPL según la compilación | Lo instala el talento (winget, Homebrew o apt) |
| [uv](https://github.com/astral-sh/uv) | Trae Python y las librerías | MIT / Apache-2.0 | Lo instala el talento |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Transcripción con tiempos por palabra | MIT | PyPI, vía `uv run` |
| Modelo Whisper `large-v3-turbo` ([OpenAI](https://github.com/openai/whisper), convertido por [mobiuslabsgmbh](https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo)) | Transcripción | MIT | Hugging Face, en el primer vídeo |
| [Inter e Inter Display](https://github.com/rsms/inter) 4.1 | Letras de los subtítulos (`impacto`, `condensada` sin Helvetica), textos grandes sin Helvetica, etiquetas (Inter Bold) y hoja de revisión | SIL Open Font License 1.1 | Zip oficial de la versión 4.1 en GitHub; se guardan solo los grosores que se usan, con su licencia |
| [Figtree](https://github.com/erikdkennedy/figtree) | Letras de los subtítulos (`clave` —estilo DECODIK—, `frase`, `caja`, `mixta`, `minimo`) | SIL Open Font License 1.1 | Repositorio oficial de Figtree, con su `OFL.txt` |
| [OpenCV](https://github.com/opencv/opencv) 4 (`opencv-python-headless`) | Detectar la cara para que los recursos no la tapen | Apache-2.0 | PyPI, vía `uv run` |
| [NumPy](https://numpy.org) | Preparar las imágenes de los recursos (color HDR, esquinas) | BSD-3-Clause | PyPI, vía `uv run` |
| Helvetica Now Display ExtraBlack (Monotype) | Marca DECODIK: ganchos, cifras, CTA y estilo `condensada` | Comercial, todos los derechos reservados (Monotype); **no se distribuye** | Nunca se descarga: se usa solo si el equipo la tiene con licencia. Si no, Inter Display Black |
| Georgia | Estilo `serif`, solo cuando la referencia del talento es serif | Letra del sistema (Windows y Mac); no se distribuye | No se descarga |
