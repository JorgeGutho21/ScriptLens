# Estado del desarrollo — ScriptLens IA

Última actualización: 2026-11-15 · Rama: `feat/desarrollo-integral` · Último commit: ver `git log -1`.

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
| 9 | Instalador NSIS verificado (49,26 MB) | ✅ |
| 10 | Documentación APA 7, manual, material de exposición, pull request | ✅ (PR abierto, sin fusionar) |

## Verificación final (2026-11-15)

- 110 pruebas de pytest aprobadas; compilación de la interfaz y `cargo check` correctos; CI en verde.
- Enlaces internos de la documentación y figuras de los documentos: todos existen.
- Licencias de dependencias directas coherentes con `THIRD_PARTY_NOTICES.md`.
- Instalador: `src-tauri\target\release\bundle\nsis\ScriptLens IA_0.1.0_x64-setup.exe`, SHA-256 `D4BAAB386E9B5CDF6E8700E0CA8784767C9282D4D69AA389204495B207C8C484` (no versionado en Git; regenerable con `scripts\construir_instalador.ps1`).

## Entregables

| Documento | Ruta |
|---|---|
| Documentación técnica (47 págs.) | `docs/desarrollo/Documentacion_Tecnica_ScriptLens_IA.docx/.pdf` |
| Informe ExpoSoftware (20 págs.) | `docs/expo_software/ExpoSoftware_2026_II_ScriptLens_IA.docx/.pdf` |
| Manual de usuario (20 págs.) | `docs/manual_usuario/Manual_Usuario_ScriptLens_IA.pdf` |
| Presentación (12 diapositivas) | `docs/expo_software/ScriptLens_IA_ExpoSoftware.pptx/.pdf` |
| Guion, demostración, FAQ del jurado | `docs/expo_software/guion_exposicion.md` |
| Guía de instalación | `docs/instalacion/INSTALACION.md` |
| Notas de versión (borrador) | `docs/release/v0.1.0.md` |

## Pendientes que requieren al autor

1. **Revisar y fusionar el pull request** hacia `main` (no se fusiona automáticamente).
2. **Publicar la release v0.1.0** en GitHub Releases con el instalador y su `.sha256` (requiere autorización expresa). Tras fusionar, el flujo `instalador.yml` puede generarlos con «Run workflow».
3. **Confirmar la grafía oficial del docente** (los documentos del ZIP dicen «Oswaldo Rueda Carreño»; el prompt mencionaba «Carrión»).
4. **Capturas del instalador paso a paso:** solo se capturó la primera pantalla porque no se autorizó el control del instalador.
5. Opcionales: firma de código del instalador, imágenes de marca propias en el asistente NSIS (hoy usa la imagen lateral genérica), segundo etiquetador para el kappa de Cohen, pruebas de usabilidad con principiantes.

## Reanudar (PowerShell, en `C:\Users\Usuario\Documents\ScriptLens`)

```powershell
git switch feat/desarrollo-integral
.\.venv\Scripts\python -m pytest -p no:warnings -q
.\.venv\Scripts\python docs\academico\generar_documentos.py; .\docs\academico\exportar_pdf.ps1
. .\scripts\msvc-env.ps1; .\scripts\construir_instalador.ps1
```
