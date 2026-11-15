"""Genera las imágenes de marca del instalador NSIS a partir del icono de ScriptLens IA.

NSIS exige mapas de bits BMP de 24 bits: barra lateral de 164 × 314 px (pantallas de
bienvenida y finalización) y encabezado de 150 × 57 px (resto de pantallas).

Uso (PowerShell, raíz del repositorio):
    .\\.venv\\Scripts\\python scripts\\generar_imagenes_instalador.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "src-tauri" / "icons" / "128x128@2x.png"
OUT = ROOT / "src-tauri" / "installer"
FONTS = Path(r"C:\Windows\Fonts")

TOP, BOTTOM = (17, 27, 46), (7, 11, 18)  # degradado del icono (#111B2E → #070B12)
ACCENT = (59, 140, 255)
TEXT, MUTED = (232, 238, 247), (148, 163, 184)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    for candidate in (name, "segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(str(FONTS / candidate), size)
        except OSError:
            continue
    return ImageFont.load_default()


def gradient(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(round(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = c
    return img


def centered(draw: ImageDraw.ImageDraw, y: int, text: str, f, fill, width: int) -> int:
    box = draw.textbbox((0, 0), text, font=f)
    draw.text(((width - (box[2] - box[0])) / 2, y), text, font=f, fill=fill)
    return y + (box[3] - box[1]) + 6


def sidebar() -> Image.Image:
    w, h = 164, 314
    img = gradient(w, h)
    icon = Image.open(ICON).convert("RGBA").resize((88, 88), Image.LANCZOS)
    img.paste(icon, ((w - 88) // 2, 34), icon)
    d = ImageDraw.Draw(img)
    y = centered(d, 136, "ScriptLens", font("seguisb.ttf", 19), TEXT, w)
    y = centered(d, y - 2, "IA", font("seguisb.ttf", 19), ACCENT, w)
    d.line([(32, y + 8), (w - 32, y + 8)], fill=(34, 50, 74), width=1)
    y += 18
    small = font("segoeui.ttf", 11)
    for line in ("Desarrollado por", "Jorge Gutiérrez", "@JorgeGutho21"):
        y = centered(d, y, line, small, TEXT if line != "Desarrollado por" else MUTED, w)
    y += 10
    for line in ("Universidad Popular", "del Cesar", "ExpoSoftware 2026-II"):
        y = centered(d, y, line, small, MUTED, w)
    return img


def header() -> Image.Image:
    w, h = 150, 57
    img = Image.new("RGB", (w, h), (255, 255, 255))
    icon = Image.open(ICON).convert("RGBA").resize((40, 40), Image.LANCZOS)
    img.paste(icon, (w - 40 - 8, (h - 40) // 2), icon)
    d = ImageDraw.Draw(img)
    f = font("seguisb.ttf", 14)
    d.text((8, 12), "ScriptLens", font=f, fill=(15, 23, 42))
    d.text((8, 30), "IA", font=f, fill=(31, 111, 235))
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sidebar().save(OUT / "sidebar.bmp", "BMP")
    header().save(OUT / "header.bmp", "BMP")
    print(f"Imágenes generadas en {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
