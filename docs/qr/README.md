# Códigos QR de ScriptLens IA

Códigos reales generados con la biblioteca [segno](https://pypi.org/project/segno/) (norma ISO/IEC 18004). Apuntan directamente a las URL oficiales, sin acortadores ni servicios intermedios, así que no caducan.

| Código | Lleva a | Texto para el póster |
|---|---|---|
| **Principal** | <https://jorgegutho21.github.io/ScriptLens/> | ESCANEA Y DESCUBRE SCRIPTLENS IA |
| Secundario | <https://github.com/JorgeGutho21/ScriptLens> | VER CÓDIGO FUENTE Y DOCUMENTACIÓN |

## Archivos

| Archivo | Uso |
|---|---|
| `qr_scriptlens_pagina_oficial.png` / `.svg` | QR principal solo, con su margen blanco |
| `qr_scriptlens_github.png` / `.svg` | QR del repositorio solo, con su margen blanco |
| `qr_scriptlens_poster.png` | Composición con logotipo, ambos códigos y textos (3000 × 4350 px; 20 × 29 cm a 381 ppp) |
| `qr_scriptlens_poster.svg` | La misma composición en vectores |
| `qr_scriptlens_poster.pdf` | Hoja de impresión vectorial de 200 × 290 mm; los códigos se mantienen nítidos a cualquier escala |
| `VERIFICACION.md` | Resultado de la decodificación automática de todos los archivos |

## Características técnicas

- Versión 4 (33 × 33 módulos), corrección de errores **Q** (tolera ~25 % del símbolo dañado), modo byte.
- Margen de **4 módulos** blancos alrededor, incluido en cada archivo.
- Módulos azul casi negro `#08111F` sobre blanco puro: contraste de ~19 : 1.
- Nada encima de los módulos: el logotipo va fuera del código.
- PNG de 2460 × 2460 px marcados a 300 ppp (20,8 cm). El SVG es vectorial y se puede ampliar sin perder calidad.

## Cómo usarlos en el póster

- **Tamaño:** el QR principal debe medir al menos **5 × 5 cm** sin contar el margen; recomendado 8 a 10 cm. Regla práctica: distancia de lectura ≈ 10 × el lado del código (8 cm → hasta unos 80 cm).
- **Canva:** sube el `.svg` (o el `.png` si Canva no conserva los colores) y no apliques filtros, transparencias, sombras sobre el código ni lo estires de forma desigual.
- **PowerPoint:** *Insertar → Imágenes* con el `.svg`. Al cambiar el tamaño, mantén pulsado Mayús para conservar la proporción.
- **Imprenta:** entrega el `qr_scriptlens_poster.pdf` o inserta los `.svg` en el diseño. Deja siempre el margen blanco alrededor del código.
- Antes de imprimir el póster final, escanea una prueba impresa con dos o tres celulares distintos (Android e iPhone) desde la distancia a la que estará el público.

## Regenerar y verificar

```powershell
python -m venv .venv-qr; .\.venv-qr\Scripts\pip install -r scripts\qr\requirements.txt
.\.venv-qr\Scripts\python scripts\qr\generar_qr.py
.\scripts\qr\renderizar_poster.ps1
.\.venv-qr\Scripts\python scripts\qr\verificar_qr.py
```

`verificar_qr.py` decodifica cada archivo con dos bibliotecas independientes (ZXing-C++ y OpenCV), exige que el texto sea idéntico a la URL y simula condiciones de una foto con celular (5 cm a baja resolución, desenfoque, giro, perspectiva, JPEG, ruido y poco contraste).
