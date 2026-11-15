# Catálogo de estilos de edición DECODIK · v0.2

Formatos habituales en redes sociales, descritos y nombrados por DECODIK. Son **ideas de formato** (no protegibles); la implementación es nuestra, sobre bases open source (ver `CLAUDE.md` → Stack).

## Arquitectura (cómo se usa el catálogo)
```
catálogo (este archivo → luego estilos.json)
   └─ selector: el talento nombra un estilo, o la skill propone 2 según brief + guion
        └─ ficha de estilo (fase 4): estilo + capa de marca (colores, letra, logo, señalización)
             └─ motor: ffmpeg (corte, montaje) + HyperFrames (subtítulos, textos, gráficos)
                  └─ render 9:16 (+ 4:5 / 1:1 si el brief lo pide)
```
Reglas comunes a todos los estilos: gancho visible desde el frame 0 · subtítulos en zona segura · nada tiembla sin motivo · voz por encima de la música · señalización de publicidad en vídeos de marca · solo material propio o con permiso.

Prioridad: **D1** = día 1 · **v1** · **v2**.

---

## A. Capa base: subtítulos y texto (se combinan con cualquier estilo)
| Id | Nombre DECODIK | Qué se ve | Base técnica | Prioridad |
|---|---|---|---|---|
| sub-nativo | Subtítulo nativo | Subtítulos pequeños tipo red social, 1-4 palabras, a media altura | HyperFrames captions | **D1** |
| sub-palabra | Palabra a palabra | Una palabra cada vez, grande, la que suena resaltada | HyperFrames captions | **D1** |
| sub-clave | Palabra clave gigante | Subtítulo normal y, en las frases importantes, la palabra clave enorme | HyperFrames captions + overlay | v1 |
| sub-detras | Texto detrás de ti | La palabra clave aparece detrás de la persona (recorte) | HyperFrames embedded captions | v2 |

## B. Estilos UGC para marcas (prioridad del modo UGC)
| Id | Nombre DECODIK | Qué se ve | Cuándo en UGC | Prioridad |
|---|---|---|---|---|
| ugc-nativo | UGC natural | Tú hablando a cámara, cortes rápidos, subtítulo nativo, planos de producto por corte seco. Parece hecho por un creador, no por una marca | Por defecto en casi todos los briefs | **D1** |
| problema-solucion | Problema → solución | Gancho con el problema, tú contándolo, entra el producto como solución, demostración, CTA | Producto que resuelve algo concreto | **D1** |
| unboxing | Unboxing / primera impresión | Caja cerrada, apertura, detalles en planos cortos, tu reacción, primer uso | Lanzamientos, envíos de producto | **D1** |
| prueba-producto | Lo pruebo por ti | Uso real del producto en situación deportiva (entreno, partido, grada, viaje), con tu voz explicando | Material deportivo, nutrición, tecnología | v1 |
| razones | 3 razones | Número grande por razón, plano de producto en cada una, cierre con CTA | Brief con 3 mensajes clave | v1 |
| antes-despues-producto | Antes y después | Misma escena sin y con el producto, etiqueta ANTES / DESPUÉS | Solo si el cambio es real y demostrable | v1 |
| comparativa-honesta | Comparativa honesta | Dos opciones lado a lado, criterios claros, el producto gana con argumentos | Si el brief permite comparar (¡nunca nombrar competidores si está prohibido!) | v2 |
| reaccion-producto | Reacción | Tu cara en pequeño reaccionando a algo (contenido de la marca, resultado del producto) | Campañas con contenido de la marca | v2 |
| dia-con | Un día con… | Mini vlog (día de partido, entreno, viaje) con el producto integrado de forma natural | Lifestyle, eventos de marca | v1 |

## C. Formatos de lista y ranking (marca personal y UGC)
| Id | Nombre DECODIK | Qué se ve | Prioridad |
|---|---|---|---|
| lista-rapida | Lista rápida | Número del punto grande + plano de apoyo por punto; la lista se va completando a un lado | **D1** |
| ranking-niveles | Ranking por niveles | Tabla de niveles que se va llenando mientras hablas | **D1** |
| top-cinco | Top 5 | Marcador del 5 al 1, se revela cada puesto | v1 |
| si-no | Sí / No | Dos columnas (haz / no hagas) que se llenan al decirlas | v1 |

## D. Formatos de explicación
| Id | Nombre DECODIK | Qué se ve | Prioridad |
|---|---|---|---|
| hablo-muestro | Hablo y te enseño | Hablas a cámara y la prueba (captura, foto, dato) aparece sobre tu cabeza cuando la nombras | v1 |
| pantalla-partida | Pantalla partida | Contenido arriba (jugada, captura, producto), tú abajo | v1 |
| pizarra | Pizarra | Dibujo o esquema que se construye mientras explicas (táctica, regla, cómo funciona) | v2 |
| cifras | Explicado con cifras | Datos grandes que aparecen al decirlos, con fuente en pantalla | v2 |

## E. Formatos de personaje y conversación
| Id | Nombre DECODIK | Qué se ve | Prioridad |
|---|---|---|---|
| dos-de-ti | Dos de ti | Dos versiones tuyas (dos planos, dos ropas) que debaten | v1 |
| fan-vs-realidad | Expectativa vs. realidad | Dos escenas enfrentadas con etiqueta | v1 |

## F. Formatos de vídeo largo
| Id | Nombre DECODIK | Qué se ve | Prioridad |
|---|---|---|---|
| clips-largo | Clips de vídeo largo | De un podcast, entrevista o directo salen los mejores clips verticales con gancho y subtítulos | v1 |
| youtube-capitulos | YouTube por capítulos | 16:9, marcador de capítulos y textos clave | v2 |

---

## Selector: qué estilo proponer (modo UGC)
| Si el brief / guion… | Propón |
|---|---|
| no pide estilo concreto | UGC natural · Problema → solución |
| es un lanzamiento o un envío de producto | Unboxing · UGC natural |
| tiene 3 mensajes clave | 3 razones · Lista rápida |
| pide demostrar el producto | Lo pruebo por ti · Antes y después |
| es para un evento o una experiencia | Un día con… · UGC natural |
| es para anuncio pagado | UGC natural + 3 variantes de gancho (v1) |

## Bases técnicas por pieza
- **Subtítulos (capa A):** skills oficiales de HyperFrames para subtítulos (Apache-2.0), descargadas de `heygen-com/hyperframes`.
- **Overlays, números, tablas, etiquetas:** composiciones HTML propias renderizadas con HyperFrames.
- **Corte y montaje:** ffmpeg + transcripción con whisper.
- **Animación por código (v2):** packs MIT de `iart-ai`, desde sus repositorios originales.
Toda base usada se anota en `CREDITOS.md` con repositorio y licencia.
