#!/usr/bin/env sh
# Reproduce localmente el paso «Reunir archivos» de .github/workflows/pages.yml.
# Uso (Git Bash, desde la raíz): sh scripts/construir_sitio.sh .dev-data/_site
set -e
D="${1:-.dev-data/_site}"
rm -rf "$D"
mkdir -p "$D/capturas" "$D/instalacion" "$D/docs" "$D/img"
cp site/index.html site/estilos.css site/app.js "$D/"
cp site/img/*.webp "$D/img/"
cp assets/branding/scriptlens-icon.svg "$D/logo.svg"
cp docs/capturas/*.png "$D/capturas/"
cp docs/instalacion/capturas/03_assets.png docs/instalacion/capturas/1*.png "$D/instalacion/"
cp docs/instalacion/Guia_Instalacion_ScriptLens_IA.pdf docs/manual_usuario/Manual_Usuario_ScriptLens_IA.pdf \
   docs/expo_software/ExpoSoftware_2026_II_ScriptLens_IA.pdf docs/desarrollo/Documentacion_Tecnica_ScriptLens_IA.pdf "$D/docs/"
