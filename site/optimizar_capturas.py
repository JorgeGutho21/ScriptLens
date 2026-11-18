"""Genera las versiones web (WebP) de las capturas que usa la página de presentación.

Los PNG originales se conservan en ``docs/capturas`` y ``docs/instalacion/capturas`` para la
documentación; aquí solo se crean copias reducidas en ``site/img``:
``nombre.webp`` (ancho máximo 1440 px) y ``nombre-p.webp`` (ancho máximo 720 px, miniaturas).

Uso (PowerShell, desde la raíz del repositorio):
    .\\.venv\\Scripts\\python site\\optimizar_capturas.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "img"
APP = ROOT / "docs" / "capturas"
INST = ROOT / "docs" / "instalacion" / "capturas"

FUENTES = [
    *(APP / f for f in (
        "34_panel_general.png", "04_procesos.png", "05_detalle_proceso.png", "06_arbol_procesos.png", "07_optimizar.png",
        "09_seguridad.png", "10_analisis_script.png", "11_script_lineas_attack.png", "13_comparar.png", "15_informes.png",
        "16_modo_claro.png", "19_informe_pdf.png", "20_ajustes_privacidad.png", "21_estadisticas.png",
        "22_auditoria_30_controles.png", "23_remoto_desactivado.png", "24_remoto_activado.png", "25_remoto_solicitud.png",
        "26_celular_vincular.png", "26b_celular_esperando.png", "27_celular_en_vivo.png", "28_remoto_dispositivo_vinculado.png",
        "29_vincular_computadora.png", "30_mis_computadoras.png", "31_detalle_otra_pc.png", "32_equipo_desconectado.png",
        "33_asistente_modos.png", "01_bienvenida.png",
    )),
    *(INST / f for f in (
        "03_assets.png", "10_instalador_bienvenida.png", "11_instalador_licencia.png", "12_instalador_ya_instalado.png",
        "13_instalador_carpeta.png", "14_instalador_instalando.png", "15_instalador_completado.png", "16_instalador_finalizar.png",
    )),
]


def guardar(img: Image.Image, ancho: int, destino: Path) -> None:
    if img.width > ancho:
        img = img.resize((ancho, round(img.height * ancho / img.width)), Image.LANCZOS)
    img.save(destino, "WEBP", quality=82, method=6)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for src in FUENTES:
        img = Image.open(src).convert("RGB")
        celular = img.height > img.width  # capturas de la vista móvil (390 px a escala 2)
        nombre = src.stem
        guardar(img, 640 if celular else 1440, OUT / f"{nombre}.webp")
        guardar(img, 360 if celular else 720, OUT / f"{nombre}-p.webp")
        total += (OUT / f"{nombre}.webp").stat().st_size + (OUT / f"{nombre}-p.webp").stat().st_size
    print(f"{len(FUENTES)} capturas optimizadas en {OUT} ({total / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
