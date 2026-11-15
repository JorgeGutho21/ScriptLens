# Estado del desarrollo — ScriptLens IA

Última actualización: 2026-11-15 · Rama: `feat/desarrollo-integral` · PR [#1](https://github.com/JorgeGutho21/ScriptLens/pull/1) fusionado en `main` (`d376dbb`) · Release [v0.1.0](https://github.com/JorgeGutho21/ScriptLens/releases/tag/v0.1.0) publicada · Último commit: ver `git log -1`.

## Fases

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Arquitectura, diseño, monitoreo real, panel | ✅ |
| 2 | Administrador de procesos | ✅ |
| 3 | Historial SQLite, comparación, privacidad | ✅ |
| 4 | Auditoría de seguridad de Windows | ✅ |
| 5 | Analizador de scripts y clasificador evaluado | ✅ |
| 6 | Acciones supervisadas | ✅ |
| 7 | Asistente local con verificación de cifras | ✅ |
| 8 | Informes PDF/HTML | ✅ |
| 9 | Instalador NSIS | ✅ |
| 10 | Documentación APA 7, manual, material de exposición, pull request | ✅ |
| 11 | Revisión de cierre: defectos P1, OneDrive, asistente, diálogos, identidad del instalador, guía de instalación, compatibilidad | ✅ |
| 12 | Publicación de v0.1.0 y capturas reales de GitHub en la guía | ✅ |

## Verificación final (2026-11-15)

- 135 pruebas de pytest aprobadas (14 archivos); compilación de la interfaz con tipos y `cargo check` correctos.
- Los dos defectos P1 del PR están corregidos, con pruebas de regresión, y verificados en la aplicación instalada.
- Instalador final: `build\release\ScriptLens-IA_0.1.0_x64-setup.exe` (51 678 985 bytes), SHA-256 `111397CF7D8164943D79F99488F3B868603A4CA32053D116D8B522AC37B6D13A`. No se versiona en Git; se regenera con `scripts\construir_instalador.ps1`.
- Ciclo del instalador final en Windows 11 (sesión sin elevación): instalación y actualización silenciosas, apertura desde el menú Inicio, motor solo en 127.0.0.1, instancia única, cierre normal y forzado sin huérfanos, desinstalación conservando historial e informes, reinstalación. Detalle en `docs/pruebas/compatibilidad.md`.

## Entregables

| Documento | Ruta |
|---|---|
| README (página de instalación) | `README.md` |
| Guía de instalación para principiantes (13 págs.) | `docs/instalacion/Guia_Instalacion_ScriptLens_IA.docx/.pdf` |
| Manual de usuario (20 págs.) | `docs/manual_usuario/Manual_Usuario_ScriptLens_IA.docx/.pdf` |
| Documentación técnica (50 págs.) | `docs/desarrollo/Documentacion_Tecnica_ScriptLens_IA.docx/.pdf` |
| Informe ExpoSoftware (20 págs.) | `docs/expo_software/ExpoSoftware_2026_II_ScriptLens_IA.docx/.pdf` |
| Presentación (12 diapositivas) y guion | `docs/expo_software/ScriptLens_IA_ExpoSoftware.pptx/.pdf`, `guion_exposicion.md` |
| Matriz de compatibilidad | `docs/pruebas/compatibilidad.md` |
| Notas de la versión | `docs/release/v0.1.0.md` |

## Publicación (2026-11-15)

- El autor fusionó el PR #1 en `main` (`d376dbb`); el árbol de `main` es idéntico al del commit desde el que se construyó el instalador (`fdd63c5`).
- Release `v0.1.0` publicada sobre `d376dbb`, marcada como *Latest*, con `ScriptLens-IA_0.1.0_x64-setup.exe` y su `.sha256`. Se descargaron ambos archivos desde la URL pública y la huella coincide (`111397CF…B6D13A`, 51 678 985 bytes).
- La guía de instalación incluye las capturas reales de la página del repositorio, de la versión y de sus archivos (Assets).

## Estado en GitHub (2026-11-15)

| Elemento | Estado |
|---|---|
| Rama `main` | Contiene todo el desarrollo (PR #1, #2 y #3 fusionados); CI en verde en cada commit |
| Release | [v0.1.0](https://github.com/JorgeGutho21/ScriptLens/releases/tag/v0.1.0), *Latest*, instalador y `.sha256` verificados por descarga pública |
| Actualizaciones | «Buscar actualizaciones» (API `releases/latest`) responde «Tiene la versión más reciente» |
| Flujo «Instalador de Windows» | Ejecutado sobre `main` (`1d7bfd6`) en un equipo limpio de GitHub: pruebas, compilación e instalador generados con éxito; el artefacto contiene `ScriptLens-IA_0.1.0_x64-setup.exe` (51 522 853 bytes) y su `.sha256` coherente. El tamaño difiere del instalador publicado porque la compilación no es reproducible bit a bit; el publicado es el verificado en el equipo de pruebas |
| Apartado *About* | Descripción, enlace a la última versión y temas configurados |
| Issues | Habilitados para errores y sugerencias |

## Pendientes

1. **Capturas de las pantallas 2–6 del instalador:** no se autorizó controlarlo. El autor puede ejecutar `.\scripts\capturar-instalador.ps1 -Instalador .\build\release\ScriptLens-IA_0.1.0_x64-setup.exe` y recorrerlo; el script guarda cada pantalla.
2. **Confirmar la grafía oficial del docente:** los documentos originales dicen «Oswaldo Rueda Carreño»; no se encontró una fuente institucional pública que lo confirme.
3. Opcionales: firma de código del instalador, pruebas en Windows 10 y en equipos con 4 GB de RAM, segundo etiquetador para el kappa de Cohen, pruebas de usabilidad con principiantes.

## Reanudar (PowerShell, en `C:\Users\Usuario\Documents\ScriptLens`)

```powershell
git switch feat/desarrollo-integral
.\.venv\Scripts\python -m pytest -p no:warnings -q
.\.venv\Scripts\python docs\academico\generar_documentos.py; .\docs\academico\exportar_pdf.ps1
.\scripts\construir_instalador.ps1            # o -OmitirMotor si solo cambió la interfaz
```
