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

## Auditoría previa a la fase 2 · 2026-11-14

| Campo | Detalle |
|---|---|
| Objetivo | Corregir problemas recuperables antes de continuar |
| Resultado | Rust 1.100, cargo y MSVC 14.44 operativos con `scripts/msvc-env.ps1`; acciones de CI actualizadas a versiones con Node.js 24 (`efc02c7`, CI en verde); ZIP académico localizado en Descargas y analizado en una carpeta aislada (guía 03B usada como fuente) |
| Observación | En los documentos del ZIP el docente figura como «Oswaldo Rueda Carreño» |

## Fase 2 — Administrador de procesos · 2026-11-14

| Campo | Detalle |
|---|---|
| Archivos | `backend/processes/{analysis,knowledge,signatures,winapi,routes}.py`, `backend/core/{engine,winps}.py`, `frontend/src/pages/Processes.tsx`, pruebas `test_process_manager.py` |
| Pruebas | 41 pruebas aprobadas al cierre de la fase; verificación con datos reales: 331 procesos con firma válida, 7 sin firma |
| Errores y soluciones | (1) `Get-AuthenticodeSignature` no cargaba: Windows PowerShell 5.1 heredaba `PSModulePath` de PowerShell 7 → se elimina esa variable al invocarlo. (2) Rutas ficticias «Registry»/«MemCompression» y el proceso inactivo marcado como consumo elevado → se descartan |
| Commits | `3108cbd`, `f721be0` |

## Fase 3 — Historial y comparación · 2026-11-14

| Campo | Detalle |
|---|---|
| Archivos | `backend/storage/*`, `frontend/src/pages/{Compare,Privacy}.tsx`, `frontend/src/components/Confirm.tsx`, `tests/backend/{conftest,test_history}.py` |
| Pruebas | 46 aprobadas; prueba en navegador con datos reales (advertencia de menos de 20 s de mediciones) |
| Error y solución | `Settings.data_dir` capturaba la función por defecto al definir la clase y las pruebas escribían en la base real → fábrica diferida y carpeta aislada para pruebas |
| Commits | `47519d0`, `1ec4a2c` |

## Fase 4 — Auditoría y seguridad · 2026-11-14

| Campo | Detalle |
|---|---|
| Archivos | `backend/security/*`, `frontend/src/pages/{Security,StartupActions}.tsx`, `test_security.py` |
| Pruebas | 57 aprobadas; recolección real sin administrador en 3,4–6,4 s (Defender, firewall 3/3, 180 tareas, 314 servicios, 83 eventos, 13 entradas de inicio) |
| Hallazgos reales | Entrada de inicio «SoyMicrosoft» → `C:\taller1\gestion.bat` (archivo inexistente) y tarea «EcoAccess P3 - vigilante del bot»: ambas «requieren revisión», ninguna calificada como malware |
| Commits | `b4b93ff`, `9f34330` |

## Fase 5 — Analizador de scripts · 2026-11-14

| Campo | Detalle |
|---|---|
| Archivos | `backend/scripts/*`, `scripts/extraer_attack.py`, `tests/fixtures/scripts_reales/*`, `docs/pruebas/evaluacion_clasificador.md`, `frontend/src/pages/Scripts.tsx` |
| Pruebas | 14 pruebas (incluye CP1–CP6 de la guía 03B y la verificación estática de que el analizador nunca ejecuta procesos) |
| Hallazgos | ATT&CK 20.1 revocó T1562.001, T1070.001 y T1562.004 (reemplazos T1685, T1685.005, T1686, comprobados en el paquete STIX). La regla P01 marcaba la lectura de la clave Run como persistencia: en validación cruzada el baseline tenía F1 macro 0,732 y 43,3 % de falsos positivos en «consulta»; tras la corrección por contexto, 0 % |
| Resultados finales | Validación cruzada (180 scripts sintéticos): baseline 1,000 (circular), modelo 0,955, híbrida 0,966. Conjunto realista independiente (18 scripts): baseline 1,000, modelo 0,886 (recall «sensible» 0,667), híbrida 1,000 |
| Commits | `b82ab66`, `a9c9cb4`, `34fd86f` |

## Fase 6 — Acciones supervisadas · 2026-11-14

| Campo | Detalle |
|---|---|
| Archivos | `backend/actions/*`, `frontend/src/lib/supervised.tsx`, `frontend/src/pages/{ProcessActions,StartupActions,Optimize}.tsx`, `test_actions.py` |
| Pruebas | 8 pruebas: token de un solo uso y caducidad, revalidación de identidad, procesos protegidos y propios, inicio automático reversible en clave aislada, limpieza que no toca archivos fuera de `%TEMP%` |
| Ajuste | Se excluyó `explorer.exe` de las recomendaciones de cierre |
| Commits | `6c26621`, `4368a1a` |

## Fase 7 — Asistente IA local · 2026-11-14

| Campo | Detalle |
|---|---|
| Archivos | `backend/assistant/*`, `frontend/src/pages/Assistant.tsx`, `test_assistant.py` |
| Pruebas | 24 pruebas: 15 preguntas obligatorias enrutadas, saneamiento, verificación de cifras, sin acceso a acciones, funcionamiento sin Ollama y prueba con el modelo real (18,4 s, cifras verificadas) |
| Hallazgo | `qwen3:4b` es la variante de razonamiento: 2 940 tokens y 256 s para una frase, `think:false` y `/no_think` no lo desactivan → se adoptó `qwen3:4b-instruct` |
| Commits | `bc7a547`, `f5e0669` |

## Fase 8 — Informes · 2026-11-14

| Campo | Detalle |
|---|---|
| Archivos | `backend/reports/*`, `frontend/src/pages/Reports.tsx`, `test_reports.py` |
| Pruebas | 4 pruebas (identidad, secciones, marca de agua, escape de HTML, PDF válido con autor en metadatos, rutas fuera de la carpeta rechazadas) |
| Commits | `7d8f06a`, `85c6c5a`, `b45a00a` (elemento 3D y actualizaciones) |

## Fase 9 — Instalador y distribución · 2026-11-14

| Campo | Detalle |
|---|---|
| Archivos | `scripts/{scriptlens_backend,construir_instalador}.py/.ps1`, `src-tauri/*`, `.github/workflows/instalador.yml` |
| Pruebas | Motor empaquetado probado sin Python (159 MB, arranque 9 s); instalación silenciosa por usuario en 8,3 s; desinstalación limpia; reinstalación; instancia única; motor sin huérfanos tras cierre forzado; recorrido completo de la app instalada con 20 capturas |
| Errores y soluciones | Pantalla en blanco del asistente (`scrollIntoView` devuelve Promise en WebView2) → efectos sin valor de retorno y límite de errores; interruptor mal dibujado; segunda instancia → `tauri-plugin-single-instance`; informes dentro de la carpeta del repositorio → `Documentos\ScriptLens IA\Informes`; análisis de 1 MB 10,4 s → 3,4 s con memorización |
| Resultado | Instalador NSIS de 49,26 MB con SHA-256 |
| Commits | `aab7b22`, `04f9709`, `ae0504a`, `4c2e76a`, `94884bf`, `b4b0437` |

## Fase 10 — Documentación y entrega · 2026-11-15

| Campo | Detalle |
|---|---|
| Archivos | `README.md`, `CHANGELOG.md`, `THIRD_PARTY_NOTICES.md`, `docs/PRIVACIDAD.md`, `docs/instalacion/INSTALACION.md`, `docs/release/v0.1.0.md`, `docs/academico/*`, `docs/{desarrollo,expo_software,manual_usuario}/*`, `scripts/demo_consumo.py` |
| Pruebas | 110 pruebas aprobadas, compilación de interfaz y `cargo check` correctos, enlaces internos verificados, DOI de las referencias verificados en Crossref y arXiv, licencias de dependencias revisadas |
| Errores y soluciones | Listas numeradas que continuaban entre secciones en los DOCX → numeración explícita; referencias que heredaban la sangría francesa en los anexos → se reinicia en el siguiente encabezado |
| Observación | No se autorizó controlar el instalador gráfico: solo se capturó su primera pantalla |
| Commits | `fce51c1`, `fac9596`, `2ff98d3` y el commit de cierre |

## Fase 11 — Revisión de cierre, defectos P1 e instalación pública · 2026-11-15

| Campo | Detalle |
|---|---|
| Origen | Dos observaciones P1 de la revisión automática del PR #1 y la orden de finalización del autor |
| P1 A — motor empaquetado | PyInstaller en modo ventana deja `sys.stdout = None` y el puerto no llegaba a Tauri. El autor cambió el empaquetado a `--console` (`109b712`); se añadió una defensa que escribe en el descriptor heredado si falta `sys.stdout` (`0794f85`). Verificado con el motor empaquetado (PATH mínimo, línea de arranque en 3,2 s, 15/15 rutas) y con la aplicación instalada (panel con datos en vivo) |
| P1 B — limpieza de temporales | `TEMP` vacía se resolvía como el directorio de trabajo. Validación en vista previa y ejecución (`b2e4ce8`, `151770c`, `79532b2`); además se rechazan el perfil, sus carpetas superiores, las carpetas personales reales (OneDrive) y Windows, y no se entra en uniones NTFS (`8dc8706`, `451f19b`). Pruebas con carpetas aisladas, una unión hacia un documento externo y token inexistente |
| Otros defectos | Informes fuera de Documentos visible con OneDrive; ruta de datos incorrecta en Acerca de y README; enrutado del asistente («esta alerta», «requiere investigación», ranking de CPU nulo al iniciar); diálogos descentrados por `transform` en el ancestro; sin indicación al preparar una limpieza; «midiendo…» permanente en el registro |
| Interfaz | Acerca de con identidad oficial, información técnica y rutas reales; tabla de procesos adaptada a 1024 px; «Comprobar de nuevo» para Ollama; imágenes de marca en el instalador NSIS |
| Marcas | Sin referencias promocionales en código, documentos, metadatos ni imágenes; se corrigió el autor de los metadatos de la presentación (plantilla de python-pptx). Se conservan el historial de commits y la lista de colaboradores de GitHub |
| Pruebas | 135 pruebas en 14 archivos; la prueba de rendimiento CP6 falló una vez con el equipo saturado (17,5 s) y se aprobó al repetirla (8,5 s). Diez preguntas de referencia con y sin Ollama. Ciclo completo del instalador final: actualización, apertura, motor solo en 127.0.0.1, instancia única, cierre forzado sin huérfanos, desinstalación conservando datos y reinstalación |
| Instalador final | `ScriptLens-IA_0.1.0_x64-setup.exe`, 51 678 985 bytes, SHA-256 `111397CF7D8164943D79F99488F3B868603A4CA32053D116D8B522AC37B6D13A` |
| Documentos | README reescrito, *Guía de instalación* (DOCX/PDF, 13 págs.), matriz de compatibilidad, documentación técnica (50 págs.), informe ExpoSoftware (20 págs.), manual (20 págs.), presentación |
| Pendiente | Fusionar el PR y publicar la release (autorización del autor); capturas de las pantallas 2–6 del instalador (no se autorizó controlarlo; existe `scripts/capturar-instalador.ps1`); pruebas en Windows 10 y equipos de 4 GB |
| Commits | `109b712` … `4e564a4` (21 commits en esta fase) |

## Fase 12 — Publicación de v0.1.0 · 2026-11-15

| Campo | Detalle |
|---|---|
| Fusión | El autor fusionó el PR #1 en `main` (squash `d376dbb`); árbol idéntico a `fdd63c5` |
| Release | `v0.1.0` sobre `d376dbb`, *Latest*; recursos `ScriptLens-IA_0.1.0_x64-setup.exe` (51 678 985 bytes) y `.sha256` (101 bytes); descarga pública verificada con la misma huella `111397CF…B6D13A`; la API `releases/latest` devuelve `v0.1.0` |
| Corrección | Las notas indicaban 100 bytes para el `.sha256`; son 101 (salto de línea final). Corregido en el repositorio y en la release |
| Guía | Capturas reales de la página del repositorio, de la versión y de Assets (navegador sin sesión); guía regenerada (14 págs., 7 figuras) |
