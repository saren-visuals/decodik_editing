# Créditos y licencias de terceros

`decodik-editor` no incluye en el repo programas, modelos ni fuentes de terceros: los scripts los descargan de su fuente oficial la primera vez que hacen falta.

| Qué | Para qué | Licencia | De dónde se descarga |
|---|---|---|---|
| [ffmpeg](https://ffmpeg.org) | Cortar, montar, subtitular y renderizar | LGPL/GPL según la compilación | Lo instala el talento (winget, Homebrew o apt) |
| [uv](https://github.com/astral-sh/uv) | Trae Python y las librerías | MIT / Apache-2.0 | Lo instala el talento |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Transcripción con tiempos por palabra | MIT | PyPI, vía `uv run` |
| Modelo Whisper `large-v3-turbo` ([OpenAI](https://github.com/openai/whisper), convertido por [mobiuslabsgmbh](https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo)) | Transcripción | MIT | Hugging Face, en el primer vídeo |
| [Montserrat](https://github.com/JulietaUla/Montserrat) ExtraBold | Letra de los subtítulos | SIL Open Font License 1.1 | Repositorio oficial de Montserrat, en el primer vídeo subtitulado (se guarda junto a su `OFL.txt`) |
