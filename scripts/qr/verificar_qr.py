"""Decodifica los QR de docs/qr/ y comprueba que contienen la URL exacta.

Usa dos decodificadores independientes (ZXing-C++ y OpenCV) y somete cada código
a condiciones parecidas a una foto con celular: tamaño mínimo de impresión,
desenfoque, giro, perspectiva, compresión JPEG, ruido y poco contraste.
Escribe el resultado en docs/qr/VERIFICACION.md y termina con error si falla algo.

    python scripts/qr/verificar_qr.py
"""

from __future__ import annotations

import io
import re
import sys
from datetime import date
from importlib.metadata import version
from pathlib import Path

import cv2
import numpy as np
import pypdfium2 as pdfium
import zxingcpp
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from generar_qr import CODIGOS, MARGEN, crear  # noqa: E402

QR = Path(__file__).resolve().parents[2] / "docs" / "qr"
URLS = {n: d["url"] for n, d in CODIGOS.items()}
filas: list[tuple[str, str, str, str]] = []
fallos = 0


def leer_zxing(img: Image.Image) -> set[str]:
    return {r.text for r in zxingcpp.read_barcodes(img.convert("L")) if r.format == zxingcpp.BarcodeFormat.QRCode}


def leer_opencv(img: Image.Image) -> set[str]:
    arr = np.array(img.convert("L"))
    det = cv2.QRCodeDetector()
    ok, textos, _, _ = det.detectAndDecodeMulti(arr)
    encontrados = {t for t in textos if t} if ok else set()
    if not encontrados:
        texto, _, _ = det.detectAndDecode(arr)
        if texto:
            encontrados.add(texto)
    return encontrados


def comprobar(prueba: str, archivo: str, img: Image.Image, esperadas: set[str], opencv: bool = True) -> None:
    global fallos
    zx = leer_zxing(img)
    ok_zx = esperadas <= zx and zx <= set(URLS.values())
    estado = ["ZXing ✔" if ok_zx else f"ZXing ✘ {sorted(zx)}"]
    ok = ok_zx
    if opencv:
        cvs = leer_opencv(img)
        ok_cv = esperadas <= cvs and cvs <= set(URLS.values())
        estado.append("OpenCV ✔" if ok_cv else f"OpenCV ✘ {sorted(cvs)}")
        ok = ok and ok_cv
    if not ok:
        fallos += 1
    filas.append((archivo, prueba, " · ".join(estado), "Correcto" if ok else "FALLA"))


def svg_a_imagen(ruta: Path, px_modulo: int = 20) -> Image.Image:
    """Rasteriza el SVG propio (rectángulos de módulos) sin depender de otro programa."""
    texto = ruta.read_text(encoding="utf-8")
    total = int(re.search(r'viewBox="0 0 (\d+) ', texto).group(1))
    d = re.search(r'<path[^>]* d="([^"]+)"', texto).group(1)
    img = Image.new("L", (total * px_modulo,) * 2, 255)
    dib = ImageDraw.Draw(img)
    for x, y, w, h in re.findall(r"M([\d.]+) ([\d.]+)h([\d.]+)v([\d.]+)h-[\d.]+z", d):
        x, y, w, h = (float(v) * px_modulo for v in (x, y, w, h))
        dib.rectangle([x, y, x + w - 1, y + h - 1], fill=0)
    return img


def perspectiva(img: Image.Image, f: float = 0.12) -> Image.Image:
    arr = np.array(img.convert("L"))
    h, w = arr.shape
    org = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[w * f, h * f * .6], [w * (1 - f * .3), 0], [w, h], [w * f * .5, h * (1 - f)]])
    m = cv2.getPerspectiveTransform(org, dst)
    return Image.fromarray(cv2.warpPerspective(arr, m, (w, h), borderValue=255))


def jpeg(img: Image.Image, calidad: int) -> Image.Image:
    b = io.BytesIO()
    img.convert("L").save(b, "JPEG", quality=calidad)
    return Image.open(io.BytesIO(b.getvalue()))


def ruido(img: Image.Image, sigma: float) -> Image.Image:
    arr = np.array(img.convert("L"), dtype=np.float32)
    arr += np.random.default_rng(7).normal(0, sigma, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def poco_contraste(img: Image.Image) -> Image.Image:
    arr = np.array(img.convert("L"), dtype=np.float32)
    return Image.fromarray((90 + arr * (200 - 90) / 255).astype(np.uint8))  # oscuro 90, claro 200


def main() -> None:
    np.random.seed(7)
    for nombre, url in URLS.items():
        base = f"qr_scriptlens_{nombre}"
        qr = crear(url)

        png = Image.open(QR / f"{base}.png")
        lado_cm = png.width / png.info.get("dpi", (300, 300))[0] * 2.54
        filas.append((f"{base}.png", "Datos del símbolo",
                      f"Versión {qr.version}, corrección {qr.error}, modo byte, {qr.symbol_size(border=MARGEN)[0]} módulos "
                      f"con margen de {MARGEN}; {png.width} px a 300 ppp = {lado_cm:.1f} cm", "Correcto"))
        comprobar("Archivo original", f"{base}.png", png, {url})

        # El SVG debe reproducir exactamente la matriz de segno
        svg = svg_a_imagen(QR / f"{base}.svg", px_modulo=1)
        esperado = np.array(qr.matrix, dtype=bool)
        obtenido = ~np.array(svg, dtype=bool)[MARGEN:-MARGEN, MARGEN:-MARGEN]
        igual = obtenido.shape == esperado.shape and bool((obtenido == esperado).all())
        filas.append((f"{base}.svg", "Módulos idénticos a la matriz calculada", "Comparación módulo a módulo",
                      "Correcto" if igual else "FALLA"))
        global fallos
        fallos += 0 if igual else 1
        comprobar("SVG rasterizado", f"{base}.svg", svg_a_imagen(QR / f"{base}.svg"), {url})

        # Tamaño mínimo de impresión: 5 cm de área de módulos a 150 ppp (calidad baja)
        px = round(5 / 2.54 * 150 * png.width / (png.width - 2 * MARGEN * 60))
        pequeno = png.convert("L").resize((px, px), Image.LANCZOS)
        comprobar(f"Impreso a 5 cm y leído a 150 ppp ({px} px)", f"{base}.png", pequeno, {url})
        comprobar("Desenfoque (radio 2 px)", f"{base}.png", pequeno.filter(ImageFilter.GaussianBlur(2)), {url})
        comprobar("Girado 17°", f"{base}.png", pequeno.rotate(17, expand=True, fillcolor=255), {url})
        comprobar("Perspectiva (foto en ángulo)", f"{base}.png", perspectiva(pequeno), {url})
        comprobar("JPEG de calidad 25", f"{base}.png", jpeg(pequeno, 25), {url})
        comprobar("Ruido por píxel sin suavizar (σ = 20)", f"{base}.png", ruido(pequeno, 20), {url})
        comprobar("Ruido fuerte (σ = 40) con el suavizado de una cámara", f"{base}.png",
                  ruido(pequeno, 40).filter(ImageFilter.GaussianBlur(0.8)), {url})
        comprobar("Poco contraste (gris 90 sobre 200)", f"{base}.png", poco_contraste(pequeno), {url})

    # Composición: ZXing debe encontrar los dos códigos en la misma imagen. Además, como una
    # persona enfoca un código a la vez, cada uno se recorta (con fondo oscuro alrededor)
    # y se lee también con OpenCV, cuyo modo de varios códigos falla con tamaños distintos.
    todas = set(URLS.values())
    zonas = {URLS["pagina_oficial"]: (380, 480, 1620, 1720), URLS["github"]: (100, 2020, 940, 2860)}  # unidades del SVG

    def composicion(prueba: str, archivo: str, img: Image.Image) -> None:
        comprobar(f"{prueba}: ambos códigos a la vez", archivo, img, todas, opencv=False)
        for url, (x0, y0, x1, y1) in zonas.items():
            k = img.width / 2000
            recorte = img.crop((round(x0 * k), round(y0 * k), round(x1 * k), round(y1 * k)))
            nombre = "página oficial" if "github.io" in url else "GitHub"
            comprobar(f"{prueba}: código de {nombre} enfocado", archivo, recorte, {url})

    poster = Image.open(QR / "qr_scriptlens_poster.png")
    composicion("Composición original", "qr_scriptlens_poster.png", poster)
    lejos = poster.convert("L").resize((poster.width // 4, poster.height // 4), Image.LANCZOS)
    comprobar("Composición reducida a ¼ (foto de lejos): ambos códigos", "qr_scriptlens_poster.png", lejos, todas, opencv=False)
    comprobar("Composición reducida, en perspectiva y desenfocada: ambos códigos", "qr_scriptlens_poster.png",
              perspectiva(lejos, .08).filter(ImageFilter.GaussianBlur(1.2)), todas, opencv=False)

    pdf = pdfium.PdfDocument(QR / "qr_scriptlens_poster.pdf")
    pagina = pdf[0]
    ancho_mm, alto_mm = (v / 72 * 25.4 for v in pagina.get_size())
    filas.append(("qr_scriptlens_poster.pdf", "Tamaño de página", f"{ancho_mm:.0f} × {alto_mm:.0f} mm, {len(pdf)} página",
                  "Correcto" if len(pdf) == 1 else "FALLA"))
    for ppp in (150, 300):
        composicion(f"PDF rasterizado a {ppp} ppp", "qr_scriptlens_poster.pdf", pagina.render(scale=ppp / 72).to_pil())

    lineas = [
        "# Verificación de los códigos QR",
        "",
        f"Generada por `scripts/qr/verificar_qr.py` el {date.today().isoformat()}. Decodificadores: "
        f"ZXing-C++ {version('zxing-cpp')} y OpenCV {cv2.__version__}; códigos generados con segno {version('segno')}.",
        "",
        "| Código | URL esperada |",
        "|---|---|",
        *[f"| `qr_scriptlens_{n}` | <{u}> |" for n, u in URLS.items()],
        "",
        "Cada prueba exige que el texto decodificado sea **idéntico** a la URL esperada (sin acortadores ni redirecciones).",
        "",
        "| Archivo | Prueba | Resultado de la decodificación | Estado |",
        "|---|---|---|---|",
        *[f"| `{a}` | {p} | {r} | {e} |" for a, p, r, e in filas],
        "",
        "Las pruebas de desenfoque, giro, perspectiva, compresión, ruido y contraste son simulaciones por software de una "
        "foto con celular. Límite observado: con ruido por píxel de σ ≥ 25 y sin ningún suavizado, ZXing deja de leer el "
        "código de 5 cm (OpenCV sí lo lee); las cámaras de celular suavizan ese ruido, y con ese suavizado ambos leen hasta σ = 40. "
        "Conviene escanear también el póster impreso con dos o tres celulares antes de la exposición.",
        "",
    ]
    (QR / "VERIFICACION.md").write_text("\n".join(lineas), encoding="utf-8")
    total = len([f for f in filas if f[3] in ("Correcto", "FALLA")])
    print(f"{total - fallos}/{total} comprobaciones correctas")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
