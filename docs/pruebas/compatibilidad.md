# Matriz de compatibilidad — ScriptLens IA v0.1.0

Fecha: 2026-11-15. Este documento registra solo lo que se probó de verdad. Las casillas «No probado» indican que el entorno no estaba disponible; no deben interpretarse como compatibles ni como incompatibles.

La versión 0.1.1 solo cambia la identidad gráfica del instalador y el número de versión; el código del motor y de la interfaz es el mismo que se probó en 0.1.0. Sobre 0.1.1 se repitieron la actualización desde 0.1.0, el arranque del motor y las pruebas automatizadas.

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

| Entorno | Estado | Evidencia y resultado |
|---|---|---|
| Windows 11 Pro 25H2 x64, 31,8 GB, sesión sin elevación | **Probado: aprobado** | Instalación silenciosa por usuario 17,7–18,3 s, código 0; apertura desde el menú Inicio; motor escuchando solo en 127.0.0.1 en 10–12 s (2,3 s con el motor ya en caché); lectura real de CPU, RAM, disco, red y 365 procesos; todos los módulos abiertos; informe PDF guardado en la carpeta Documentos real (redirigida a OneDrive); cierre normal sin procesos en 1 s; cierre forzado: motor terminado en 1,6 s; segunda apertura: 1 aplicación y 1 motor; desinstalación limpia conservando historial e informes; reinstalación correcta |
| Equipo sin Python, Node.js ni Rust en el PATH | **Aproximado** | Motor empaquetado iniciado con `PATH=%SystemRoot%\System32;%SystemRoot%` y sin variables de Python: línea de arranque en 3,2–3,3 s, 15 de 15 rutas de la interfaz respondidas, auditoría, diagnóstico e informes PDF/HTML generados. No es un equipo limpio: las herramientas siguen instaladas en el disco |
| Usuario estándar sin privilegios administrativos | **Probado (sesión sin elevación)** | Toda la prueba se hizo con un token no administrativo (`IsInRole(Administrator) = False`); el instalador es por usuario y no pidió elevación. No se probó una cuenta del grupo «Usuarios» sin pertenencia a Administradores |
| Con Ollama 0.40.16 y `qwen3:4b-instruct` | **Probado: aprobado** | Diez preguntas de referencia respondidas con herramientas de datos medidos; respuestas de 10–65 s; cifras verificadas; la aplicación instalada respondió «¿Qué significa esta alerta?» con los dos hallazgos reales |
| Sin Ollama (modo sin IA) | **Probado: aprobado** | «Usar IA local» desactivado en la aplicación instalada: respuesta inmediata con plantillas y los mismos datos; pruebas automáticas con Ollama inalcanzable |
| Carpetas de usuario redirigidas a OneDrive | **Probado: aprobado tras corrección** | Los informes se guardaban fuera de la carpeta Documentos visible; corregido con `SHGetKnownFolderPath` y verificado en la aplicación instalada |
| Pantalla 1920 × 1080 al 125 % | **Probado** | Ventana predeterminada 1360 × 860 y mínima 980 × 640; en 1024 px de ancho la tabla de procesos cabe sin desplazamiento horizontal |
| Windows 10 de 64 bits | No probado | Sin equipo ni máquina virtual disponibles |
| Equipo con 4 GB de RAM | No probado | Memoria medida de la aplicación instalada tras un minuto: contenedor Tauri 28 MB, motor 163 MB (conjunto de trabajo; 581 MB de memoria privada comprometida por scikit-learn y NumPy) y WebView2 485 MB en 6 procesos (270 MB privados). Con 4 GB el sistema puede necesitar paginar; no se verificó |
| Otras escalas (100 %, 150 %, 4K) | No probado | — |
| Sin conexión a Internet tras instalar | No probado directamente | El diseño no depende de la red (ver limitaciones) |
| Windows de 32 bits, ARM64, macOS, Linux | No compatible | El instalador es x64 y usa API de Windows |

## Casos críticos del instalador final

| # | Caso | Resultado |
|---|---|---|
| 1 | Generación del ejecutable y del motor empaquetado | Aprobado |
| 2 | Generación del instalador NSIS y su SHA-256 | Aprobado |
| 3 | Instalación desde una sesión sin elevación | Aprobado |
| 4 | Apertura desde el menú Inicio | Aprobado |
| 5 | Inicio del motor empaquetado | Aprobado |
| 6 | Comunicación entre Tauri y el motor (P1) | Aprobado: panel con datos en vivo |
| 7 | Lectura real de CPU y RAM | Aprobado |
| 8 | Listado de procesos | Aprobado |
| 9 | Apertura de todos los módulos | Aprobado |
| 10 | Funcionamiento con y sin Ollama | Aprobado |
| 11 | Exportación de informes | Aprobado |
| 12 | Cierre correcto | Aprobado |
| 13 | Ausencia de procesos huérfanos (cierre normal y forzado) | Aprobado |
| 14 | Desinstalación | Aprobado |
| 15 | Ausencia de errores críticos | Aprobado en el entorno probado |

## Problemas encontrados durante estas pruebas

| Problema | Solución | Commit |
|---|---|---|
| Informes fuera de la carpeta Documentos visible con OneDrive | `SHGetKnownFolderPath`; protección de carpetas reales en la limpieza | `451f19b` |
| Acerca de y README indicaban una carpeta de datos incorrecta | Acerca de muestra las rutas que informa el motor | `5ff1ad8` |
| Diálogo de confirmación descentrado y fondo parcial | Diálogos en un portal sobre `<body>` | `4e564a4` |
| Sin indicación mientras se prepara una limpieza (≈ 8 s) | Mensaje «Preparando el resumen de la acción…» | `9f5087c` |
| Registro de acciones con «midiendo…» permanente | «—» o «sin medición» | `9f5087c` |
| Prueba CP6 por encima de 10 s con el equipo saturado | Se repitió con menos carga (8,5 s); se documenta la dependencia de la carga | — |

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
