# Ordenar mis recursos

Objetivo: pasar de una carpeta caótica de clips y fotos a una biblioteca donde todo se encuentra en segundos.

1. Pregunta qué carpeta ordenar y dónde quiere la biblioteca (recomienda `Decodik/_recursos/`).
2. Haz el inventario:
   ```bash
   python "{SKILL}/scripts/inventario.py" --carpeta "<carpeta>" --out "<carpeta>/_inventario"
   ```
   El script lista cada archivo con su fecha, duración, orientación y una miniatura (`_inventario/miniaturas/`).
3. **Mira las miniaturas** y clasifica cada archivo por:
   - **Tema** (lo que sale): `entrenando`, `competicion`, `lifestyle`, `producto`, `viajes`, `comida`, `equipo`…
   - **Tipo de plano**: `general`, `medio`, `detalle`, `accion`.
   - Nombre: `tema_plano_AAAA-MM_numero` (por ejemplo `entrenando_detalle_2026-11_03.mp4`).
4. Enseña la propuesta en una tabla (archivo actual → carpeta y nombre nuevo) y **espera el OK**. Nunca muevas nada sin aprobación.
5. Con el OK, **copia** (no muevas) los archivos a `_recursos/<tema>/<plano>/` con su nombre nuevo, y guarda `_recursos/indice.md` con una línea por archivo: nombre, qué se ve y duración. Ese índice es lo que usarás para buscar B-roll en futuras ediciones.
6. Ofrece borrar los originales solo si el usuario lo pide, y pide permiso explícito.
