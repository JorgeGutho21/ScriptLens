[[TOC]]

# Resumen

ScriptLens IA es una aplicación de escritorio para Windows que diagnostica el rendimiento y la seguridad del equipo, analiza scripts BAT, CMD y PowerShell sin ejecutarlos y explica sus resultados en lenguaje sencillo mediante un asistente de inteligencia artificial que funciona localmente. Se construyó con una interfaz Tauri 2, React y TypeScript, y con un motor de análisis en Python que usa psutil, la API nativa de Windows, SQLite, scikit-learn y Ollama. El proyecto conserva y amplía la propuesta académica previa del autor: un catálogo de 24 reglas asociadas a MITRE ATT&CK y un clasificador de regresión logística con clases balanceadas sobre rasgos TF-IDF de n-gramas de caracteres. La evaluación reproducible muestra, en validación cruzada sobre 180 scripts sintéticos, un F1 macro de 0,955 para el modelo y de 0,966 para la política híbrida; en un conjunto independiente de 18 scripts realistas, la política híbrida alcanzó un recall de 1,0 en la clase sensible, mientras que el modelo por sí solo obtuvo 0,667. El asistente usa Qwen3 4B Instruct mediante herramientas internas de solo lectura y verifica cada cifra de su respuesta contra los datos medidos. La aplicación se distribuye como un instalador NSIS de 49,3 MB que no requiere privilegios de administrador ni la instalación de Python, Node.js o Rust; se verificó su instalación, desinstalación, reinstalación y funcionamiento en Windows 11. El desarrollo se registró en commits progresivos y 135 pruebas automatizadas.

*Palabras clave:* diagnóstico de Windows, análisis estático, regresión logística, MITRE ATT&CK, inteligencia artificial local, Tauri.

[[SALTO]]

# Introducción

Los usuarios de computadores personales suelen percibir que su equipo «está lento» o que «algo raro está pasando», pero carecen de herramientas que expliquen la situación en términos comprensibles. El Administrador de tareas de Windows muestra cifras sin interpretarlas, y las herramientas avanzadas, como System Informer, están orientadas a especialistas. Al mismo tiempo, en los cursos de Sistemas Operativos los estudiantes intercambian scripts que escriben en el Registro, crean tareas programadas o borran carpetas, y quien los ejecuta asume esos efectos sin conocerlos.

Este documento describe, de forma reproducible, la construcción de ScriptLens IA desde cero: la investigación de repositorios de referencia, la selección de tecnologías, la arquitectura, cada módulo implementado, las pruebas ejecutadas, los problemas encontrados y sus correcciones, la compilación del instalador y su distribución. Todos los resultados que se presentan provienen de mediciones y pruebas realizadas en el equipo de desarrollo; donde un resultado no pudo comprobarse, se indica expresamente.

# Planteamiento del problema

Un usuario sin formación técnica no puede responder con facilidad preguntas como «¿por qué mi computador está lento?», «¿qué programa consume más memoria?» o «¿es peligroso este proceso?». La información existe en el sistema operativo, pero está dispersa entre el Administrador de tareas, el Visor de eventos, el Programador de tareas, el Registro y Seguridad de Windows, y su interpretación exige conocimientos especializados. Las respuestas que circulan en Internet tienden a recomendar medidas riesgosas, como finalizar procesos esenciales o desactivar el antivirus.

En el caso de los scripts, el problema es similar: leer un archivo de 150 líneas exige conocer decenas de comandos. Los antivirus no explican qué hace un script benigno pero riesgoso, como uno que borra una carpeta con `rmdir /s /q`, y no están pensados para enseñar.

# Justificación

ScriptLens IA reúne en una sola aplicación la medición, la interpretación y la acción supervisada. Su valor diferencial es triple: explica con evidencia y distingue lo comprobado de lo estimado; integra un analizador de scripts académicamente fundamentado que nunca ejecuta el código analizado; y ofrece un asistente de inteligencia artificial local que no envía datos a Internet y cuyas cifras se verifican automáticamente. Desde el punto de vista académico, aplica contenidos de Sistemas Operativos (procesos, memoria, servicios, Registro, seguridad), de aprendizaje automático (representación de texto, clasificación supervisada, validación) y de ingeniería de software (arquitectura, pruebas, integración continua y distribución).

# Objetivos

## Objetivo general

Desarrollar una aplicación de escritorio para Windows que diagnostique el rendimiento y la seguridad del equipo, analice scripts sin ejecutarlos y explique sus hallazgos mediante un asistente de inteligencia artificial local, con acciones de optimización supervisadas por el usuario.

## Objetivos específicos

1. Medir en tiempo real el procesador, la memoria, el disco, la red y los procesos, y distinguir el consumo sostenido de los picos momentáneos.
2. Construir un administrador de procesos que muestre la ruta, la firma digital, el editor y las relaciones padre-hijo, con explicaciones para principiantes.
3. Auditar en modo de solo lectura Microsoft Defender, el firewall, el inicio automático, las tareas programadas, los servicios y los eventos del sistema.
4. Recuperar y ampliar el analizador de scripts académico con reglas, MITRE ATT&CK y regresión logística balanceada, evaluado de forma reproducible.
5. Integrar un asistente local con Ollama y Qwen3 que responda con datos verificados y sin capacidad de ejecutar acciones.
6. Implementar acciones supervisadas, historial local, comparación de diagnósticos e informes exportables.
7. Distribuir la aplicación mediante un instalador de Windows verificado que no requiera herramientas de desarrollo.

# Alcance

La versión 0.1.0 funciona en Windows 10 (1809 o posterior) y Windows 11 de 64 bits. Incluye monitoreo, procesos, optimización supervisada, seguridad, análisis de scripts, asistente local, comparación, informes y ajustes de accesibilidad. Quedan fuera del alcance: la detección de malware por firmas o comportamiento (función que se delega en Microsoft Defender), la vigilancia permanente en segundo plano, la modificación de configuraciones de seguridad y la firma de código comercial del instalador.

# Antecedentes

El proyecto parte de la entrega académica «ENTREGA_FINAL_JORGE_GUTIERREZ», que contiene tres propuestas de inteligencia artificial del autor para ExpoSoftware 2026. La guía 03B, «ScriptLens IA», define un analizador estático de scripts con un catálogo de 24 patrones en 9 categorías asociados a MITRE ATT&CK, un análisis de flujo y un clasificador de regresión logística balanceada comparado con un baseline de reglas fijas. Esa guía advierte que sus métricas eran metas sin medir. La guía 02B, «BitácoraIA», propone verificar cifra por cifra las explicaciones de un modelo de lenguaje local; ese concepto se incorporó al asistente. La guía 04B, «RecuperaSO IA», aporta la idea de monitorear CPU y RAM con psutil y SQLite.

En la literatura, Hendler et al. (2018) mostraron que la detección de comandos PowerShell maliciosos puede abordarse como un problema de clasificación de texto con representaciones a nivel de caracteres, y Bohannon y Holmes (2017) documentaron técnicas de ofuscación de PowerShell y su detección. MITRE ATT&CK proporciona un vocabulario estándar para nombrar técnicas de adversarios (Strom et al., 2018).

# Marco teórico

## Procesos, memoria y servicios en Windows

Un proceso es un programa en ejecución con su propio espacio de direcciones, hilos e identificadores. Windows asigna a cada proceso un identificador (PID) que puede reutilizarse cuando el proceso termina, por lo que un PID solo identifica a un proceso de forma única junto con su hora de creación (Yosifovich et al., 2017). Los servicios son procesos que inicia el Administrador de control de servicios, normalmente en la sesión 0, sin interfaz visible. La memoria que usa un proceso puede medirse como conjunto de trabajo (*working set*), que incluye páginas compartidas, o como memoria privada confirmada; el Administrador de tareas muestra por defecto el conjunto de trabajo privado (Silberschatz et al., 2018).

## Análisis estático y dinámico

El análisis dinámico ejecuta el programa en un entorno controlado y observa su comportamiento; el estático examina el código sin ejecutarlo. El análisis estático es seguro y rápido, pero no observa lo que el código construye en tiempo de ejecución, como un comando descargado o decodificado.

## Representación de texto y regresión logística

TF-IDF pondera un término según su frecuencia en el documento y su rareza en el corpus (Salton & Buckley, 1988). Los n-gramas de caracteres toleran variaciones de escritura como `REG ADD` y `reg.exe add`. La regresión logística modela la probabilidad de cada clase como una función logística de una combinación lineal de rasgos (Hosmer et al., 2013); el parámetro `class_weight="balanced"` pondera cada clase de forma inversamente proporcional a su frecuencia, una corrección relacionada con el problema de clases desbalanceadas descrito por King y Zeng (2001). Se implementó con scikit-learn (Pedregosa et al., 2011).

## Evaluación de clasificadores

La validación cruzada estratificada de *k* pliegues entrena *k* veces con *k* − 1 particiones y evalúa con la restante, de modo que cada ejemplo se evalúa sin haberse visto en el entrenamiento (Kohavi, 1995). La precisión indica cuántos de los casos predichos como positivos lo eran; el recall, cuántos positivos reales se detectaron; y F1 es su media armónica. En seguridad importa sobre todo el recall de la clase peligrosa. El acuerdo entre etiquetadores se mide con el coeficiente kappa de Cohen (1960).

## Modelos de lenguaje locales y sus riesgos

Los modelos de lenguaje pueden generar contenido plausible pero falso, fenómeno conocido como alucinación (Ji et al., 2023). Cuando se integran con datos externos, también son vulnerables a la inyección indirecta de instrucciones: texto malicioso dentro de los datos que el modelo interpreta como órdenes (Greshake et al., 2023; OWASP Foundation, 2025). Qwen3 es una familia de modelos abiertos que incluye variantes con y sin razonamiento explícito (Qwen Team, 2025); Ollama permite ejecutarlos localmente.

# Metodología

Se siguió un desarrollo incremental por fases, cada una con criterios de aceptación, pruebas automatizadas y commits. En cada fase se comprobó el estado, se implementó la funcionalidad, se ejecutaron las pruebas, se corrigieron los fallos, se documentaron los cambios y se registró el commit en la bitácora. Las funciones de la interfaz se verificaron con el motor real en un navegador de desarrollo y, al final, en la aplicación instalada con el instalador generado. Las métricas del clasificador se obtuvieron con un script de entrenamiento determinista que regenera el informe de evaluación.

Tabla: Fases del desarrollo y criterio de aceptación
| Fase | Objetivo | Criterio de aceptación |
|---|---|---|
| 1 | Arquitectura y monitoreo real | Panel con datos reales y pruebas de unidades |
| 2 | Administrador de procesos | Firmas verificadas, árbol válido con PID reutilizados |
| 3 | Historial y comparación | Guardar, comparar y borrar diagnósticos |
| 4 | Auditoría de seguridad | Lectura sin administrador y hallazgos de ocho puntos |
| 5 | Analizador de scripts | Casos CP1–CP6 de la guía original y evaluación reproducible |
| 6 | Acciones supervisadas | Confirmación, revalidación y auditoría |
| 7 | Asistente local | Preguntas obligatorias con cifras verificadas |
| 8 | Informes | PDF y HTML válidos con marca de agua |
| 9 | Instalador | Instalación, desinstalación y uso probados en Windows |
| 10 | Documentación | Documentos APA 7 y pull request |

# Comparación de repositorios

Se analizaron nueve repositorios de referencia. Su lenguaje, licencia y actividad se verificaron con la API de GitHub el 14 de noviembre de 2026. No se integraron todos: se adoptaron dependencias directas solo cuando eran ligeras y compatibles, y en los demás casos se reutilizaron conceptos con implementaciones propias.

Tabla: Matriz comparativa de repositorios de referencia
| Proyecto | Lenguaje | Licencia | Aporte a ScriptLens | Decisión |
|---|---|---|---|---|
| psutil | Python/C | BSD-3-Clause | Métricas de CPU, RAM, disco, red y servicios | Dependencia directa |
| System Informer | C | MIT | Enumeración de procesos con una sola llamada nativa | Concepto, implementación propia en ctypes |
| Glances | Python | LGPL-3.0 | Umbrales por niveles y promedios en ventana | Concepto |
| osquery | C++ | Apache-2.0 / GPL-2.0 | Auditoría como fuentes de solo lectura | Concepto, sin servicio permanente |
| winget-cli | C++ | MIT | Métodos oficiales de instalación | Referencia |
| PSScriptAnalyzer | C# | MIT | Reglas de riesgo en PowerShell | Referencia para la ampliación del catálogo |
| PowerDetect | Python | MIT | Señales de ofuscación | Referencia |
| MaliciousPowerShellDetector | Python | MIT | TF-IDF y modelo lineal | Referencia metodológica |
| attack-stix-data | JSON STIX | Licencia de ATT&CK | Nombres oficiales de técnicas | Datos (30 técnicas, ATT&CK 20.1) |

La adopción del concepto de System Informer se justificó con una medición: leer los procesos uno a uno con psutil tardaba 3,4 s por pasada (346 procesos) y 0,8 s con lecturas mínimas, mientras que una llamada a `NtQuerySystemInformation` tarda menos de 0,05 s y no sufre denegaciones de acceso.

# Selección de tecnologías

Tabla: Tecnologías seleccionadas y justificación
| Capa | Tecnología | Justificación |
|---|---|---|
| Contenedor de escritorio | Tauri 2 (Rust) | Ejecutable pequeño, usa WebView2 del sistema, instalador NSIS integrado |
| Interfaz | React 19, TypeScript, Tailwind CSS 4 | Componentes tipados y sistema de diseño basado en variables |
| 3D | Three.js | Elemento discreto cargado bajo demanda |
| Motor | Python 3.12, FastAPI, Uvicorn | Ecosistema de análisis de datos y aprendizaje automático |
| Sistema | psutil, ctypes (API de Windows), Windows PowerShell 5.1 | Lectura del sistema sin privilegios |
| Persistencia | SQLite | Base local sin servidor; se descartó MySQL por innecesario |
| Aprendizaje automático | scikit-learn, joblib | Implementación de referencia del pipeline original |
| IA generativa | Ollama, Qwen3 4B Instruct | Ejecución local y privada |
| Informes | reportlab | PDF sin dependencias externas |
| Empaquetado | PyInstaller, NSIS | El usuario no necesita instalar Python |
| Calidad | pytest, oxlint, GitHub Actions | Pruebas y comprobaciones automáticas |

# Arquitectura

La aplicación se compone de dos procesos. El contenedor Tauri muestra la interfaz en WebView2, inicia el motor de análisis como proceso hijo sin consola, lee de su salida estándar una línea con el puerto y un token aleatorio, y entrega esos datos a la interfaz. El motor expone una API HTTP solo en 127.0.0.1, exige el token en cada petición y vigila el PID de la aplicación para cerrarse si esta desaparece. Ningún módulo de la interfaz lee el sistema directamente.

Tabla: Módulos del motor de análisis
| Paquete | Responsabilidad |
|---|---|
| core | Configuración, API, motor de hilos, PowerShell controlado, actualizaciones |
| monitoring | Muestreo global y reglas de consumo sostenido |
| processes | Lectura nativa, rutas, firmas, base de conocimiento, señales y explicaciones |
| storage | SQLite: diagnósticos, comparación, conversaciones, auditoría y ajustes |
| security | Recolección de solo lectura y reglas de auditoría |
| scripts | Analizador estático, modelo, corpus y entrenamiento |
| actions | Acciones supervisadas con confirmación |
| assistant | Enrutador, herramientas de solo lectura, cliente de Ollama y verificación |
| reports | Informes HTML y PDF |

# Diagramas

El flujo de una petición sigue la secuencia: interfaz → API local autenticada → módulo → fuente del sistema (psutil, API nativa, Registro, PowerShell de solo lectura o SQLite) → respuesta JSON. Las acciones que modifican el sistema siguen un flujo distinto de dos pasos: la interfaz pide *preparar*, el motor valida y devuelve un resumen y un token de un solo uso; la interfaz muestra un diálogo de confirmación cuyo botón inicial es «Cancelar»; solo si el usuario confirma se llama a *ejecutar*, el motor revalida la identidad del objetivo y registra la acción. El asistente nunca participa en ese flujo.

```
Usuario ─► Interfaz React ─► API 127.0.0.1 + token ─► Motor Python
                                         │                 ├─ monitoring  (psutil)
Tauri (Rust) ─ inicia/cierra el motor ───┘                 ├─ processes   (NtQuerySystemInformation, Authenticode)
                                                           ├─ security    (Registro, PowerShell solo lectura)
Acción: preparar ─► confirmar (usuario) ─► ejecutar        ├─ scripts     (reglas + regresión logística)
                                                           ├─ assistant   (Ollama local, solo lectura)
                                                           └─ storage     (SQLite)
```

# Diseño de la interfaz

La interfaz se diseñó para personas sin conocimientos técnicos. Incluye un panel lateral fijo, una barra superior con el estado del motor y las cifras actuales, un modo sencillo y uno avanzado, un modo oscuro y uno claro, ajuste del tamaño de texto, opción de reducir animaciones, un glosario contextual en las palabras subrayadas y un asistente de primera ejecución de ocho pasos. El sistema de diseño define tokens de color (azul tecnológico #3B8CFF como acento, grafito y negro), tipografía Segoe UI Variable con cifras tabulares, escala de espaciado de 4 px y estados con icono y texto, nunca solo con color. Los gráficos son SVG propios para no cargar librerías pesadas, y la interfaz deja de consultar el motor cuando la ventana no es visible.

Figura: docs/capturas/02_panel_general.png | Panel general de la aplicación instalada | Captura real tomada el 14 de noviembre de 2026 en el equipo de desarrollo. Los valores corresponden a mediciones de ese momento.

Figura: docs/capturas/16_modo_claro.png | Panel general en modo claro | Mismo equipo y sesión que la figura anterior.

# Estructura del código

Tabla: Estructura del repositorio
| Carpeta | Contenido |
|---|---|
| backend/ | Motor de análisis en Python (4 946 líneas) |
| frontend/ | Interfaz React y TypeScript (3 733 líneas) |
| src-tauri/ | Contenedor Rust, configuración e iconos |
| tests/backend/ | 135 pruebas de pytest y conjunto realista de scripts |
| scripts/ | Construcción del instalador, entorno MSVC, capturas, extracción de ATT&CK |
| docs/ | Arquitectura, desarrollo, instalación, pruebas, capturas y documentos académicos |
| .github/workflows/ | Integración continua e instalador |

# Preparación del entorno

El equipo de desarrollo fue un portátil con Windows 11 Pro 10.0.26200, 8 procesadores lógicos y 32 GB de RAM. Al iniciar contaba con Git, GitHub CLI, Node.js 26 y Ollama, pero no con Python, Rust ni el compilador de C++. Las herramientas se instalaron con WinGet, desde **PowerShell**, con autorización del autor.

```
winget install --id Python.Python.3.12 -e --scope user
winget install --id Rustlang.Rustup -e
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
rustup default stable
```

# Instalación de herramientas

Después de clonar el repositorio, en **PowerShell** desde su raíz, se creó el entorno de Python y se instalaron las dependencias del motor y de la interfaz:

```
py -3.12 -m venv .venv
.\.venv\Scripts\pip install -r backend\requirements-dev.txt pyinstaller
npm install
npm --prefix frontend install
```

Durante esta etapa aparecieron dos problemas. El comando `python` abría la Microsoft Store porque la sesión no había recargado la variable PATH; se resolvió usando la ruta absoluta del intérprete. El compilador de Rust no encontraba `link.exe`, porque el instalador de Visual Studio no registró la instancia; se creó `scripts/msvc-env.ps1`, que configura `PATH`, `LIB` e `INCLUDE` para la sesión.

# Implementación del frontend

La interfaz se organiza en páginas (Panel, Procesos, Optimizar, Seguridad, Analizar scripts, Asistente, Comparar, Informes, Ajustes y Acerca de) y componentes reutilizables (tarjetas, indicadores circulares, gráfico temporal, insignias de estado, diálogo de confirmación, glosario). Un cliente de API resuelve el puerto y el token mediante el comando `backend_info` de Tauri, y un gancho de consulta periódica se pausa cuando la ventana está oculta. Cada página se envuelve en un límite de errores para que un fallo no deje la ventana en blanco. El elemento tridimensional, una lente que gira lentamente en la pantalla de carga y en «Acerca de», se implementó con Three.js en un fragmento de carga diferida de 133 KB comprimidos, con resolución limitada y un único fotograma estático cuando se reducen las animaciones.

# Implementación del backend

El motor se inicia con `python -m backend` o como `scriptlens-backend.exe`. Al arrancar enlaza un socket libre, comienza a escuchar, inicia dos hilos de muestreo (sistema cada segundo y procesos cada dos segundos) y escribe una línea JSON con el puerto y el token. FastAPI exige el token en todas las rutas y desactiva la documentación pública. Las consultas a PowerShell se realizan con scripts constantes del código y los datos variables, como rutas, se envían por la entrada estándar en JSON para evitar la inyección de comandos.

# Captura de datos

El muestreador global obtiene, con psutil, el uso de CPU total y por núcleo, la memoria usada y disponible, el archivo de paginación, y las tasas de disco y red calculadas como diferencia de contadores dividida por el tiempo real. Conserva diez minutos en memoria. Las pruebas comprueban que la memoria usada más la disponible es igual a la total, que los porcentajes están entre 0 y 100, que las tasas no son negativas aunque un contador se reinicie y que la temperatura se informa como no disponible en lugar de inventarse.

# Monitoreo de procesos

La lectura de procesos usa `NtQuerySystemInformation(SystemProcessInformation)` mediante ctypes y calcula la CPU de cada proceso a partir de la diferencia de sus tiempos de usuario y núcleo, normalizada al total del equipo. Las rutas se obtienen una sola vez por proceso y se guardan en caché por PID y hora de creación. Las firmas se verifican en lotes con `Get-AuthenticodeSignature`, que, a diferencia de una llamada directa a `WinVerifyTrust` sobre el archivo, valida los binarios de Windows firmados por catálogo. Cada proceso se clasifica como núcleo de Windows, servicio, aplicación abierta o proceso en segundo plano, y se le asignan señales con su fuente y su tipo: comprobado o estimado.

Figura: docs/capturas/05_detalle_proceso.png | Detalle de un proceso con preguntas frecuentes | Microsoft Defender aparece con firma válida, su proceso padre y sus procesos hijos; ScriptLens no permite finalizarlo por ser un componente de seguridad.

En la primera verificación con datos reales, 331 procesos tenían firma válida y 7 no estaban firmados. Ninguno se marcó como sospechoso, conforme al principio de no calificar un proceso como malicioso solo por carecer de firma o consumir muchos recursos.

# Sistema de diagnóstico

El diagnóstico evalúa el promedio del último minuto y exige al menos 20 mediciones antes de hablar de consumo sostenido. Las reglas producen los estados normal, informativo, consumo elevado, requiere revisión e información insuficiente, con una explicación sencilla, la evidencia medida y una recomendación.

Tabla: Reglas de diagnóstico de rendimiento
| Condición | Estado |
|---|---|
| Menos de 20 mediciones | Información insuficiente |
| CPU promedio ≥ 80 % | Consumo elevado |
| 60 % ≤ CPU promedio < 80 % | Informativo |
| RAM promedio ≥ 85 % | Consumo elevado |
| 75 % ≤ RAM promedio < 85 % | Informativo |
| Unidad de disco ≥ 90 % ocupada | Requiere revisión |
| Ninguna de las anteriores | Normal |

# Auditoría de Windows

La auditoría es de solo lectura y se ejecuta únicamente cuando el usuario la solicita. Una sola invocación de PowerShell consulta Microsoft Defender, el Centro de seguridad, el firewall, las tareas programadas, los eventos del registro Sistema de los últimos siete días, las cuentas locales y el plan de energía; el inicio automático se lee del Registro, incluido el estado de `StartupApproved` que usa el Administrador de tareas, y los servicios se leen con psutil. Cada hallazgo responde a ocho preguntas: qué se encontró, dónde, por qué requiere revisión, qué evidencia existe, qué información falta, qué consecuencias podría tener, qué puede hacer el usuario y qué no se recomienda. Solo Microsoft Defender puede originar el estado «amenaza detectada».

Figura: docs/capturas/09_seguridad.png | Centro de seguridad con hallazgos reales | En el equipo de desarrollo, la auditoría tardó entre 3,4 y 6,4 s sin privilegios de administrador.

En el equipo de desarrollo se detectaron dos elementos que requieren revisión: la entrada de inicio «SoyMicrosoft», que ejecuta `C:\taller1\gestion.bat`, un archivo que ya no existe y cuyo nombre alude a Microsoft sin estar firmado por esta empresa; y la tarea «EcoAccess P3 - vigilante del bot», que ejecuta un script. Ninguno se calificó como malicioso.

# Clasificación de scripts

El analizador recupera el catálogo original de 24 reglas con sus identificadores, patrones, categorías y técnicas, y añade 19 reglas para operaciones de PowerShell y CMD, entre ellas `Invoke-Expression`, descargas con `DownloadString`, la desactivación de Microsoft Defender o del firewall y el borrado de registros de eventos. Los nombres de las técnicas se extrajeron del paquete STIX oficial de ATT&CK 20.1; al hacerlo se comprobó que T1562.001, T1070.001 y T1562.004 fueron revocadas y reemplazadas por T1685, T1685.005 y T1686.

El texto se lee como bytes con un límite de 1 MB y detección de UTF-16 sin marca de orden de bytes. Antes de aplicar las reglas se eliminan formas simples de ofuscación: el carácter `^` en CMD, las comillas invertidas y las concatenaciones en PowerShell, y el contenido de `-EncodedCommand` y `FromBase64String`, que se decodifica para analizarlo como texto. El flujo identifica etiquetas, saltos y ciclos, y, a diferencia de la versión original, evalúa cada ciclo por separado para decidir si tiene salida. Cada línea recibe una explicación. El resultado presenta por separado la clasificación estadística, las reglas, la severidad contextual, la evidencia y las limitaciones. Una prueba analiza el código fuente y verifica que ningún módulo del analizador importa funciones capaces de ejecutar procesos.

Figura: docs/capturas/11_script_lineas_attack.png | Técnicas ATT&CK y explicación línea por línea | El borde de color de cada línea indica si la operación es de consulta, de modificación o sensible.

# Modelo de inteligencia artificial

El clasificador reproduce el pipeline de la guía original: la unión de TF-IDF de n-gramas de caracteres de 3 a 5 («char_wb», `min_df=2`, hasta 20 000 rasgos) con el logaritmo de los conteos de hallazgos por categoría, y una regresión logística multiclase con pesos balanceados. La política híbrida marca un script como sensible si lo indican las reglas o si el modelo asigna una probabilidad de al menos 0,30 a esa clase.

El corpus de entrenamiento tiene 180 scripts sintéticos: 90 BAT generados con el código y la semilla de la guía original y 90 PowerShell generados con un diseño equivalente. Para una evaluación más honesta se escribió un conjunto independiente de 18 scripts realistas, 6 por clase, que no se usa en el entrenamiento. El análisis de errores reveló un defecto heredado: la regla P01 contaba la lectura de la clave Run como persistencia. Antes de corregirla, el baseline obtenía un F1 macro de 0,732 con 43,3 % de falsos positivos en la clase consulta; tras la corrección por contexto, esa tasa fue de 0 %.

Tabla: Resultados del clasificador (F1 macro y recall de la clase sensible)
| Conjunto | Método | F1 macro | Recall sensible | Falsos positivos en consulta |
|---|---|---|---|---|
| Sintético, validación cruzada de 5 pliegues | Reglas (baseline) | 1,000 | 1,000 | 0 % |
| Sintético, validación cruzada de 5 pliegues | Regresión logística | 0,955 | 0,917 | 0 % |
| Sintético, validación cruzada de 5 pliegues | Política híbrida | 0,966 | 1,000 | 0 % |
| Realista independiente (18 scripts) | Reglas (baseline) | 1,000 | 1,000 | 0 % |
| Realista independiente (18 scripts) | Regresión logística | 0,886 | 0,667 | 0 % |
| Realista independiente (18 scripts) | Política híbrida | 1,000 | 1,000 | 0 % |

Estos resultados deben interpretarse con cautela. El F1 de 1,0 de las reglas sobre el corpus sintético es circular, porque el corpus se genera con los mismos comandos que buscan las reglas. El conjunto realista es pequeño y lo etiquetó una sola persona, de modo que el acuerdo entre dos etiquetadores con kappa de Cohen sigue pendiente. Aun así, el resultado confirma la decisión de la guía original: el modelo por sí solo dejó pasar dos de seis scripts sensibles, ambos con patrones poco frecuentes en el corpus, y la política híbrida los recuperó. La interfaz aclara que la probabilidad de la clase sensible indica parecido con los ejemplos de entrenamiento y no es la probabilidad de que un script sea malicioso. El tiempo de análisis de un script típico es de unos 10 ms y el de un archivo de 1 MB, de 3,4 s.

# Integración de Ollama

El asistente separa la explicación de la acción. Un enrutador determinista decide qué herramientas internas consultar según la pregunta; existen doce herramientas, todas de solo lectura y con parámetros validados, como el resumen de rendimiento, los programas que más memoria o CPU usan, los procesos en segundo plano, las aplicaciones no esenciales, la auditoría de seguridad, el inicio automático, las tareas, el disco, los cambios desde el último diagnóstico y el último script analizado. El modelo recibe los resultados dentro de un bloque delimitado, con instrucciones que le prohíben inventar cifras, recomendar desactivar protecciones o obedecer órdenes contenidas en los datos. Los textos procedentes del equipo se sanean antes de enviarse.

Al integrarlo se encontró que la etiqueta `qwen3:4b` de Ollama corresponde a una variante que razona antes de responder: generó 2 940 tokens y tardó 256 s en una respuesta de una frase, y ni el parámetro `think:false` ni la instrucción `/no_think` lo evitaron. Se adoptó `qwen3:4b-instruct`, de la misma familia y tamaño, que respondió entre 10 y 58 s según la carga del equipo.

Cada respuesta se verifica cifra por cifra contra los datos entregados. En una prueba real, ante la pregunta «¿Por qué mi computador está lento?», el modelo afirmó que dos programas ocupaban «más del 70 % de la RAM», una cifra ausente de los datos; el verificador la marcó y la interfaz mostró «Cifras no verificadas: 70». Si Ollama no está instalado o falla durante la respuesta, el asistente responde con plantillas a partir de los mismos datos.

Figura: docs/capturas/12_asistente_ia.png | Asistente con respuestas verificadas | La respuesta sobre programas sospechosos cita los hallazgos reales de la auditoría y aclara que Defender no registró amenazas.

# Sistema de acciones supervisadas

Las acciones se ejecutan en dos pasos con un token de un solo uso que caduca a los 60 s. Antes de actuar sobre un proceso, el motor verifica de nuevo su PID, su hora de creación y su nombre; si Windows reutilizó el PID, la acción se cancela. No pueden finalizarse procesos críticos, de seguridad, servicios ni la propia ScriptLens. Se prioriza la alternativa menos invasiva: solicitar el cierre de la ventana antes que finalizar el proceso, y desactivar un inicio automático de forma reversible en lugar de borrarlo. La limpieza solo elimina archivos de la carpeta temporal del usuario con más de siete días y nunca toca la carpeta Descargas. La desinstalación abre el desinstalador oficial del programa. Cada acción se registra con las mediciones anteriores y las posteriores.

Figura: docs/capturas/08_confirmacion_accion.png | Diálogo de confirmación de una acción | El botón con el foco inicial es «Cancelar». La captura se tomó sin ejecutar la limpieza.

# Seguridad y privacidad

La API escucha solo en 127.0.0.1 con un puerto y un token aleatorios por arranque, comparados en tiempo constante, y con CORS limitado a los orígenes de Tauri. La aplicación se instala por usuario y no requiere administrador. El asistente no puede alcanzar el módulo de acciones, lo que se comprueba con una prueba que analiza sus importaciones. Los nombres de procesos y rutas se escapan en los informes HTML, los enlaces externos se limitan a una lista permitida y la apertura de informes se restringe a su carpeta. Las mediciones permanecen en memoria diez minutos; los diagnósticos, conversaciones y acciones se guardan en SQLite y pueden borrarse desde Ajustes. La comprobación de actualizaciones solo se realiza a petición del usuario y no envía datos del equipo.

# Persistencia de datos

La base SQLite se crea en la carpeta de datos de la aplicación con un esquema versionado mediante `PRAGMA user_version`. Contiene las tablas de diagnósticos, procesos por diagnóstico agrupados por nombre, acciones, conversaciones, mensajes y ajustes. La comparación de diagnósticos describe las diferencias de CPU, RAM y procesos y nunca afirma una causa: cuando procede, indica que los cambios «coinciden en el tiempo» con lo ocurrido entre ambos diagnósticos.

Figura: docs/capturas/13_comparar.png | Comparación de dos diagnósticos | Incluye las diferencias por programa y las limitaciones de la comparación.

# Generación de informes

Los informes reúnen el resumen del sistema, las métricas del último minuto, los programas destacados, los hallazgos de seguridad, las evidencias, las recomendaciones, las acciones realizadas, la comparación opcional y las limitaciones. El HTML es autocontenido; el PDF se genera con reportlab y la fuente Segoe UI. Ambos incluyen el nombre del proyecto, el autor, el repositorio y una marca de agua con 5 % de opacidad que no afecta la lectura.

Figura: docs/capturas/19_informe_pdf.png | Primera página de un informe PDF real | Informe generado desde la aplicación instalada el 14 de noviembre de 2026.

# Historial de desarrollo

El desarrollo se realizó entre el 14 y el 15 de noviembre de 2026 en la rama `feat/desarrollo-integral`, partiendo de un repositorio vacío. La bitácora de `docs/desarrollo/bitacora.md` registra para cada fase su objetivo, los archivos afectados, las pruebas, los errores, las soluciones y los hashes de los commits.

# Commits reales

Tabla: Commits principales de la rama de desarrollo
| Hash | Descripción |
|---|---|
| ae3af68 | Inicializar el repositorio de ScriptLens IA |
| 5e129dd | Implementar el motor de monitoreo real del sistema |
| 6267e26 | Diseñar el panel principal y el sistema de diseño de la interfaz |
| 63b96c2 | Configurar el contenedor de escritorio Tauri y la identidad gráfica |
| efc02c7 | Actualizar las acciones de integración continua a versiones con Node.js 24 |
| 3108cbd | Implementar el inventario de procesos con firmas, rutas y explicaciones |
| 47519d0 | Incorporar el historial local en SQLite y la comparación de diagnósticos |
| b4b93ff | Implementar la auditoría de seguridad de Windows |
| b82ab66 | Recuperar el analizador de scripts del proyecto original |
| a9c9cb4 | Mejorar la clasificación con regresión logística balanceada y evaluación reproducible |
| 6c26621 | Añadir comprobaciones antes de finalizar procesos y acciones supervisadas |
| bc7a547 | Integrar el asistente local y conectar sus respuestas con métricas reales |
| 7d8f06a | Crear informes PDF y HTML con marca de agua |
| aab7b22 | Corregir defectos encontrados al probar la aplicación instalada |
| 04f9709 | Preparar el instalador de Windows con el motor empaquetado |
| 4c2e76a | Añadir capturas reales de la aplicación instalada |
| fac9596 | Elaborar la documentación técnica, el informe de ExpoSoftware y el manual de usuario |
| 109b712 | Corregir la comunicación del motor empaquetado con la interfaz Windows |
| b2e4ce8 | Impedir limpiezas de temporales cuando TEMP no sea segura |
| 0794f85 | Garantizar el anuncio de conexión del motor aunque falte stdout |
| 8dc8706 | Proteger la limpieza de temporales frente a uniones y carpetas personales |
| f6e962e | Corregir el enrutado del asistente para alertas, investigación y arranque reciente |
| 451f19b | Respetar las carpetas de usuario redirigidas a OneDrive |

# Pruebas

Se ejecutaron 135 pruebas automatizadas con pytest, todas aprobadas al cierre, distribuidas en 14 archivos. La prueba de rendimiento CP6 (archivo de 5 MB truncado a 1 MB) tardó entre 3,4 y 8,5 s según la carga del equipo y falló una vez, con 17,5 s, mientras otro conjunto de pruebas y el modelo de lenguaje ocupaban el procesador; se repitió con menor carga y se aprobó. Las pruebas usan procesos hijos reales para simular procesos que terminan durante la medición, una base de datos aislada para no tocar los datos del usuario y una clave del Registro de pruebas para el inicio automático. GitHub Actions ejecuta las pruebas del motor, la compilación con comprobación de tipos de la interfaz y `cargo check` del contenedor.

Tabla: Distribución de las pruebas automatizadas
| Archivo | Pruebas | Qué comprueba |
|---|---|---|
| test_monitoring.py | 9 | Unidades, rangos, contadores reiniciados, consumo sostenido frente a picos |
| test_processes.py y test_ntquery.py | 8 | Procesos que terminan, acceso denegado, lectura nativa contra psutil |
| test_process_manager.py | 15 | Firmas por catálogo, rutas con comillas, suplantación, procesos protegidos |
| test_api.py y test_startup.py | 9 | Token, validación de parámetros, arranque y cierre sin huérfanos |
| test_history.py | 5 | Migraciones, borrado en cascada, comparación sin causalidad |
| test_security.py | 11 | Estructura de hallazgos, permisos insuficientes, recolección real |
| test_scripts.py | 14 | Casos CP1–CP6, desofuscación, independencia de resultados, no ejecución |
| test_actions.py y test_known_folders.py | 23 | Token único, revalidación, protección, reversibilidad, TEMP vacía, relativa o personal, uniones NTFS, carpetas redirigidas a OneDrive |
| test_assistant.py | 34 | 15 preguntas obligatorias, 10 preguntas de referencia, saneamiento, verificación, ausencia de Ollama |
| test_reports.py y test_updates_links.py | 7 | PDF válido, marca de agua, lista permitida, actualizaciones sin red |

Además se realizaron pruebas manuales en la aplicación instalada: recorrido de todas las pantallas, consultas reales al asistente, comparación de diagnósticos, generación de un informe, modo claro y oscuro, instalación, desinstalación, reinstalación e instancia única.

# Problemas encontrados

Tabla: Problemas encontrados durante el desarrollo
| Problema | Causa identificada |
|---|---|
| La lectura de procesos tardaba 3,4 s | psutil consulta la lista completa del sistema por cada atributo de cada proceso |
| `link.exe` no encontrado | Instancia de Build Tools no registrada |
| «Motor desconectado» al iniciar | El motor anunciaba estar listo antes de escuchar en el socket |
| Motor huérfano al cerrar | El intérprete del entorno virtual crea un segundo proceso |
| Firmas no verificadas | Windows PowerShell 5.1 heredaba los módulos de PowerShell 7 |
| Pruebas escribían en la base real | La ruta de datos se fijaba al definir la clase de configuración |
| Lectura de la clave Run como persistencia | Regla P01 sin contexto |
| Técnicas ATT&CK inexistentes | Revocadas en ATT&CK 20.1 |
| Respuesta del asistente en 256 s | Variante de razonamiento de Qwen3 |
| Ventana en blanco en el asistente | `scrollIntoView` devuelve una Promise en WebView2 reciente |
| Interruptores mal dibujados | Alineación a la derecha de la celda |
| Dos instancias y dos motores | Sin control de instancia única |
| Informes dentro de la carpeta del repositorio | Ruta predeterminada coincidente |
| Análisis de 1 MB en 10,4 s | El catálogo se evaluaba cuatro veces sobre el mismo texto |
| Motor empaquetado sin canal de arranque (P1) | PyInstaller en modo ventana deja `sys.stdout` en `None` y el puerto no llega a Tauri |
| Limpieza fuera de la carpeta temporal (P1) | `TEMP` vacía se resolvía como el directorio de trabajo |
| Recorrido de temporales dentro de uniones NTFS | `os.walk` entra en las uniones aunque no siga enlaces simbólicos |
| Informes fuera de la carpeta Documentos visible | Documentos redirigida a OneDrive y ruta fija `%USERPROFILE%\Documents` |
| «Esta» tomado como nombre de proceso por el asistente | Patrón de «qué significa…» sin lista de palabras excluidas |
| Ranking de CPU nulo al iniciar | El promedio de un minuto aún no existía |

# Correcciones

Cada problema de la tabla anterior se corrigió y se cubrió con una prueba cuando fue posible: lectura nativa de procesos; script de entorno MSVC; escucha del socket antes de anunciar el arranque; vigilancia del PID de la aplicación; eliminación de la variable `PSModulePath`; carpeta de datos aislada para pruebas; corrección por contexto de P01; identificadores vigentes de ATT&CK; adopción de Qwen3 4B Instruct; efectos de React sin valor de retorno y límite de errores; posición fija del indicador de los interruptores; complemento de instancia única de Tauri; carpeta `Documentos\ScriptLens IA\Informes`; y memorización de los hallazgos, que redujo el análisis de 1 MB de 10,4 s a 3,4 s.

# Revisión de cierre y defectos de prioridad alta

La revisión automática del pull request señaló dos defectos de prioridad P1 que las pruebas anteriores no habían detectado. Ambos se corrigieron, se cubrieron con pruebas de regresión y se volvieron a comprobar con el instalador reconstruido.

**Comunicación entre Tauri y el motor empaquetado.** El motor anuncia su puerto y su token en una única línea JSON por la salida estándar, y el contenedor Rust la lee de la tubería del proceso hijo. PyInstaller, en modo ventana (`--noconsole`), deja `sys.stdout` con valor `None`, de modo que el anuncio podía perderse y la aplicación quedarse en la pantalla de inicio. Se empaquetó el motor en modo consola, manteniendo la ventana oculta con la bandera `CREATE_NO_WINDOW` que ya aplicaba el contenedor, y se añadió una segunda defensa: si `sys.stdout` falta, el anuncio se escribe directamente en el descriptor de salida que Windows entregó al proceso. La corrección se validó instalando la aplicación y comprobando que el motor empaquetado responde a la interfaz.

**Limpieza de archivos temporales.** Si la variable `TEMP` estaba vacía, `Path("").resolve()` devolvía el directorio de trabajo y la limpieza podía borrar archivos antiguos ajenos a la carpeta temporal; la comprobación de contención usaba esa misma raíz incorrecta. La validación actual rechaza, tanto en la vista previa como de nuevo en la ejecución, una variable ausente, vacía, relativa, inexistente o que sea un enlace, así como la raíz de una unidad, el perfil del usuario, cualquier carpeta que lo contenga, las carpetas personales conocidas y la carpeta de Windows. El recorrido no entra en enlaces simbólicos ni en uniones NTFS (`os.walk` sí entra en las uniones aunque no siga enlaces), cada archivo se resuelve y debe seguir dentro de la carpeta temporal, y la ejecución exige el token emitido por la confirmación del usuario. Las pruebas usan carpetas temporales aisladas: una unión hacia una carpeta externa con un documento antiguo comprueba que el documento permanece intacto mientras se elimina el residuo legítimo.

**Otros defectos de la revisión de cierre.** Al recorrer las diez preguntas de referencia del asistente se encontraron tres fallos de enrutado: «¿Qué significa esta alerta?» tomaba «esta» como nombre de proceso, «¿Qué proceso requiere investigación?» solo consultaba el resumen de rendimiento y, recién iniciado el motor, el ranking de CPU devolvía promedios nulos que el modelo interpretaba como «ningún proceso usa CPU». Se añadieron la intención «alerta», una lista de palabras que no son procesos y una nota explícita cuando el motor lleva menos de un minuto midiendo. En la interfaz se completó la sección Acerca de con la identidad oficial y la información técnica, la tabla de procesos se adaptó al ancho mínimo de la ventana y el asistente ofrece «Comprobar de nuevo» cuando Ollama no está activo. La prueba del motor empaquetado en el equipo de desarrollo, cuya carpeta Documentos está redirigida a OneDrive, reveló que los informes se guardaban en `%USERPROFILE%\Documents`, una carpeta que el usuario no ve como «Documentos»; ahora las carpetas se obtienen de Windows con `SHGetKnownFolderPath` y la limpieza protege tanto las rutas reales como las clásicas. Por último, el instalador se publica con un nombre sin espacios, porque GitHub sustituye los espacios de los archivos adjuntos por puntos y los enlaces de la documentación no coincidirían.

# Compilación

La interfaz se compila con `npm --prefix frontend run build`, que ejecuta la comprobación de tipos de TypeScript y genera los archivos con Vite. El motor se empaqueta con PyInstaller en una carpeta de 159 MB que incluye los datos del modelo y de ATT&CK. El contenedor se compila en modo *release* con optimización por tamaño, LTO y eliminación de símbolos. Todo el proceso se ejecuta en **PowerShell** con `.\scripts\construir_instalador.ps1`.

# Instalador

Tauri genera un instalador NSIS en español, de instalación por usuario, que copia la aplicación, el motor como recurso, la licencia y los avisos de terceros en `%LOCALAPPDATA%\ScriptLens IA` y crea los accesos directos. El historial se guarda aparte, en `%LOCALAPPDATA%\io.github.jorgegutho21.scriptlens`, carpeta que Tauri asigna a la aplicación y que el motor recibe en la variable `SCRIPTLENS_DATA_DIR`. El asistente de instalación muestra una barra lateral y un encabezado con la identidad del proyecto, generados a partir del icono con `scripts/generar_imagenes_instalador.py`. El instalador final pesa 49,3 MB (51 678 985 bytes) y su SHA-256 es `111397CF7D8164943D79F99488F3B868603A4CA32053D116D8B522AC37B6D13A`.

Con ese mismo archivo se comprobó en Windows 11, desde una sesión sin privilegios de administrador, que la instalación silenciosa termina en 11,8–18,3 s (también sobre una versión ya instalada), que el acceso del menú Inicio abre la aplicación y que el motor empaquetado escucha solo en 127.0.0.1 entre 6,5 y 12,2 s después, que la interfaz recibe sus datos en vivo, que una segunda apertura deja una sola aplicación y un solo motor, que al forzar el cierre de la aplicación el motor termina en 1–1,6 s y que la desinstalación elimina la carpeta, la entrada del registro y los accesos directos conservando el historial y los informes. Los detalles y los entornos que no pudieron probarse están en `docs/pruebas/compatibilidad.md`.

Figura: docs/capturas/00_instalador_bienvenida.png | Primera pantalla del instalador | Captura real del instalador final, con la identidad de ScriptLens IA.

# Distribución pública

El repositorio incluye un flujo de GitHub Actions que construye el instalador y su SHA-256 como artefacto descargable sin publicar ninguna release, las notas de la versión y la *Guía de instalación de ScriptLens IA* (DOCX y PDF), dirigida a personas que nunca han usado GitHub, con tres métodos: gráfico, con verificación del hash en PowerShell y desde CMD o el código fuente para desarrolladores. El instalador se publica como `ScriptLens-IA_0.1.0_x64-setup.exe` junto a su `.sha256`: GitHub sustituye por puntos los espacios de los archivos adjuntos, de modo que el nombre que genera Tauri no coincidiría con los enlaces de la documentación. Como el instalador no tiene firma de código comercial, Windows SmartScreen mostrará un aviso; la guía pide comprobar la procedencia y la huella antes de continuar y no recomienda omitir el aviso de forma automática. La publicación en GitHub Releases requiere la autorización del autor.

# Manual de usuario

El manual para principiantes se entrega por separado en `docs/manual_usuario/Manual_Usuario_ScriptLens_IA.pdf`, con capturas reales de cada pantalla.

# Mantenimiento

Para actualizar el clasificador se modifica el catálogo o el corpus y se ejecuta `python -m backend.scripts.train`, que regenera el modelo y el informe de evaluación. Para actualizar los nombres de ATT&CK se descarga el paquete STIX vigente y se ejecuta `scripts/extraer_attack.py`. La base de datos admite nuevas versiones de esquema mediante migraciones numeradas. El archivo `docs/ESTADO_DESARROLLO.md` describe cómo reanudar el trabajo.

# Resultados

Se cumplieron los objetivos de la versión 0.1.0: la aplicación mide el equipo en tiempo real, explica los procesos con datos comprobados, audita la seguridad sin privilegios, analiza scripts con resultados independientes y evaluados, responde preguntas con cifras verificadas, ejecuta acciones supervisadas, compara diagnósticos, genera informes y se instala sin herramientas de desarrollo. En la aplicación instalada, tras un minuto, el motor ocupó 163 MB de memoria de trabajo, el contenedor Tauri 28 MB y los seis procesos de WebView2 485 MB; la interfaz es, por tanto, el componente que más memoria usa.

# Conclusiones

Separar la medición, la interpretación y la acción permitió construir una herramienta comprensible para principiantes sin sacrificar la seguridad. La evaluación sobre un conjunto independiente mostró que el modelo estadístico aislado no basta para la clase peligrosa y que la política híbrida propuesta en la guía original es necesaria. La verificación cifra por cifra resultó útil en la práctica: detectó una cifra inventada por el modelo en una consulta real. Las pruebas sobre la aplicación instalada revelaron defectos que no aparecían en el entorno de desarrollo, lo que confirma la importancia de verificar el producto distribuido.

# Recomendaciones

Se recomienda ampliar el conjunto realista de scripts con ejemplos autorizados y etiquetados por dos personas para medir el kappa de Cohen; firmar el instalador con un certificado de código; publicar la versión en GitHub Releases tras la revisión del autor; y evaluar la experiencia de uso con personas sin formación técnica.

[[SALTO]]

# Referencias

[[REFERENCIAS]]

American Psychological Association. (2020). *Publication manual of the American Psychological Association* (7th ed.). https://doi.org/10.1037/0000165-000

Bohannon, D., & Holmes, L. (2017). *Revoke-Obfuscation: PowerShell obfuscation detection framework* [Computer software]. GitHub. https://github.com/danielbohannon/Revoke-Obfuscation

Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement, 20*(1), 37–46. https://doi.org/10.1177/001316446002000104

Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023). Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection. En *Proceedings of the 16th ACM Workshop on Artificial Intelligence and Security* (pp. 79–90). ACM. https://doi.org/10.1145/3605764.3623985

Hendler, D., Kels, S., & Rubin, A. (2018). Detecting malicious PowerShell commands using deep neural networks. En *Proceedings of the 2018 Asia Conference on Computer and Communications Security* (pp. 187–197). ACM. https://doi.org/10.1145/3196494.3196511

Hosmer, D. W., Lemeshow, S., & Sturdivant, R. X. (2013). *Applied logistic regression* (3rd ed.). Wiley. https://doi.org/10.1002/9781118548387

Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y. J., Madotto, A., & Fung, P. (2023). Survey of hallucination in natural language generation. *ACM Computing Surveys, 55*(12), Artículo 248. https://doi.org/10.1145/3571730

King, G., & Zeng, L. (2001). Logistic regression in rare events data. *Political Analysis, 9*(2), 137–163. https://doi.org/10.1093/oxfordjournals.pan.a004868

Kohavi, R. (1995). A study of cross-validation and bootstrap for accuracy estimation and model selection. En *Proceedings of the 14th International Joint Conference on Artificial Intelligence* (Vol. 2, pp. 1137–1143). Morgan Kaufmann.

Microsoft. (s. f.-a). *Get-AuthenticodeSignature*. Microsoft Learn. Recuperado el 14 de noviembre de 2026, de https://learn.microsoft.com/powershell/module/microsoft.powershell.security/get-authenticodesignature

Microsoft. (s. f.-b). *Get-MpComputerStatus*. Microsoft Learn. Recuperado el 14 de noviembre de 2026, de https://learn.microsoft.com/powershell/module/defender/get-mpcomputerstatus

Microsoft. (s. f.-c). *NtQuerySystemInformation function (winternl.h)*. Microsoft Learn. Recuperado el 14 de noviembre de 2026, de https://learn.microsoft.com/windows/win32/api/winternl/nf-winternl-ntquerysysteminformation

MITRE. (2026). *ATT&CK STIX data* (Versión 20.1) [Conjunto de datos]. GitHub. https://github.com/mitre-attack/attack-stix-data

OWASP Foundation. (2025). *OWASP Top 10 for large language model applications 2025*. https://genai.owasp.org/llm-top-10/

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html

Qwen Team. (2025). *Qwen3 technical report* (arXiv:2505.09388). arXiv. https://doi.org/10.48550/arXiv.2505.09388

Rodola, G. (2026). *psutil* (Versión 7.2.2) [Computer software]. GitHub. https://github.com/giampaolo/psutil

Salton, G., & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval. *Information Processing & Management, 24*(5), 513–523. https://doi.org/10.1016/0306-4573(88)90021-0

Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). *Operating system concepts* (10th ed.). Wiley.

Strom, B. E., Applebaum, A., Miller, D. P., Nickels, K. C., Pennington, A. G., & Thomas, C. B. (2018). *MITRE ATT&CK: Design and philosophy* (Technical Report MP180360). The MITRE Corporation. https://attack.mitre.org/docs/ATTACK_Design_and_Philosophy_March_2020.pdf

Tauri Contributors. (2026). *Tauri* (Versión 2) [Computer software]. https://tauri.app

Yosifovich, P., Ionescu, A., Russinovich, M. E., & Solomon, D. A. (2017). *Windows internals, part 1* (7th ed.). Microsoft Press.

[[SALTO]]

# Anexos

## Anexo A. Resultados completos del clasificador

El informe completo, con las matrices de confusión y el detalle por script, se encuentra en `docs/pruebas/evaluacion_clasificador.md` y se regenera con `python -m backend.scripts.train`.

## Anexo B. Capturas de la aplicación

Figura: docs/capturas/04_procesos.png | Administrador de procesos | Tabla con firma y editor verificados.

Figura: docs/capturas/06_arbol_procesos.png | Árbol de procesos | El árbol descarta padres con hora de creación posterior a la del hijo.

Figura: docs/capturas/07_optimizar.png | Optimización supervisada | Vista previa de temporales y recomendaciones basadas en mediciones.

Figura: docs/capturas/18_inicio_automatico.png | Inicio automático | Interruptores reversibles; las entradas de todos los usuarios requieren administrador.

Figura: docs/capturas/10_analisis_script.png | Resultados independientes del análisis de un script | Clasificación estadística, reglas y severidad contextual.

Figura: docs/capturas/20_ajustes_privacidad.png | Ajustes de accesibilidad y privacidad | Muestra las rutas reales de datos e informes.
