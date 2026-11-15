# Matriz de compatibilidad — ScriptLens IA v0.1.0

Fecha: 2026-11-15. Este documento registra solo lo que se probó de verdad. Las casillas «No probado» indican que el entorno no estaba disponible; no deben interpretarse como compatibles ni como incompatibles.

## Entorno disponible

| Dato | Valor |
|---|---|
| Sistema operativo | Windows 11 Pro 25H2, compilación 26200 |
| Arquitectura | x64 (64 bits) |
| Procesador | Intel Core i5-10300H, 4 núcleos / 8 hilos |
| Memoria | 31,8 GB |
| Gráficos | Intel UHD Graphics + NVIDIA GeForce GTX 1650 |
| Pantalla | 1920 × 1080 al 125 % (1536 × 864 lógicos) |
| Sesión | Usuario sin elevación de privilegios (token no administrativo) |
| Carpetas | Documentos redirigida a OneDrive («OneDrive - unicesar.edu.co\Documentos») |
| Ollama | 0.40.16 con `qwen3:4b-instruct` |
| Máquinas virtuales | No disponibles: Windows Sandbox e Hyper-V no están habilitados y habilitarlos requiere administrador |

## Matriz

[[RESULTADOS]]

## Procedimiento

1. Construcción con `.\scripts\construir_instalador.ps1` (PyInstaller + Tauri + NSIS) y cálculo del SHA-256.
2. Prueba de humo del motor empaquetado (`scriptlens-backend.exe`) arrancado como lo hace Tauri: salida estándar redirigida a una tubería, ventana oculta (`CREATE_NO_WINDOW`) y `PATH` reducido a `%SystemRoot%\System32;%SystemRoot%`, sin `PYTHONPATH`, `PYTHONHOME` ni `VIRTUAL_ENV`. Se comprobaron la línea de arranque, el rechazo sin token (HTTP 401), las 15 rutas que usa la interfaz, la auditoría de seguridad, el guardado de un diagnóstico y la generación de informes PDF y HTML.
3. Instalación silenciosa por usuario (`/S`) desde la sesión sin elevación, apertura desde el acceso del menú Inicio, comprobación de que el motor instalado responde, cierre, ausencia de procesos huérfanos, desinstalación silenciosa y comprobación de restos.
4. Recorrido de las pantallas de la aplicación instalada con capturas reales.
5. Diez preguntas de referencia al asistente con Ollama activo y con «Usar IA local» desactivado.

## Limitaciones de la matriz

- Solo se dispuso de un equipo físico con Windows 11. Windows 10, equipos con 4 GB de RAM y otras escalas de pantalla no se probaron.
- No se pudo verificar un equipo «limpio» sin Python, Node.js ni Rust. Se aproximó ejecutando el motor empaquetado con un entorno mínimo: no depende de esas herramientas porque PyInstaller incluye el intérprete y las bibliotecas, y el contenedor Tauri es un ejecutable nativo.
- No se desconectó la red del equipo (sería una modificación de la configuración del sistema). El funcionamiento sin conexión se apoya en el diseño: la API solo escucha en 127.0.0.1, Ollama es local y la única consulta externa es «Buscar actualizaciones», a petición del usuario.
- El escenario «sin Ollama» se comprobó con pruebas automáticas (Ollama inalcanzable) y desactivando «Usar IA local»; no se desinstaló Ollama del equipo.
