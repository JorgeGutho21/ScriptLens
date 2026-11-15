# Estado del desarrollo — ScriptLens IA

Última actualización: 2026-11-14 · Rama: `feat/desarrollo-integral` · Último commit: ver `git log -1` y [bitácora](desarrollo/bitacora.md).

## Fase completada: 1 — Arquitectura, sistema de diseño y monitoreo real

### Hecho y comprobado
- Motor Python (`backend/`): muestreo real de CPU/núcleos/RAM/paginación/disco/red, información del equipo, diagnóstico de consumo sostenido, ranking de procesos y consumo sostenido por proceso, lectura nativa de procesos con `NtQuerySystemInformation`.
- API local autenticada por token (solo lectura).
- Interfaz React: panel general con datos reales, navegación, barra superior con estado, pie con autoría, Ajustes, Acerca de, asistente de primera ejecución, glosario.
- Contenedor Tauri 2 que arranca y detiene el motor.
- Iconos de Windows generados desde `assets/branding/scriptlens-icon.svg`.
- Pruebas: 24 pruebas de pytest aprobadas (ver bitácora). Compilación de la interfaz sin errores de tipos.

### Pendiente / no verificado aún
- Empaquetar el motor Python como `scriptlens-backend.exe` (PyInstaller) e incluirlo en el instalador NSIS.
- Instalador verificado en Windows y publicación en Releases (requiere autorización del autor).
- Archivo `ENTREGA_FINAL_JORGE_GUTIERREZ.zip`: no se encontró en el equipo. El analizador de scripts se reconstruirá con la descripción del proyecto original y se ajustará cuando el autor indique la ruta del archivo.
- Verificar la grafía oficial del nombre del docente (Oswaldo Rueda Carrión) antes de los documentos académicos.

## Próximas fases

| Fase | Objetivo | Criterio de aceptación |
|---|---|---|
| 2 | Administrador de procesos: tabla con búsqueda/filtros, árbol padre-hijo, ruta, firma digital (Authenticode), editor, explicaciones | Árbol coincide con `ppid` real; firma verificada con WinVerifyTrust; pruebas con procesos que terminan |
| 3 | Persistencia SQLite: diagnósticos guardados, historial, borrado; "Comparar mi PC" | Guardar/comparar/eliminar diagnósticos; pruebas de migración |
| 4 | Auditoría y Centro de seguridad: Defender (`Get-MpComputerStatus`, `Get-MpThreatDetection`), firewall, inicio automático, tareas programadas, servicios, eventos | Lectura sin administrador cuando sea posible; estados del §12 |
| 5 | Analizador de scripts: reglas, MITRE ATT&CK, TF-IDF + n-gramas + regresión logística balanceada, explicación por línea | Métricas de evaluación documentadas; nunca ejecuta el script |
| 6 | Acciones supervisadas: cerrar/finalizar procesos no protegidos, inicio automático, WinGet, vista previa de temporales, auditoría | Confirmación explícita, revalidación de identidad, registro |
| 7 | Asistente IA local: Ollama + Qwen3 4B con herramientas de solo lectura, defensa ante inyección de instrucciones | Responde las preguntas obligatorias con datos reales; funciona sin Ollama |
| 8 | Informes PDF/HTML con marca de agua | Exportación verificada |
| 9 | Empaquetado, instalador NSIS, SHA-256, verificación de actualizaciones | Instalador probado en Windows |
| 10 | Documentación técnica, informe ExpoSoftware (APA 7), manual de usuario, material de exposición, PR | Documentos .docx/.pdf generados con capturas reales |

## Cómo continuar

En **PowerShell**, desde `C:\Users\Usuario\Documents\ScriptLens`:

```powershell
git switch feat/desarrollo-integral
.\.venv\Scripts\python -m pytest
. .\scripts\msvc-env.ps1   # solo si cargo no encuentra link.exe
npm run dev
```
