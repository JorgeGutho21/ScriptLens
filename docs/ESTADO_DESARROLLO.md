# Estado del desarrollo — ScriptLens IA

Última actualización: 2026-11-14 · Rama: `feat/desarrollo-integral` · Último commit: ver `git log -1`.

## Fases

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Arquitectura, diseño, monitoreo real, panel | ✅ |
| 2 | Administrador de procesos (tabla, árbol, firmas, explicaciones) | ✅ |
| 3 | Historial SQLite, comparación, privacidad | ✅ |
| 4 | Auditoría de seguridad de Windows | ✅ |
| 5 | Analizador de scripts (catálogo original + ATT&CK 20.1 + regresión logística balanceada) | ✅ |
| 6 | Acciones supervisadas con confirmación y auditoría | ✅ |
| 7 | Asistente local Ollama + qwen3:4b-instruct, verificación de cifras | ✅ |
| 8 | Informes PDF/HTML con marca de agua | ✅ |
| 9 | Motor PyInstaller, instalador NSIS (49,26 MB), SHA-256, instalación/desinstalación/reinstalación e instancia única probadas | ✅ |
| 10 | Documentación académica y PR | ⏳ **en curso** |

Instalador verificado: `src-tauri\target\release\bundle\nsis\ScriptLens IA_0.1.0_x64-setup.exe`
SHA-256: `D4BAAB386E9B5CDF6E8700E0CA8784767C9282D4D69AA389204495B207C8C484`
Pruebas: 110+ pruebas de pytest aprobadas; CI (pytest, interfaz, cargo check) en verde hasta `94884bf` (verificar el último run).

## Pendiente (fase 10) — siguiente tarea exacta

1. Actualizar `README.md` (capturas de `docs/capturas`, instalación A/B/C, configuración de IA, FAQ), `CHANGELOG.md`, `THIRD_PARTY_NOTICES.md` (añadir scikit-learn, numpy, scipy, joblib, reportlab, three, PyInstaller, tauri-plugin-single-instance, datos ATT&CK), `backend/README.md` (endpoints nuevos), `docs/desarrollo/bitacora.md` (fases 2–9 con hashes de `git log`).
2. Crear `docs/PRIVACIDAD.md`, `docs/instalacion/` y notas de versión `docs/release/v0.1.0.md` (no publicar la release sin autorización del autor).
3. Generar con python-docx (APA 7) + exportación PDF con Word: `Documentacion_Tecnica_ScriptLens_IA.docx/.pdf`, `ExpoSoftware_2026_II_ScriptLens_IA.docx/.pdf`, `Manual_Usuario_ScriptLens_IA.pdf`, presentación `.pptx` y guion. Referencias ya verificadas (DOI por Crossref): Hosmer et al. 2013; Salton & Buckley 1988; King & Zeng 2001; Cohen 1960; APA 2020; Greshake et al. 2023; Ji et al. 2023; Hendler et al. 2018; Qwen Team 2025 (arXiv 2505.09388); Pedregosa et al. 2011.
4. Revisión final, `gh pr create` hacia `main` (no fusionar).

## Hallazgos para la documentación

- Docente según los documentos del ZIP: **Oswaldo Rueda Carreño** (confirmar grafía oficial).
- `qwen3:4b` es variante de razonamiento (256 s/respuesta); se usa `qwen3:4b-instruct` (10–58 s, cifras verificadas; caso real donde el verificador marcó la cifra inventada «70»).
- ATT&CK 20.1 revocó T1562.001, T1070.001 y T1562.004 → T1685, T1685.005, T1686.
- Corrección de la regla P01 (lectura de clave Run): falsos positivos de consulta 43,3 % → 0 % en validación cruzada.
- Defectos hallados en la app instalada y corregidos: pantalla en blanco por `scrollIntoView` (Promise en WebView2), interruptor mal dibujado, instancias duplicadas, informes dentro de la carpeta del repositorio, análisis de 1 MB 10,4 s → 3,4 s.
- Primer arranque de la app instalada ≈ 25 s (motor de 159 MB analizado por Defender); siguientes ≈ 9 s.
- `instalador.yml` solo se puede lanzar manualmente tras fusionar a `main`.

## Reanudar (PowerShell, en `C:\Users\Usuario\Documents\ScriptLens`)

```powershell
git switch feat/desarrollo-integral
.\.venv\Scripts\python -m pytest -p no:warnings -q
. .\scripts\msvc-env.ps1
.\scripts\construir_instalador.ps1   # reconstruir instalador si cambia el código
```
