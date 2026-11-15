# Investigación técnica de repositorios de referencia

Fecha de consulta: 2026-11-14. Licencia, lenguaje y actividad verificados con la API de GitHub (`gh api repos/<owner>/<repo>`).

## Matriz comparativa

| Proyecto | Lenguaje | Licencia | Funciones principales | Arquitectura | Reutilizable en ScriptLens | Dificultad de integración | Decisión |
|---|---|---|---|---|---|---|---|
| [giampaolo/psutil](https://github.com/giampaolo/psutil) | Python + C | BSD-3-Clause | CPU, memoria, discos, red, procesos multiplataforma | Extensión C por plataforma + API Python | CPU/RAM/disco/red globales, procesos en ruta portable | Baja (dependencia pip) | **Dependencia directa** |
| [winsiderss/systeminformer](https://github.com/winsiderss/systeminformer) | C | MIT | Administrador de procesos avanzado, árbol, firmas, handles, servicios | Aplicación nativa + controlador opcional | Concepto: enumerar todos los procesos con `NtQuerySystemInformation(SystemProcessInformation)` en una sola llamada | Alta para integrar entero; baja para el concepto | **Concepto adoptado**, implementación propia en ctypes (`backend/processes/ntquery.py`) |
| [nicolargo/glances](https://github.com/nicolargo/glances) | Python | LGPL-3.0 | Monitor de sistema con plugins, API REST, umbrales | Núcleo + plugins por métrica sobre psutil | Concepto: umbrales por métrica (careful/warning/critical) y promedio en ventana | Media | **Concepto adoptado** (umbrales y ventanas en `monitoring/diagnosis.py`); sin código copiado |
| [osquery/osquery](https://github.com/osquery/osquery) | C++ | Apache-2.0 / GPL-2.0 | Consultas SQL sobre el sistema (procesos, servicios, inicio, tareas) | Tablas virtuales SQLite + demonio | Concepto: organizar la auditoría como "tablas" de solo lectura consultables | Alta (binario de ~30 MB y servicio) | **Concepto** para el módulo de auditoría (fase 4); no se distribuye osquery |
| [microsoft/winget-cli](https://github.com/microsoft/winget-cli) | C++ | MIT | Gestor oficial de paquetes de Windows | CLI + COM API | Listar y desinstalar programas mediante el mecanismo oficial | Baja (se invoca `winget` ya instalado) | **Uso de la herramienta** del sistema en acciones supervisadas (fase 6) |
| [PowerShell/PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer) | C# | MIT | Reglas estáticas para PowerShell (AST) | Motor de reglas sobre el AST de PowerShell | Catálogo de reglas de riesgo (Invoke-Expression, credenciales en texto plano) | Media (requiere PowerShell) | **Referencia de reglas** para el analizador de scripts (fase 5) |
| [KyootyBella/PowerDetect](https://github.com/KyootyBella/PowerDetect) | Python | MIT | Detección de PowerShell malicioso | Paquete Python + web | Ideas de características (entropía, ofuscación) | Media | **Referencia** de características para el clasificador |
| [Arjunren/MaliciousPowerShellDetector](https://github.com/Arjunren/MaliciousPowerShellDetector) | Python | MIT | Clasificación ML de scripts PowerShell | Notebooks + modelos + API | Flujo TF-IDF + modelo lineal, métricas de evaluación | Media | **Referencia metodológica**; se conserva la regresión logística balanceada del proyecto original |
| [mitre-attack/attack-stix-data](https://github.com/mitre-attack/attack-stix-data) | JSON (STIX 2.1) | Licencia de uso de ATT&CK (MITRE) | Datos oficiales de técnicas ATT&CK | Paquetes STIX | Identificadores y nombres de técnicas para etiquetar hallazgos | Baja | **Datos**: subconjunto con atribución en THIRD_PARTY_NOTICES (fase 5) |

## Bibliotecas de plataforma

| Componente | Uso | Licencia |
|---|---|---|
| Tauri 2 | Contenedor de escritorio, instalador NSIS | MIT / Apache-2.0 |
| React 19 + TypeScript | Interfaz | MIT / Apache-2.0 |
| Tailwind CSS 4 | Sistema de estilos basado en variables | MIT |
| lucide-react | Iconografía consistente | ISC |
| FastAPI + Uvicorn | API local en 127.0.0.1 | MIT / BSD-3-Clause |
| Ollama | Ejecución local del modelo Qwen3 (fase 7) | MIT |

## Hallazgo medido que motivó la adopción del concepto de System Informer

Leyendo procesos uno a uno con psutil en este equipo (346 procesos):

| Método | Tiempo por pasada |
|---|---|
| psutil, `as_dict` con `ppid`, `status`, `num_threads` | 3,4 s |
| psutil con `oneshot()` y atributos mínimos | 0,8 s |
| `NtQuerySystemInformation` en una sola llamada (ntquery.py) | < 0,05 s |

Con muestreo cada 2 s, la primera opción ocuparía más de un núcleo de forma permanente; la implementación nativa elimina ese costo y no sufre `AccessDenied` en procesos protegidos. La prueba `tests/backend/test_ntquery.py` valida los datos contra psutil.

## Alternativas descartadas

- Integrar osquery completo: añade un servicio permanente y un binario grande; contradice el requisito de no instalar vigilancia permanente.
- Java o MySQL: no aportan nada que SQLite y Python no cubran.
- Librerías de gráficos pesadas: se usan gráficos SVG propios para mantener bajo el consumo de la propia aplicación.
