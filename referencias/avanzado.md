# Avanzado: recorte del sujeto y formatos

## Palabra detrás de la cabeza
1. Comprueba equipo: `comprobar_equipo.py --nivel avanzado`. El modelo se descarga con `--descargar-modelo` (pide permiso: ~100 MB, licencia GPL-3.0).
2. Recorte (mate):
   ```bash
   python "{SKILL}/scripts/recortar_sujeto.py" --src 06_trabajo/cortado.mp4 --out 06_trabajo/mate.mp4
   ```
   El script avisa del tiempo estimado; si es mucho (sin tarjeta NVIDIA), ofrece seguir sin palabra detrás.
3. Prueba con un fotograma: `--prueba 5.0` genera `06_trabajo/prueba-mate.jpg` (sujeto sobre tablero) para ver si hay agujeros.
4. **Mantén el fondo real.** El mate solo sirve para poner texto o logos detrás de la cabeza.
5. Capa de detrás: pon en `plan.json` los gráficos `palabra_detras` y genera solo esa capa, con fondo transparente:
   ```bash
   python "{SKILL}/scripts/construir_composicion.py" --trabajo 06_trabajo --estilo "{SKILL}/estilos/<id>.json" --modo detras
   cd 06_trabajo/graficos && npx hyperframes render . --format mov -o ../detras.mov
   ```
6. Compón la base:
   ```bash
   python "{SKILL}/scripts/componer_base.py" --toma 06_trabajo/cortado.mp4 --mate 06_trabajo/mate.mp4 --detras 06_trabajo/detras.mov --out 06_trabajo/graficos/assets/base.mp4
   ```
7. Vuelve a generar la composición final (`--modo final`): usará esa `base.mp4` automáticamente. Renderiza como en `graficos.md`.

Reglas: 1-2 palabras detrás por vídeo (gancho y la idea más fuerte), que quepan enteras en el ancho, sin contorno blanco alrededor de la persona.

## Pantalla dividida
Pon `"formato": "pantalla-dividida"` en `plan.json` (o `--formato pantalla-dividida` en `construir_composicion.py`).
- Lienzo 1080×1920: arriba 1080×768 (40 %) para recursos y gráficos; abajo 1080×1152 (60 %) la persona, encuadrada en la cara. Línea menta de 4 px en la costura.
- **El panel de arriba explica lo que se dice, frase a frase.** Regla:
  1. Si el usuario tiene **capturas o vídeos reales** de ese momento (en `03_recursos/` o los aporta), se ponen: `{"src": "../03_recursos/captura.png", "t": 0.0, "hasta": 3.3}`.
  2. Si no, **motions explicativos** de `scripts/motions.py`, nunca capturas de relleno ni imágenes que no tengan que ver con la frase.
- Tipos de motion (detalle en la cabecera de `motions.py`): `cronometro` (anillo que se llena hasta un valor) · `chat` (una orden que se escribe sola) · `pasos` (tarjetas numeradas que se encienden al decir cada punto, con mini-animación `rec`, `onda` o `estilos`) · `barra` (cifra que cambia de «antes» a «ahora» y barra que encoge) · `flujo` (documento → resultado con progreso y ✓) · `comentario` (burbuja donde se escribe la palabra de la CTA). Si una idea necesita otro tipo, **añádelo a `motions.py`**: no lo improvises en HTML.
- Antes de construir, enseña el storyboard del panel como tabla (tiempo · lo que dice · animación) y espera el OK.
- Cubre todo el vídeo con el panel (sin huecos vacíos). Usa `"mantener_subtitulos": true` y `"graficos": []`: en este formato el panel ya hace de gráfico.
- Subtítulos en la costura entre los dos paneles.
- Textos del panel de 28 px o más, y el último elemento al menos 2 s en pantalla (lo comprueba `hyperframes check`).

## Recuadro
Pon `"formato": "recuadro"` en `plan.json`.
- **Fondo, misma regla que la pantalla dividida:** si el usuario tiene una **grabación de pantalla o un clip real**, va de fondo (`"fondo": "../03_recursos/fondo/<grabación>.mp4"`, sin sonido, al menos tan largo como el vídeo). Si no, el fondo es azul noche y la franja de abajo se rellena con **motions explicativos** (`"panel": [...]`, los mismos tipos de `motions.py`, ver Pantalla dividida). Nunca imágenes de relleno.
- Persona en un recuadro **centrado** arriba (270×480, x 405-675, y 288-768), radio 32 px y borde menta de 4 px, sin zoom.
- Motions o gráficos en la franja de debajo (y 800-1248), a tamaño real y centrados.
- Subtítulos sobre el pecho, en la parte baja del recuadro.
- Usa `"mantener_subtitulos": true` y `"graficos": []` cuando el fondo son motions.

## 4K
Solo con tarjeta NVIDIA. Todo en 2160×3840: multiplica por 2 las medidas en px de los estilos, zonas seguras y plantillas.
