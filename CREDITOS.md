# Créditos y licencias de terceros

`decodik-editor` no incluye en el repo programas, modelos ni fuentes de terceros: los scripts los descargan de su fuente oficial la primera vez que hacen falta.

| Qué | Para qué | Licencia | De dónde se descarga |
|---|---|---|---|
| [ffmpeg](https://ffmpeg.org) | Cortar, montar, subtitular y renderizar | LGPL/GPL según la compilación | Lo instala el talento (winget, Homebrew o apt) |
| [uv](https://github.com/astral-sh/uv) | Trae Python y las librerías | MIT / Apache-2.0 | Lo instala el talento |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Transcripción con tiempos por palabra | MIT | PyPI, vía `uv run` |
| Modelo Whisper `large-v3-turbo` ([OpenAI](https://github.com/openai/whisper), convertido por [mobiuslabsgmbh](https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo)) | Transcripción | MIT | Hugging Face, en el primer vídeo |
| [Inter e Inter Display](https://github.com/rsms/inter) 4.1 | Letras de los subtítulos (`clave`, `frase`, `impacto`, `condensada`, `minimo`) y de la hoja de revisión | SIL Open Font License 1.1 | Zip oficial de la versión 4.1 en GitHub; se guardan solo los grosores que se usan, con su licencia |
| [Figtree](https://github.com/erikdkennedy/figtree) | Letras de los subtítulos (`caja`, `mixta`) | SIL Open Font License 1.1 | Repositorio oficial de Figtree, con su `OFL.txt` |
| Georgia | Estilo `serif` (provisional) | Letra del sistema (Windows y Mac); no se distribuye | No se descarga |
