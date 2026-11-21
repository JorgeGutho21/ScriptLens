# Verificación de los códigos QR

Generada por `scripts/qr/verificar_qr.py` el 2026-11-21. Decodificadores: ZXing-C++ 3.1.1 y OpenCV 5.1.0; códigos generados con segno 1.6.6.

| Código | URL esperada |
|---|---|
| `qr_scriptlens_pagina_oficial` | <https://jorgegutho21.github.io/ScriptLens/> |
| `qr_scriptlens_github` | <https://github.com/JorgeGutho21/ScriptLens> |

Cada prueba exige que el texto decodificado sea **idéntico** a la URL esperada (sin acortadores ni redirecciones).

| Archivo | Prueba | Resultado de la decodificación | Estado |
|---|---|---|---|
| `qr_scriptlens_pagina_oficial.png` | Datos del símbolo | Versión 4, corrección Q, modo byte, 41 módulos con margen de 4; 2460 px a 300 ppp = 20.8 cm | Correcto |
| `qr_scriptlens_pagina_oficial.png` | Archivo original | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_pagina_oficial.svg` | Módulos idénticos a la matriz calculada | Comparación módulo a módulo | Correcto |
| `qr_scriptlens_pagina_oficial.svg` | SVG rasterizado | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_pagina_oficial.png` | Impreso a 5 cm y leído a 150 ppp (367 px) | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_pagina_oficial.png` | Desenfoque (radio 2 px) | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_pagina_oficial.png` | Girado 17° | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_pagina_oficial.png` | Perspectiva (foto en ángulo) | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_pagina_oficial.png` | JPEG de calidad 25 | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_pagina_oficial.png` | Ruido por píxel sin suavizar (σ = 20) | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_pagina_oficial.png` | Ruido fuerte (σ = 40) con el suavizado de una cámara | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_pagina_oficial.png` | Poco contraste (gris 90 sobre 200) | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_github.png` | Datos del símbolo | Versión 4, corrección Q, modo byte, 41 módulos con margen de 4; 2460 px a 300 ppp = 20.8 cm | Correcto |
| `qr_scriptlens_github.png` | Archivo original | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_github.svg` | Módulos idénticos a la matriz calculada | Comparación módulo a módulo | Correcto |
| `qr_scriptlens_github.svg` | SVG rasterizado | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_github.png` | Impreso a 5 cm y leído a 150 ppp (367 px) | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_github.png` | Desenfoque (radio 2 px) | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_github.png` | Girado 17° | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_github.png` | Perspectiva (foto en ángulo) | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_github.png` | JPEG de calidad 25 | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_github.png` | Ruido por píxel sin suavizar (σ = 20) | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_github.png` | Ruido fuerte (σ = 40) con el suavizado de una cámara | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_github.png` | Poco contraste (gris 90 sobre 200) | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_poster.png` | Composición original: ambos códigos a la vez | ZXing ✔ | Correcto |
| `qr_scriptlens_poster.png` | Composición original: código de página oficial enfocado | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_poster.png` | Composición original: código de GitHub enfocado | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_poster.png` | Composición reducida a ¼ (foto de lejos): ambos códigos | ZXing ✔ | Correcto |
| `qr_scriptlens_poster.png` | Composición reducida, en perspectiva y desenfocada: ambos códigos | ZXing ✔ | Correcto |
| `qr_scriptlens_poster.pdf` | Tamaño de página | 200 × 290 mm, 1 página | Correcto |
| `qr_scriptlens_poster.pdf` | PDF rasterizado a 150 ppp: ambos códigos a la vez | ZXing ✔ | Correcto |
| `qr_scriptlens_poster.pdf` | PDF rasterizado a 150 ppp: código de página oficial enfocado | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_poster.pdf` | PDF rasterizado a 150 ppp: código de GitHub enfocado | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_poster.pdf` | PDF rasterizado a 300 ppp: ambos códigos a la vez | ZXing ✔ | Correcto |
| `qr_scriptlens_poster.pdf` | PDF rasterizado a 300 ppp: código de página oficial enfocado | ZXing ✔ · OpenCV ✔ | Correcto |
| `qr_scriptlens_poster.pdf` | PDF rasterizado a 300 ppp: código de GitHub enfocado | ZXing ✔ · OpenCV ✔ | Correcto |

Las pruebas de desenfoque, giro, perspectiva, compresión, ruido y contraste son simulaciones por software de una foto con celular. Límite observado: con ruido por píxel de σ ≥ 25 y sin ningún suavizado, ZXing deja de leer el código de 5 cm (OpenCV sí lo lee); las cámaras de celular suavizan ese ruido, y con ese suavizado ambos leen hasta σ = 40. Conviene escanear también el póster impreso con dos o tres celulares antes de la exposición.
