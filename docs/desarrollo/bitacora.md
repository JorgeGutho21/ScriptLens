# Bitácora de desarrollo

## Fase 0 — Inicialización · 2026-11-14

- **Objetivo:** preparar el repositorio vacío `JorgeGutho21/ScriptLens`.
- **Acciones:** inspección remota (`gh repo view`: repositorio público y vacío); clonación en `Documents\ScriptLens`; identidad Git local `Jorge Gutiérrez <…+JorgeGutho21@users.noreply.github.com>`; rama `main` con README inicial y publicación; creación de `feat/desarrollo-integral`.
- **Commit:** `ae3af68` Inicializar el repositorio de ScriptLens IA.

## Fase 1 — Arquitectura, sistema de diseño y monitoreo real · 2026-11-14

| Campo | Detalle |
|---|---|
| Objetivo | Motor de monitoreo real, panel principal profesional, contenedor de escritorio, documentación base |
| Archivos | `backend/**`, `tests/backend/**`, `frontend/**`, `src-tauri/**`, `assets/branding/**`, `scripts/**`, `docs/**`, archivos raíz |
| Motivo | Prioridad del proyecto: experiencia visual y monitoreo real desde el inicio |
| Pruebas | `.venv\Scripts\python -m pytest` → **26 aprobadas**; `npm run build` (tipos + Vite) sin errores; `cargo build` correcto; ejecución real de la aplicación con captura `docs/capturas/01_panel_general.png` |
| Resultado | Panel con datos reales del equipo (CPU, núcleos, RAM, disco, red, tiempo encendido, procesos); consumo del motor medido: ~77 MB de RAM y ~0 % de CPU |

### Errores encontrados y soluciones

| # | Error | Causa | Solución |
|---|---|---|---|
| 1 | Lectura de procesos tardaba 3,4 s por pasada | `ppid()`, `status()` y `num_threads()` de psutil consultan la lista completa del sistema por cada proceso en Windows | Lectura nativa con `NtQuerySystemInformation` en una llamada (< 0,05 s); prueba cruzada contra psutil |
| 2 | `link.exe not found` al compilar Rust | Build Tools instaladas pero instancia no registrada en `vswhere` | `scripts/msvc-env.ps1` |
| 3 | "Motor desconectado", almacenamiento y tiempo encendido vacíos en la app real | El motor anunciaba `ready` antes de `listen()`; la primera consulta fallaba y la siguiente era a los 30 s | `sock.listen()` antes de anunciar; reintento rápido tras error; prueba `test_ready_line_and_immediate_connection` |
| 4 | Motor huérfano tras cerrar la aplicación | El `python.exe` del entorno virtual es un lanzador que crea otro proceso | El motor vigila `SCRIPTLENS_PARENT_PID` y se cierra solo; prueba `test_backend_exits_when_parent_disappears`; verificado con cierre forzado real (0 huérfanos) |
| 5 | Etiqueta "100" recortada en el gráfico y "Promedio 1 min" duplicado | Margen superior nulo; etiqueta de ventana larga | Margen superior y etiqueta "Promedio de la sesión" |

### Commits

| Hash | Mensaje |
|---|---|
| `5e129dd` | Implementar el motor de monitoreo real del sistema |
| `6267e26` | Diseñar el panel principal y el sistema de diseño de la interfaz |
| `63b96c2` | Configurar el contenedor de escritorio Tauri y la identidad gráfica |
| `ed90d66` | Documentar la arquitectura, la investigación de repositorios y la integración continua |
