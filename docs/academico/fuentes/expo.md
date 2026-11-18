[[TOC]]

# Resumen

Muchos usuarios de Windows no saben por qué su equipo está lento, qué programas se ejecutan en segundo plano ni qué hace un script antes de ejecutarlo. ScriptLens IA es una aplicación de escritorio que mide el equipo en tiempo real, explica los procesos con evidencia comprobada, audita la seguridad sin privilegios de administrador, analiza scripts BAT, CMD y PowerShell sin ejecutarlos y responde preguntas mediante un modelo de lenguaje que funciona localmente. Se siguió una metodología de desarrollo tecnológico incremental en fases con criterios de aceptación, pruebas automatizadas y evaluación cuantitativa. El analizador combina un catálogo de 43 reglas asociadas a MITRE ATT&CK con una regresión logística balanceada sobre TF-IDF de n-gramas de caracteres. En un conjunto independiente de 18 scripts realistas, la política híbrida de reglas y modelo detectó los 6 scripts sensibles (recall de 1,0), mientras que el modelo por sí solo detectó 4 de 6. El asistente, basado en Qwen3 4B Instruct, consulta únicamente herramientas de solo lectura y verifica cada cifra de su respuesta; en una prueba real detectó una cifra inventada por el modelo. Se ejecutaron 135 pruebas automatizadas y el instalador final, de 49,3 MB, se verificó en Windows 11 sin privilegios de administrador y se publicó en GitHub Releases.

*Palabras clave:* diagnóstico de sistemas operativos, análisis estático de scripts, regresión logística, MITRE ATT&CK, inteligencia artificial local, verificación de respuestas.

[[SALTO]]

# Introducción

Los sistemas operativos ofrecen gran cantidad de información sobre su estado, pero la presentan en herramientas dispersas y técnicas. Este informe presenta ScriptLens IA, un proyecto del programa de Ingeniería de Sistemas de la Universidad Popular del Cesar para ExpoSoftware 2026-II, que convierte esa información en explicaciones comprensibles y en acciones seguras bajo el control del usuario. El proyecto amplía una propuesta previa del autor que planteaba un analizador estático de scripts con aprendizaje supervisado; aquí se construye, se evalúa y se integra en una aplicación completa e instalable.

El informe se organiza de la siguiente manera: primero se plantean el problema, la justificación y los objetivos; luego se presenta el marco referencial; después se describen la metodología y el desarrollo; finalmente se exponen los resultados medidos, su discusión, las conclusiones y las recomendaciones.

# Planteamiento del problema

## Descripción del problema

Cuando un computador responde lentamente, el usuario sin formación técnica no puede identificar con facilidad la causa, y las recomendaciones que encuentra en Internet a menudo son riesgosas, como finalizar procesos esenciales o desactivar el antivirus. De forma similar, en los cursos de Sistemas Operativos circulan scripts que modifican el Registro, crean tareas programadas, ocultan archivos o borran carpetas; quien los ejecuta sin leerlos asume efectos que desconoce. Los antivirus no explican qué hace un script benigno pero riesgoso y no están diseñados para enseñar.

## Pregunta de investigación

¿Puede una aplicación local que combine mediciones verificadas, reglas expertas asociadas a MITRE ATT&CK, un clasificador supervisado y un modelo de lenguaje con verificación de cifras explicar el estado de un equipo Windows y el riesgo de un script a un usuario sin formación técnica, sin enviar datos fuera del equipo y sin ejecutar acciones sin su consentimiento?

# Justificación

La propuesta es pertinente para la asignatura porque aplica conceptos centrales de Sistemas Operativos —procesos, memoria, servicios, Registro, planificación de tareas y seguridad— en una herramienta útil. Es segura por diseño: los scripts nunca se ejecutan, las acciones requieren confirmación y la inteligencia artificial no puede actuar. Es medible: el clasificador se evalúa de forma reproducible frente a un baseline sin inteligencia artificial. Y es respetuosa con la privacidad, porque todo el análisis ocurre en el equipo del usuario.

# Objetivos

## Objetivo general

Desarrollar y evaluar una aplicación de escritorio para Windows que diagnostique el rendimiento y la seguridad del equipo, analice scripts sin ejecutarlos y explique sus hallazgos mediante inteligencia artificial local verificada, con acciones supervisadas por el usuario.

## Objetivos específicos

1. Medir en tiempo real el procesador, la memoria, el disco, la red y los procesos, distinguiendo el consumo sostenido de los picos.
2. Explicar cada proceso con datos comprobados (ruta, firma digital, editor, relaciones) y conclusiones estimadas claramente identificadas.
3. Auditar sin privilegios Microsoft Defender, el firewall, el inicio automático, las tareas programadas, los servicios y los eventos.
4. Construir y evaluar un clasificador de riesgo de scripts frente a un baseline de reglas.
5. Integrar un asistente local cuyas cifras se verifiquen contra los datos medidos.
6. Distribuir la aplicación en un instalador verificado que no requiera herramientas de desarrollo.

# Marco referencial

## Antecedentes

La entrega académica previa del autor contenía tres propuestas: BitácoraIA, un asistente que explica auditorías verificando cada cifra; ScriptLens IA, un analizador estático de scripts con 24 reglas en 9 categorías y un clasificador de regresión logística balanceada; y RecuperaSO IA, un monitor de CPU y RAM con detección de anomalías. Las tres se presentaban como propuestas con métricas sin medir. Este proyecto toma como núcleo ScriptLens IA, incorpora la verificación de cifras de BitácoraIA y el monitoreo de RecuperaSO, y presenta resultados medidos.

## Estado del arte

Tabla: Herramientas existentes relacionadas
| Herramienta | Enfoque | Limitación frente al problema |
|---|---|---|
| Administrador de tareas de Windows | Cifras de consumo por proceso | No explica ni distingue consumo sostenido |
| System Informer | Inspección avanzada de procesos | Orientada a especialistas |
| Glances | Monitor multiplataforma con umbrales | Sin explicaciones ni análisis de seguridad |
| osquery | Consultas SQL sobre el sistema | Requiere conocimientos técnicos y un servicio permanente |
| Microsoft Defender | Detección de malware | No explica scripts benignos pero riesgosos |
| PSScriptAnalyzer | Reglas de calidad y seguridad para PowerShell | Solo PowerShell y sin explicaciones para principiantes |

En investigación, Hendler et al. (2018) abordaron la detección de PowerShell malicioso como clasificación de texto con redes neuronales a nivel de caracteres, y Bohannon y Holmes (2017) estudiaron la ofuscación de PowerShell. MITRE ATT&CK ofrece una taxonomía estándar de técnicas (Strom et al., 2018). En modelos de lenguaje, se han documentado la alucinación (Ji et al., 2023) y la inyección indirecta de instrucciones (Greshake et al., 2023) como riesgos principales de su integración en aplicaciones.

## Marco teórico

Un proceso es un programa en ejecución identificado por un PID que Windows puede reutilizar; por ello, la identidad de un proceso se define por su PID y su hora de creación (Yosifovich et al., 2017). El análisis estático examina el código sin ejecutarlo. TF-IDF pondera los términos frecuentes en un documento y raros en el corpus (Salton & Buckley, 1988), y los n-gramas de caracteres toleran variaciones de escritura. La regresión logística estima la probabilidad de cada clase (Hosmer et al., 2013); los pesos balanceados compensan clases de distinto tamaño (King & Zeng, 2001). La validación cruzada estratificada evalúa cada ejemplo sin haberlo usado en el entrenamiento (Kohavi, 1995), y el kappa de Cohen (1960) mide el acuerdo entre etiquetadores.

# Metodología

## Enfoque y tipo de investigación

Se trata de una investigación aplicada de desarrollo tecnológico con enfoque cuantitativo en la evaluación. El producto se construyó de forma incremental y cada incremento se aceptó solo cuando cumplía criterios verificables: pruebas automatizadas aprobadas, compilación correcta en integración continua y comprobación en la aplicación real. Las afirmaciones sobre desempeño se sustentan en mediciones repetibles con scripts incluidos en el repositorio.

## Fases del desarrollo

Tabla: Fases del desarrollo y criterios de aceptación
| Fase | Actividades | Producto | Criterio de aceptación |
|---|---|---|---|
| 1 | Arquitectura, diseño visual y monitoreo | Panel en tiempo real | Cifras coherentes con el sistema; pruebas de monitoreo |
| 2 | Inventario de procesos | Administrador de procesos | Lectura completa < 0,1 s; firmas y rutas verificadas |
| 3 | Persistencia | Historial y comparación | Migraciones y borrado probados |
| 4 | Auditoría de Windows | Centro de seguridad | Funciona sin administrador; hallazgos con evidencia |
| 5 | Análisis de scripts | Reglas, ATT&CK y clasificador | Evaluación reproducible frente al baseline |
| 6 | Acciones supervisadas | Cierre, inicio automático, temporales | Confirmación, revalidación y registro |
| 7 | Asistente local | Respuestas con cifras verificadas | Herramientas de solo lectura; modo sin IA |
| 8 | Informes | PDF y HTML | Documento válido con identidad y marca de agua |
| 9 | Distribución | Instalador NSIS | Instalación sin administrador en Windows 11 |
| 10–13 | Documentación, revisión y publicación | Documentos, correcciones y versiones v0.1.0 y v0.1.1 | Defectos críticos corregidos; descarga pública verificada |

## Diseño del sistema

La aplicación tiene dos procesos: un contenedor Tauri (Rust) que muestra la interfaz React y un motor de análisis en Python. El contenedor inicia el motor, recibe un puerto y un token aleatorios y los entrega a la interfaz. El motor expone una API solo en 127.0.0.1, exige el token en cada petición y se cierra si la aplicación desaparece. Sus módulos son: monitoreo, procesos, historial, seguridad, scripts, acciones, asistente e informes.

La interfaz está pensada para principiantes: modo sencillo y avanzado, glosario contextual, asistente de primera ejecución, modo claro y oscuro, tamaño de texto ajustable y reducción de animaciones. Cada hallazgo indica su estado con icono y texto, su evidencia y su fuente. Las acciones que modifican el sistema muestran un diálogo de confirmación cuyo botón inicial es «Cancelar».

Figura: docs/capturas/02_panel_general.png | Panel general de ScriptLens IA | Captura real de la aplicación instalada en el equipo de pruebas.

## Herramientas

Tabla: Herramientas utilizadas
| Herramienta | Uso |
|---|---|
| Tauri 2, React 19, TypeScript, Tailwind CSS 4, Three.js | Aplicación de escritorio e interfaz |
| Python 3.12, FastAPI, psutil, ctypes | Motor de análisis y lectura del sistema |
| SQLite | Historial local |
| scikit-learn, joblib | Clasificador de scripts |
| Ollama, Qwen3 4B Instruct | Asistente local |
| reportlab | Informes PDF |
| PyInstaller, NSIS | Empaquetado e instalador |
| pytest, GitHub Actions | Pruebas e integración continua |

## Datos y conjuntos de evaluación

Para entrenar el clasificador se generó de forma determinista un corpus sintético de 180 scripts, 60 por clase: consulta (solo lee información), modifica (cambia configuración de forma reversible) y sensible (persistencia, ocultamiento, borrado o desactivación de protecciones). Como el corpus sintético comparte vocabulario con las reglas, se construyó además un conjunto independiente de 18 scripts realistas, escritos a mano y no usados en el entrenamiento, con 6 scripts por clase, etiquetados por el autor. No se usó malware real: los scripts sensibles son demostraciones controladas que nunca se ejecutan.

## Procedimiento de evaluación

1. **Clasificador.** Validación cruzada estratificada de 5 pliegues sobre el corpus sintético y evaluación sobre el conjunto realista. Se compararon tres métodos: reglas (baseline sin aprendizaje), regresión logística y la política híbrida. Métricas: F1 macro, recall de la clase sensible y falsos positivos en la clase consulta. El procedimiento se repite con `python -m backend.scripts.train`.
2. **Pruebas automatizadas.** 135 pruebas de pytest que cubren casos límite: procesos que terminan durante la medición, permisos insuficientes, ausencia de Ollama, rutas maliciosas tratadas como datos, tokens caducados y reutilizados, y rutas temporales inseguras.
3. **Asistente.** Diez preguntas de referencia («¿Qué proceso consume más CPU?», «¿Qué significa esta alerta?», entre otras) con Ollama activo y sin él, comprobando que cada respuesta use herramientas de datos medidos y que sus cifras se verifiquen.
4. **Producto instalado.** Instalación con el instalador final desde una sesión sin privilegios de administrador, apertura desde el menú Inicio, recorrido de todas las pantallas, instancia única, cierre normal y forzado, desinstalación y reinstalación.

## Consideraciones éticas y de seguridad

Todo el análisis se realiza en el equipo del usuario y no se envían datos a servidores externos. Los scripts analizados nunca se ejecutan. Las acciones que modifican el sistema requieren confirmación explícita, revalidan la identidad del proceso y quedan registradas. El modelo de lenguaje no tiene acceso al módulo de acciones. Las pruebas destructivas, como la limpieza de temporales, se realizaron sobre carpetas aisladas y no sobre archivos personales.

# Desarrollo e implementación

## Monitoreo y procesos

El monitoreo usa psutil y, para los procesos, una única llamada a `NtQuerySystemInformation`, concepto tomado de System Informer, que redujo la lectura de 3,4 s a menos de 0,05 s. Las firmas digitales se verifican con `Get-AuthenticodeSignature`, que también valida binarios firmados por catálogo.

Figura: docs/capturas/05_detalle_proceso.png | Explicación de un proceso | Los datos comprobados y las conclusiones estimadas se distinguen con etiquetas.

## Auditoría de seguridad

La auditoría lee el Registro y consulta PowerShell en modo de solo lectura. Cada hallazgo se estructura en ocho puntos: qué es, dónde está, por qué requiere atención, evidencia, información que falta, consecuencias posibles, qué hacer y qué no se recomienda. Solo Microsoft Defender puede producir el estado «amenaza detectada».

## Analizador de scripts

El analizador conserva el catálogo original de 24 reglas, añade 19 reglas para PowerShell y CMD, normaliza la ofuscación simple, decodifica Base64, asocia cada hallazgo a técnicas de MITRE ATT&CK 20.1 y explica cada línea del script.

## Inteligencia artificial integrada

ScriptLens integra dos formas de inteligencia artificial con funciones diferentes. El **motor analítico** mide, aplica reglas y clasifica: la regresión logística balanceada estima el riesgo de un script y se combina con las reglas en una política híbrida que marca como sensible un script si lo indican las reglas o si el modelo asigna una probabilidad de al menos 0,30. El **asistente** explica: un enrutador determinista consulta herramientas de solo lectura y el modelo Qwen3 4B Instruct redacta la respuesta con esos datos. Cada cifra de la respuesta se verifica; las que no aparecen en los datos se muestran como «no verificadas».

## Acciones supervisadas y seguridad del sistema

Las acciones usan confirmación en dos pasos con un token de un solo uso, revalidan la identidad del proceso y quedan registradas con mediciones antes y después. Los procesos críticos y de seguridad no pueden finalizarse, y ScriptLens nunca desactiva el antivirus, el firewall ni las actualizaciones. La limpieza de temporales solo actúa dentro de la carpeta temporal del usuario y rechaza rutas vacías, relativas, personales o del sistema.

## Distribución

El motor se empaqueta con PyInstaller y la aplicación se distribuye en un instalador NSIS por usuario, en español, con la identidad del proyecto. La versión v0.1.0 se publicó en GitHub Releases junto con su huella SHA-256; la v0.1.1 rediseñó la identidad gráfica del instalador.

# Resultados

## Funcionalidades implementadas

Tabla: Funcionalidades implementadas
| Módulo | Funcionalidad |
|---|---|
| Panel | CPU, núcleos, RAM, disco, red, tiempo encendido, consumo sostenido, gráfico de 5 minutos |
| Procesos | Búsqueda, filtros, árbol, firma, editor, conexiones, explicaciones |
| Optimizar | Recomendaciones medidas, cierre supervisado, temporales, desinstaladores, registro de acciones |
| Seguridad | Defender, firewall, inicio automático reversible, tareas, servicios, eventos |
| Scripts | Reglas, ATT&CK, flujo, desofuscación, explicación por línea, clasificación |
| Asistente | Preguntas en español con cifras verificadas, modo sin IA |
| Comparar | Diagnósticos guardados y comparación sin atribuir causas |
| Informes | PDF y HTML con marca de agua |

## Desempeño del clasificador

Tabla: Resultados del clasificador de scripts
| Conjunto | Método | F1 macro | Recall sensible |
|---|---|---|---|
| Sintético (180, validación cruzada de 5 pliegues) | Reglas | 1,000 | 1,000 |
| Sintético (180, validación cruzada de 5 pliegues) | Regresión logística | 0,955 | 0,917 |
| Sintético (180, validación cruzada de 5 pliegues) | Política híbrida | 0,966 | 1,000 |
| Realista independiente (18) | Reglas | 1,000 | 1,000 |
| Realista independiente (18) | Regresión logística | 0,886 | 0,667 |
| Realista independiente (18) | Política híbrida | 1,000 | 1,000 |

## Desempeño del producto

Tabla: Mediciones del producto
| Medición | Resultado |
|---|---|
| Lectura de todos los procesos (≈ 345) | < 0,05 s (antes 3,4 s con psutil) |
| Análisis de un script típico / de 1 MB | 10 ms / 3,4–8,5 s según la carga del equipo |
| Auditoría de seguridad sin administrador | 3,4–10,6 s |
| Respuesta del asistente (Qwen3 4B Instruct, CPU) | 10–65 s |
| Respuesta con `qwen3:4b` (razonamiento) | 256 s |
| Memoria de la aplicación instalada | Motor 163 MB, contenedor 28 MB, WebView2 485 MB (tras un minuto) |
| Tamaño del instalador | 49,3 MB |
| Instalación silenciosa por usuario | 11,8–18,3 s (sin administrador) |
| Motor disponible tras abrir la aplicación | 6,5–12,2 s |
| Procesos con firma válida en el equipo de prueba | 331 de 338 verificados |

## Pruebas automatizadas y verificación del instalador

Las 135 pruebas automatizadas se aprobaron. La prueba de rendimiento del archivo de 5 MB falló una vez, con 17,5 s, mientras otro proceso saturaba el procesador, y se aprobó al repetirla con menos carga; el resultado se documenta porque muestra que el tiempo depende del equipo.

Tabla: Verificación del instalador final en Windows 11
| Caso | Resultado |
|---|---|
| Instalación desde una sesión sin privilegios de administrador | Aprobado |
| Apertura desde el menú Inicio y conexión del motor | Aprobado |
| Motor accesible solo desde 127.0.0.1 | Aprobado |
| Segunda apertura: una sola aplicación y un solo motor | Aprobado |
| Cierre forzado: el motor termina en 1–1,6 s | Aprobado |
| Desinstalación conservando historial e informes | Aprobado |
| Descarga pública desde GitHub Releases con huella coincidente | Aprobado |

## Asistente

Las diez preguntas de referencia se respondieron con herramientas de datos medidos, con Ollama activo y en modo sin IA. Con Ollama, las respuestas tardaron entre 10 y 65 s; sin IA, fueron inmediatas. En una consulta real, la verificación de cifras detectó que el modelo afirmó «más del 70 % de la RAM» sin respaldo en los datos y la marcó como no verificada.

Figura: docs/capturas/12_asistente_ia.png | Respuesta del asistente | La respuesta indica la evidencia usada y si sus cifras se verificaron.

## Defectos encontrados y corregidos

Tabla: Defectos detectados al probar el producto instalado
| Defecto | Corrección |
|---|---|
| El motor empaquetado no comunicaba su puerto a la aplicación | Empaquetado en modo consola con ventana oculta y respaldo por el descriptor heredado |
| La limpieza podía actuar fuera de la carpeta temporal si `TEMP` estaba vacía | Validación de la ruta en vista previa y ejecución; no se siguen uniones NTFS |
| Informes fuera de la carpeta Documentos cuando OneDrive la redirige | Carpetas obtenidas de Windows con `SHGetKnownFolderPath` |
| El asistente tomaba «esta alerta» como nombre de proceso | Nueva intención «alerta» y lista de palabras excluidas |
| Diálogos de confirmación descentrados | Renderizado en un portal sobre toda la ventana |

# Discusión

## Interpretación de los resultados

El F1 perfecto de las reglas en el corpus sintético es circular, porque ese corpus se generó con los mismos comandos que buscan las reglas; por eso el conjunto realista es la referencia principal. En él, el modelo estadístico aislado dejó pasar dos scripts sensibles: uno que crea una cuenta y comparte el disco, y otro ofuscado. La política híbrida los recuperó sin aumentar los falsos positivos, lo que confirma la decisión de diseño de la propuesta original. Antes de una corrección introducida tras el análisis de errores, la regla P01 contaba la simple lectura de la clave Run como persistencia y producía un 43,3 % de falsos positivos en scripts de consulta; tras corregirla, la tasa fue de 0 %. El conjunto realista es pequeño y tiene un único etiquetador, por lo que las cifras deben tomarse como indicios y no como desempeño general.

Los defectos de la tabla anterior no aparecían en el entorno de desarrollo y solo se manifestaron con el producto empaquetado o en un equipo con carpetas redirigidas a OneDrive. Esto indica que las pruebas automatizadas, aunque necesarias, no sustituyen la verificación del producto instalado en condiciones reales.

## Comparación con herramientas existentes

A diferencia del Administrador de tareas y de System Informer, ScriptLens explica cada proceso y separa lo comprobado de lo estimado. A diferencia de osquery, no instala un servicio permanente y está dirigido a usuarios no técnicos. A diferencia de Microsoft Defender, no pretende detectar malware, sino explicar el riesgo de scripts y configuraciones; cuando Defender registra una detección, ScriptLens la muestra como la única fuente de «amenaza detectada». Su aporte distintivo es la combinación de mediciones verificadas, análisis de scripts evaluado y un asistente local cuyas cifras se comprueban.

## Beneficios para los usuarios

El usuario obtiene respuestas comprensibles a preguntas habituales, sabe qué programas puede cerrar sin afectar Windows, revisa qué se ejecuta al iniciar sesión, comprende un script antes de ejecutarlo y puede comparar su equipo antes y después de un cambio. Todo ocurre sin enviar datos a Internet y sin acciones automáticas.

## Limitaciones

El clasificador se entrenó con datos sintéticos y el conjunto realista es pequeño y con un solo etiquetador. El análisis estático no observa el código que se descarga o construye al ejecutarse. El asistente depende de los recursos del equipo y puede tardar hasta un minuto en un portátil sin tarjeta gráfica. Algunos datos, como el historial de amenazas de Defender, pueden requerir permisos de administrador. El instalador no tiene firma de código comercial y Windows SmartScreen muestra un aviso. Solo se probó en Windows 11; Windows 10 y equipos con 4 GB de RAM no se verificaron. La temperatura del hardware no está disponible.

# Conclusiones

La respuesta a la pregunta de investigación es afirmativa dentro de los límites medidos: la combinación de mediciones, reglas, aprendizaje supervisado y un modelo de lenguaje verificado permitió explicar el estado del equipo y el riesgo de los scripts sin enviar datos fuera del equipo ni ejecutar acciones sin consentimiento.

En relación con los objetivos específicos, se midió el equipo en tiempo real distinguiendo el consumo sostenido; se explicaron los procesos con datos comprobados; la auditoría funcionó sin privilegios; el clasificador se evaluó frente al baseline y mostró que el modelo aislado no basta para la clase peligrosa, por lo que la política híbrida es necesaria; la verificación de cifras resultó una salvaguarda práctica frente a la alucinación; y la aplicación se distribuyó en un instalador verificado y publicado que no requiere herramientas de desarrollo.

# Recomendaciones

Ampliar el conjunto realista con scripts autorizados y dos etiquetadores para calcular el kappa de Cohen; firmar el instalador con un certificado de código; realizar pruebas de usabilidad con personas sin formación técnica; y verificar la aplicación en Windows 10 y en equipos con 4 GB de RAM.

Como trabajo futuro se propone incorporar la detección de anomalías no supervisada planteada en RecuperaSO IA, ampliar el catálogo de reglas con el análisis del árbol sintáctico de PowerShell, ofrecer el paquete en WinGet, agregar modelos más pequeños con aceleración por hardware y traducir la interfaz a otros idiomas.

[[SALTO]]

# Referencias

[[REFERENCIAS]]

Bohannon, D., & Holmes, L. (2017). *Revoke-Obfuscation: PowerShell obfuscation detection framework* [Computer software]. GitHub. https://github.com/danielbohannon/Revoke-Obfuscation

Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement, 20*(1), 37–46. https://doi.org/10.1177/001316446002000104

Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023). Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection. En *Proceedings of the 16th ACM Workshop on Artificial Intelligence and Security* (pp. 79–90). ACM. https://doi.org/10.1145/3605764.3623985

Hendler, D., Kels, S., & Rubin, A. (2018). Detecting malicious PowerShell commands using deep neural networks. En *Proceedings of the 2018 Asia Conference on Computer and Communications Security* (pp. 187–197). ACM. https://doi.org/10.1145/3196494.3196511

Hosmer, D. W., Lemeshow, S., & Sturdivant, R. X. (2013). *Applied logistic regression* (3rd ed.). Wiley. https://doi.org/10.1002/9781118548387

Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y. J., Madotto, A., & Fung, P. (2023). Survey of hallucination in natural language generation. *ACM Computing Surveys, 55*(12), Artículo 248. https://doi.org/10.1145/3571730

King, G., & Zeng, L. (2001). Logistic regression in rare events data. *Political Analysis, 9*(2), 137–163. https://doi.org/10.1093/oxfordjournals.pan.a004868

Kohavi, R. (1995). A study of cross-validation and bootstrap for accuracy estimation and model selection. En *Proceedings of the 14th International Joint Conference on Artificial Intelligence* (Vol. 2, pp. 1137–1143). Morgan Kaufmann.

MITRE. (2026). *ATT&CK STIX data* (Versión 20.1) [Conjunto de datos]. GitHub. https://github.com/mitre-attack/attack-stix-data

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html

Qwen Team. (2025). *Qwen3 technical report* (arXiv:2505.09388). arXiv. https://doi.org/10.48550/arXiv.2505.09388

Salton, G., & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval. *Information Processing & Management, 24*(5), 513–523. https://doi.org/10.1016/0306-4573(88)90021-0

Strom, B. E., Applebaum, A., Miller, D. P., Nickels, K. C., Pennington, A. G., & Thomas, C. B. (2018). *MITRE ATT&CK: Design and philosophy* (Technical Report MP180360). The MITRE Corporation. https://attack.mitre.org/docs/ATTACK_Design_and_Philosophy_March_2020.pdf

Yosifovich, P., Ionescu, A., Russinovich, M. E., & Solomon, D. A. (2017). *Windows internals, part 1* (7th ed.). Microsoft Press.

[[SALTO]]

# Anexos

## Anexo A. Capturas del producto

Figura: docs/capturas/09_seguridad.png | Centro de seguridad | Estado de Defender y del firewall y servicios de terceros con su firma, en el equipo de pruebas.

Figura: docs/capturas/10_analisis_script.png | Análisis de un script de demostración | El script contiene persistencia, ocultamiento y borrado; nunca se ejecutó.

Figura: docs/capturas/08_confirmacion_accion.png | Confirmación de una acción supervisada | El botón con el foco inicial es «Cancelar».

Figura: docs/capturas/13_comparar.png | Comparación de diagnósticos | Diferencias medidas entre dos momentos.

## Anexo B. Repositorio y evidencias

El código fuente, la bitácora con los hashes de los commits, el informe de evaluación del clasificador, la matriz de compatibilidad y las capturas están en https://github.com/JorgeGutho21/ScriptLens. El instalador y su huella SHA-256 se publican en https://github.com/JorgeGutho21/ScriptLens/releases (versión vigente: v0.1.1).
