"""Genera los códigos QR de ScriptLens IA y la composición para el póster.

Los códigos se calculan con la biblioteca segno (ISO/IEC 18004), con corrección
de errores Q (hasta ~25 % del símbolo dañado) y un margen de 4 módulos. No se
coloca nada sobre los módulos. Uso:

    python scripts/qr/generar_qr.py            # escribe en docs/qr/

Después, `scripts/qr/renderizar_poster.ps1` crea el PNG y el PDF del póster y
`scripts/qr/verificar_qr.py` decodifica todos los archivos.
"""

from __future__ import annotations

import re
from pathlib import Path

import segno

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "docs" / "qr"
LOGO = RAIZ / "assets" / "branding" / "scriptlens-icon.svg"

CODIGOS = {
    "pagina_oficial": {
        "url": "https://jorgegutho21.github.io/ScriptLens/",
        "texto": "ESCANEA Y DESCUBRE SCRIPTLENS IA",
        "cm": 10.0,  # tamaño de impresión sugerido, con margen incluido
    },
    "github": {
        "url": "https://github.com/JorgeGutho21/ScriptLens",
        "texto": "VER CÓDIGO FUENTE Y DOCUMENTACIÓN",
        "cm": 6.5,
    },
}

MARGEN = 4          # módulos de zona silenciosa (mínimo de la norma)
OSCURO = "#08111F"  # azul casi negro de la marca; contraste ~19:1 con blanco
CLARO = "#FFFFFF"
ESCALA_PNG = 60     # px por módulo: 41 módulos → 2460 px ≈ 20,8 cm a 300 ppp


def crear(url: str) -> segno.QRCode:
    qr = segno.make_qr(url, error="q", boost_error=False, mode="byte")
    return qr


def ruta_modulos(qr: segno.QRCode, x0: float = 0, y0: float = 0, modulo: float = 1) -> str:
    """Trazado SVG de los módulos oscuros, uniendo los tramos de cada fila."""
    partes = []
    for y, fila in enumerate(qr.matrix):
        x = 0
        n = len(fila)
        while x < n:
            if fila[x]:
                inicio = x
                while x < n and fila[x]:
                    x += 1
                ancho = (x - inicio) * modulo
                px = x0 + inicio * modulo
                py = y0 + y * modulo
                partes.append(f"M{px:g} {py:g}h{ancho:g}v{modulo:g}h{-ancho:g}z")
            else:
                x += 1
    return "".join(partes)


def svg_qr(qr: segno.QRCode, cm: float, titulo: str) -> str:
    total = qr.symbol_size(scale=1, border=MARGEN)[0]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{cm * 10:g}mm" height="{cm * 10:g}mm" '
        f'viewBox="0 0 {total} {total}" shape-rendering="crispEdges">\n'
        f"  <title>{titulo}</title>\n"
        f'  <rect width="{total}" height="{total}" fill="{CLARO}"/>\n'
        f'  <path fill="{OSCURO}" d="{ruta_modulos(qr, MARGEN, MARGEN)}"/>\n'
        "</svg>\n"
    )


def logo_incrustado(x: float, y: float, lado: float) -> str:
    """Inserta el logotipo oficial con identificadores propios para no chocar con otros."""
    svg = LOGO.read_text(encoding="utf-8")
    interior = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    interior = interior.replace('id="lens"', 'id="logo-lente"').replace("url(#lens)", "url(#logo-lente)")
    interior = interior.replace('id="bg"', 'id="logo-fondo"').replace("url(#bg)", "url(#logo-fondo)")
    return f'<svg x="{x:g}" y="{y:g}" width="{lado:g}" height="{lado:g}" viewBox="0 0 64 64" fill="none">{interior}</svg>'


def tarjeta_qr(qr: segno.QRCode, x: float, y: float, lado: float, relleno: float) -> str:
    """Tarjeta blanca con el QR; el margen de 4 módulos queda dentro del QR, no en el relleno."""
    total = qr.symbol_size(scale=1, border=MARGEN)[0]
    modulo = lado / total
    return (
        f'<rect x="{x - relleno:g}" y="{y - relleno:g}" width="{lado + 2 * relleno:g}" '
        f'height="{lado + 2 * relleno:g}" rx="{relleno * 1.2:g}" fill="{CLARO}"/>'
        f'<path fill="{OSCURO}" shape-rendering="crispEdges" '
        f'd="{ruta_modulos(qr, x + MARGEN * modulo, y + MARGEN * modulo, modulo)}"/>'
    )


def poster(principal: segno.QRCode, github: segno.QRCode) -> str:
    """Composición de 20 × 29 cm (1 unidad = 0,1 mm)."""
    W, H = 2000, 2900
    fuente = "'Segoe UI', 'Segoe UI Variable Display', Inter, 'Helvetica Neue', Arial, sans-serif"
    lado_p, lado_g = 1000, 640  # 10 cm y 6,4 cm con margen: área de módulos 8,0 y 5,1 cm
    xp = (W - lado_p) / 2
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="290mm" viewBox="0 0 {W} {H}">
  <title>ScriptLens IA — códigos QR para el póster</title>
  <defs>
    <linearGradient id="fondo" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0C1A30"/>
      <stop offset="1" stop-color="#060D18"/>
    </linearGradient>
    <radialGradient id="brillo" cx="0.5" cy="0.32" r="0.55">
      <stop offset="0" stop-color="#3D8BFF" stop-opacity="0.28"/>
      <stop offset="1" stop-color="#3D8BFF" stop-opacity="0"/>
    </radialGradient>
    <pattern id="rejilla" width="80" height="80" patternUnits="userSpaceOnUse">
      <path d="M80 0H0V80" fill="none" stroke="#1D3150" stroke-width="2" opacity="0.55"/>
    </pattern>
    <linearGradient id="acento" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#6DB0FF"/>
      <stop offset="1" stop-color="#1F6FEB"/>
    </linearGradient>
  </defs>

  <rect width="{W}" height="{H}" fill="url(#fondo)"/>
  <rect width="{W}" height="1500" fill="url(#rejilla)" opacity="0.6"/>
  <rect width="{W}" height="{H}" fill="url(#brillo)"/>

  {logo_incrustado(W / 2 - 90, 110, 180)}
  <text x="{W / 2}" y="420" text-anchor="middle" font-family="{fuente}" font-size="118" font-weight="700" fill="#E9F0FA" letter-spacing="-2">ScriptLens <tspan fill="#3D8BFF">IA</tspan></text>
  <text x="{W / 2}" y="498" text-anchor="middle" font-family="{fuente}" font-size="44" fill="#A3B4CC">Diagnóstico, seguridad y supervisión de computadoras Windows</text>

  {tarjeta_qr(principal, xp, 600, lado_p, 44)}
  <text x="{W / 2}" y="1790" text-anchor="middle" font-family="{fuente}" font-size="66" font-weight="700" fill="#FFFFFF" letter-spacing="1">{CODIGOS['pagina_oficial']['texto']}</text>
  <rect x="{W / 2 - 90}" y="1822" width="180" height="8" rx="4" fill="url(#acento)"/>
  <text x="{W / 2}" y="1900" text-anchor="middle" font-family="{fuente}" font-size="44" fill="#8CBCFF">{CODIGOS['pagina_oficial']['url']}</text>

  <line x1="160" y1="2010" x2="{W - 160}" y2="2010" stroke="#1D3150" stroke-width="3"/>

  {tarjeta_qr(github, 200, 2120, lado_g, 30)}
  <text x="990" y="2230" font-family="{fuente}" font-size="54" font-weight="700" fill="#FFFFFF" letter-spacing="0.5">VER CÓDIGO FUENTE</text>
  <text x="990" y="2298" font-family="{fuente}" font-size="54" font-weight="700" fill="#FFFFFF" letter-spacing="0.5">Y DOCUMENTACIÓN</text>
  <text x="990" y="2370" font-family="{fuente}" font-size="38" fill="#8CBCFF">github.com/JorgeGutho21/ScriptLens</text>
  <text x="990" y="2500" font-family="{fuente}" font-size="38" font-weight="600" fill="#E9F0FA">Jorge Gutiérrez · @JorgeGutho21</text>
  <text x="990" y="2556" font-family="{fuente}" font-size="34" fill="#A3B4CC">Universidad Popular del Cesar</text>
  <text x="990" y="2606" font-family="{fuente}" font-size="34" fill="#A3B4CC">Ingeniería de Sistemas · ExpoSoftware 2026-II</text>
  <text x="990" y="2720" font-family="{fuente}" font-size="30" fill="#7F93B0">Windows 10 y 11 de 64 bits · gratuito y de código abierto</text>
</svg>
"""


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    qrs = {}
    for nombre, datos in CODIGOS.items():
        qr = crear(datos["url"])
        qrs[nombre] = qr
        base = SALIDA / f"qr_scriptlens_{nombre}"
        qr.save(base.with_suffix(".png"), kind="png", scale=ESCALA_PNG, border=MARGEN,
                dark=OSCURO, light=CLARO, dpi=300)
        base.with_suffix(".svg").write_text(svg_qr(qr, datos["cm"], f"{datos['texto']}: {datos['url']}"),
                                             encoding="utf-8")
        print(f"{nombre}: versión {qr.version}, corrección {qr.error}, {qr.symbol_size(border=MARGEN)[0]} módulos con margen")
    (SALIDA / "qr_scriptlens_poster.svg").write_text(poster(qrs["pagina_oficial"], qrs["github"]), encoding="utf-8")
    print("Composición SVG escrita. Ejecuta renderizar_poster.ps1 para el PNG y el PDF.")


if __name__ == "__main__":
    main()
