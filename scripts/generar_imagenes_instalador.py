"""Genera las imágenes de marca del instalador NSIS de ScriptLens IA.

NSIS ajusta las imágenes al tamaño del control sin suavizado: si las amplía se ven
borrosas y si las reduce el texto fino pierde píxeles. El control se mide en unidades
de diálogo, así que su tamaño en píxeles no es proporcional en ambos ejes: a 125 %
(escala predeterminada de muchos portátiles) la barra lateral mide 194 × 386 px y el
encabezado 177 × 70 px (medidos en Windows 11). Las imágenes se dibujan a 3× con
supermuestreo directamente a esas medidas, de modo que a 125 % se muestran píxel a
píxel, y el texto tiene tamaño suficiente para seguir legible a 100 % y 150 %.

El logotipo se toma de ``assets/branding/scriptlens-icon-1024.png``, renderizado del
SVG original sin pérdida.

Uso (PowerShell, raíz del repositorio):
    .\\.venv\\Scripts\\python scripts\\generar_imagenes_instalador.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "assets" / "branding" / "scriptlens-icon-1024.png"
OUT = ROOT / "src-tauri" / "installer"
FONTS = Path(r"C:\Windows\Fonts")
S = 3  # factor de supermuestreo
SIDEBAR = (194, 386)  # px reales del control a 125 %
HEADER = (177, 70)
K = SIDEBAR[0] / 164  # escala del diseño (trazado en unidades de 164 px de ancho)
U = K * S  # píxeles de lienzo por unidad de diseño


def u(v: float) -> int:
    return round(v * U)

TOP, BOTTOM = (16, 25, 43), (6, 9, 15)
ACCENT, ACCENT_SOFT = (77, 150, 255), (31, 111, 235)
TEXT, MUTED, FAINT, LINE = (236, 241, 248), (154, 168, 189), (104, 119, 141), (38, 52, 76)


def font(names: tuple[str, ...], size: int) -> ImageFont.FreeTypeFont:
    for name in names:
        try:
            return ImageFont.truetype(str(FONTS / name), round(size * U))
        except OSError:
            continue
    return ImageFont.load_default()


SEMIBOLD = ("seguisb.ttf", "segoeuib.ttf", "arialbd.ttf")
REGULAR = ("segoeui.ttf", "arial.ttf")
LIGHT = ("segoeuil.ttf", "segoeui.ttf", "arial.ttf")


def gradient(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(round(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3)))
    return img


def glow(base: Image.Image, center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius], fill=color + (alpha,)
    )
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.45))
    base.alpha_composite(layer)


def text_center(d: ImageDraw.ImageDraw, w: int, y: int, parts: list[tuple[str, ImageFont.FreeTypeFont, tuple]], gap: int = 0) -> int:
    widths = [d.textlength(t, font=f) for t, f, _ in parts]
    x = (w - sum(widths) - gap * (len(parts) - 1)) / 2
    height = 0
    for (t, f, c), tw in zip(parts, widths):
        d.text((x, y), t, font=f, fill=c)
        x += tw + gap
        box = d.textbbox((0, 0), t, font=f)
        height = max(height, box[3])
    return y + height


def sidebar() -> Image.Image:
    w, h = SIDEBAR[0] * S, SIDEBAR[1] * S
    img = gradient(w, h).convert("RGBA")
    logo_size = u(84)
    cx, cy = w // 2, u(96)
    glow(img, (cx, cy), u(70), ACCENT_SOFT, 70)
    logo = Image.open(LOGO).convert("RGBA").resize((logo_size, logo_size), Image.LANCZOS)
    img.alpha_composite(logo, (cx - logo_size // 2, cy - logo_size // 2))

    d = ImageDraw.Draw(img)
    y = text_center(d, w, u(154), [("ScriptLens", font(SEMIBOLD, 18), TEXT), ("IA", font(SEMIBOLD, 18), ACCENT)], gap=u(5))
    y = text_center(d, w, y + u(5), [("Diagnóstico inteligente", font(REGULAR, 9), MUTED)])

    # Créditos alineados al pie (posiciones medidas desde abajo)
    top = h - u(94)
    d.line([(u(44), top), (w - u(44), top)], fill=LINE, width=S)
    y = text_center(d, w, top + u(8), [("Desarrollado por", font(REGULAR, 9), MUTED)])
    y = text_center(d, w, y + u(3), [("Jorge Gutiérrez", font(SEMIBOLD, 11), TEXT)])
    y = text_center(d, w, y + u(2), [("@JorgeGutho21", font(SEMIBOLD, 9), ACCENT)])
    y = text_center(d, w, y + u(9), [("Universidad Popular del Cesar", font(REGULAR, 8), MUTED)])
    text_center(d, w, y + u(2), [("ExpoSoftware 2026-II", font(REGULAR, 8), MUTED)])
    return img.convert("RGB")


def header() -> Image.Image:
    w, h = HEADER[0] * S, HEADER[1] * S
    img = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    size = u(38)
    logo = Image.open(LOGO).convert("RGBA").resize((size, size), Image.LANCZOS)
    img.alpha_composite(logo, (w - size - u(9), (h - size) // 2))
    d = ImageDraw.Draw(img)
    f = font(SEMIBOLD, 13)
    x, y = u(8), (h - u(32)) // 2
    d.text((x, y), "ScriptLens", font=f, fill=(15, 23, 42))
    d.text((x + d.textlength("ScriptLens ", font=f), y), "IA", font=f, fill=ACCENT_SOFT)
    d.text((x, y + u(19)), "Jorge Gutiérrez", font=font(REGULAR, 9), fill=(71, 85, 105))
    return img.convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, img, size in (("sidebar.bmp", sidebar(), SIDEBAR), ("header.bmp", header(), HEADER)):
        img.resize(size, Image.LANCZOS).save(OUT / name, "BMP")
    print(f"Imágenes generadas en {OUT.relative_to(ROOT)}: barra {SIDEBAR}, encabezado {HEADER}")


if __name__ == "__main__":
    main()
