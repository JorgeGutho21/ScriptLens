[[TOC]]

# 1. Qué es ScriptLens IA

ScriptLens IA es un programa que le ayuda a entender qué está pasando en su computador con Windows. Le dice, con palabras sencillas, si el equipo funciona con normalidad, qué programas usan más recursos, qué se abre solo al encender el equipo y si hay algo que convenga revisar. También puede leer un script (un archivo `.bat`, `.cmd` o `.ps1`) y explicarle qué haría **sin ejecutarlo**.

Todo el análisis ocurre en su propio computador. ScriptLens no envía sus datos a Internet.

# 2. Para qué sirve

- Saber por qué el computador está lento.
- Descubrir qué programa consume más memoria o procesador.
- Revisar qué programas se inician con Windows y desactivar los que no necesita.
- Comprobar que el antivirus y el firewall estén activos.
- Entender un script antes de ejecutarlo.
- Comparar el computador antes y después de un cambio.
- Guardar un informe en PDF.

# 3. Dónde descargarlo

1. Abra el navegador y entre a **github.com/JorgeGutho21/ScriptLens**.
2. En la parte derecha, pulse **Releases**.
3. En la versión marcada **Latest**, abra **Assets** y descargue `ScriptLens-IA_0.1.0_x64-setup.exe` y su huella `ScriptLens-IA_0.1.0_x64-setup.exe.sha256`.
4. Compruebe que la huella coincide siguiendo la *Guía de instalación de ScriptLens IA* (apartado 2.4).

Descargue ScriptLens solo desde esa dirección.

# 4. Cómo instalarlo

1. Abra la carpeta Descargas y haga doble clic en el instalador.
2. Windows puede mostrar «Windows protegió su PC» porque el instalador no tiene una firma de código comercial. Ese aviso es una protección útil: continúe solo si descargó el archivo de la página oficial y la huella coincide. En ese caso pulse **Más información** y luego **Ejecutar de todas formas**. Si tiene dudas, no continúe.
3. Siga los pasos del asistente de instalación: **Siguiente**, acepte la licencia e **Instalar**.

Figura: docs/capturas/00_instalador_bienvenida.png | Primera pantalla del instalador | No necesita ser administrador del equipo para instalar ScriptLens.

# 5. Cómo abrirlo

Abra el menú Inicio y busque **ScriptLens IA**, o use el acceso directo del escritorio. La primera vez puede tardar hasta 30 segundos en iniciar, porque el antivirus revisa los archivos nuevos; después tarda unos 10 segundos.

La primera vez aparece una guía de bienvenida de ocho pasos. Léala con calma: explica qué analiza el programa, qué datos se quedan en su equipo y qué acciones piden confirmación. Puede volver a verla desde **Ajustes → Guía de bienvenida**.

Figura: docs/capturas/01_bienvenida.png | Guía de bienvenida | Pulse «Siguiente» para avanzar u «Omitir» para cerrarla.

# 6. Qué significa cada pantalla

Tabla: Secciones de ScriptLens IA
| Sección | Para qué sirve |
|---|---|
| Panel general | Resumen del estado del equipo en tiempo real |
| Procesos | Lista de programas en ejecución y explicación de cada uno |
| Optimizar | Recomendaciones, limpieza de temporales y programas instalados |
| Seguridad | Antivirus, firewall, inicio automático, tareas y eventos |
| Analizar scripts | Explicación de un script sin ejecutarlo |
| Asistente IA | Preguntas en español sobre su computador |
| Comparar mi PC | Comparar dos momentos |
| Informes | Crear informes PDF o HTML |
| Ajustes | Apariencia, accesibilidad y privacidad |
| Acerca de | Versión, autor y actualizaciones |

En la parte superior verá **Sencillo** y **Avanzado**. El modo sencillo muestra solo lo esencial; el avanzado añade detalles técnicos como el uso por núcleo, el identificador de cada proceso y la firma digital.

Las palabras subrayadas con puntos, como **Memoria RAM**, tienen una explicación: púlselas para leerla.

# 7. Cómo analizar el computador

El análisis empieza solo al abrir el programa. En el **Panel general** espere unos 20 segundos: al principio verá «Recopilando mediciones», porque ScriptLens necesita varias mediciones para distinguir un consumo continuo de un pico momentáneo.

Figura: docs/capturas/14_recopilando_mediciones.png | Panel recién abierto | El mensaje «Información insuficiente» desaparece tras unos segundos.

Figura: docs/capturas/02_panel_general.png | Panel general con el equipo funcionando con normalidad | El recuadro «Qué está pasando» resume la situación.

# 8. Cómo interpretar CPU y RAM

- **CPU (procesador):** es la parte del computador que ejecuta los programas. Si está casi al 100 % durante mucho tiempo, todo va más lento.
- **Memoria RAM:** almacena temporalmente los datos de los programas abiertos. Si está muy ocupada, el computador responde más lentamente.

Los círculos se ven **azules** (o morados para la RAM) cuando el uso es normal, **amarillos** cuando es elevado (70 % o más) y **rojos** cuando es muy alto (88 % o más). Debajo del círculo de CPU aparece el promedio del último minuto, que es más importante que el valor de un instante.

# 9. Cómo identificar procesos

En **Procesos** verá todos los programas en ejecución. Puede buscar por nombre, filtrar por tipo (aplicaciones abiertas, segundo plano, servicios, Windows) y ordenar por consumo.

Figura: docs/capturas/04_procesos.png | Lista de procesos | La columna Firma indica si el programa está firmado por su editor.

Pulse un proceso para ver su ficha: qué hace, por qué está en ejecución, cuánto consume, si es necesario para Windows, si puede cerrarlo, qué pasa si lo cierra y si tiene características sospechosas. Cada respuesta tiene una etiqueta: **Comprobado** (dato medido o verificado) o **Estimado** (conclusión de ScriptLens).

Figura: docs/capturas/05_detalle_proceso.png | Ficha de un proceso | Los componentes esenciales de Windows no se pueden finalizar desde ScriptLens.

La vista **Árbol** muestra qué programa abrió a cuál.

# 10. Cómo preguntar a la IA

1. Abra **Asistente IA**.
2. Pulse una de las preguntas sugeridas o escriba la suya, por ejemplo: «¿Qué programa consume más RAM?».
3. Espere la respuesta (entre 10 y 60 segundos con la IA local).

Debajo de cada respuesta verá si las cifras fueron **verificadas** con los datos medidos. Si aparece «Cifras no verificadas», tome esos números con precaución. Pulse **Evidencia usada** para ver los datos exactos que se consultaron.

Figura: docs/capturas/12_asistente_ia.png | Conversación con el asistente | El asistente explica, pero nunca ejecuta acciones.

**Para activar la IA local:** instale Ollama desde ollama.com/download, ábralo y, en la pantalla del asistente, pulse **Descargar** junto a «Qwen3 4B Instruct» (unos 2,5 GB). Sin Ollama, el asistente igualmente responde con los datos medidos, aunque con frases más simples.

# 11. Cómo interpretar riesgos

Tabla: Estados que muestra ScriptLens
| Estado | Qué significa |
|---|---|
| Normal según la evidencia | No se observaron señales de riesgo |
| Informativo | Dato útil que no requiere acción |
| Consumo elevado | Usa muchos recursos; no significa que sea peligroso |
| Requiere revisión | Algo inusual que conviene comprobar |
| Actividad sospechosa | Varias señales juntas; investigue antes de actuar |
| Amenaza detectada | Solo cuando Microsoft Defender detectó algo |
| Información insuficiente | Faltan datos o permisos para concluir |

Un programa no es peligroso solo porque no lo conozca, no tenga firma o use mucha memoria. ScriptLens no es un antivirus.

# 12. Cómo revisar programas de inicio

1. Abra **Seguridad** y pulse **Revisar ahora** (o **Volver a revisar**).
2. Abra la pestaña **Inicio automático**.
3. Cada programa tiene un interruptor. Desactivar uno solo evita que se abra al encender el equipo: **no lo desinstala** y puede volver a activarlo cuando quiera.

Figura: docs/capturas/18_inicio_automatico.png | Programas que inician con Windows | Las entradas de todos los usuarios requieren permisos de administrador y no se pueden cambiar desde aquí.

Figura: docs/capturas/09_seguridad.png | Hallazgos de seguridad | Cada hallazgo explica qué se encontró, dónde, por qué, qué puede hacer y qué no se recomienda.

# 13. Cómo realizar acciones supervisadas

Toda acción que cambia el equipo pide confirmación. El diálogo explica qué va a pasar y sus advertencias; el botón seleccionado al principio es **Cancelar**, para evitar confirmaciones por accidente. La confirmación caduca a los 60 segundos.

Figura: docs/capturas/08_confirmacion_accion.png | Confirmación antes de limpiar archivos temporales | Solo se borran temporales de su usuario con más de siete días; nunca documentos ni la carpeta Descargas.

- **Solicitar cierre:** como pulsar la X de la ventana; el programa puede pedirle guardar.
- **Finalizar:** cierra el programa de inmediato; se pierde lo que no esté guardado. Úselo solo si «Solicitar cierre» no funciona.
- **Desinstalar:** abre el desinstalador oficial del programa.

En **Optimizar → Registro de acciones** verá todo lo realizado, con la memoria antes y después.

Figura: docs/capturas/07_optimizar.png | Pantalla Optimizar | Las recomendaciones se basan en mediciones reales.

# 14. Cómo analizar scripts

1. Abra **Analizar scripts**.
2. Arrastre el archivo a la ventana o pulse **Seleccionar archivo**. También puede probar los ejemplos incluidos.
3. ScriptLens muestra tres resultados independientes: la clasificación estadística, la decisión de las reglas y la severidad.

Figura: docs/capturas/10_analisis_script.png | Resultado del análisis | «Sensible» indica operaciones como persistencia, borrado u ocultamiento.

Más abajo verá las técnicas de MITRE ATT&CK detectadas y la explicación de cada línea, con un borde verde (consulta), amarillo (modificación) o rojo (sensible). El porcentaje de la clase «sensible» indica parecido con los ejemplos de entrenamiento, **no** la probabilidad de que el archivo sea un virus.

Figura: docs/capturas/11_script_lineas_attack.png | Explicación línea por línea | El script nunca se ejecuta.

# 15. Cómo generar informes

1. Abra **Informes**.
2. Elija si incluye la revisión de seguridad y, si quiere, una comparación con un diagnóstico guardado.
3. Pulse **Crear PDF** o **Crear HTML**. El informe se abre al terminar y se guarda en `Documentos\ScriptLens IA\Informes`.

Figura: docs/capturas/15_informes.png | Pantalla de informes | Los informes incluyen una marca de agua discreta con el nombre del proyecto y del autor.

# 16. Cómo revisar el historial

En **Comparar mi PC**:

1. Escriba un nombre, por ejemplo «Antes de cerrar programas», y pulse **Guardar diagnóstico**.
2. Haga el cambio que quiera evaluar.
3. Elija el diagnóstico guardado, deje «El estado actual (medir ahora)» y pulse **Comparar**.

Figura: docs/capturas/13_comparar.png | Comparación de dos momentos | ScriptLens describe lo que cambió, pero no afirma que una acción lo haya causado.

Puede borrar diagnósticos con el icono de papelera, o todos a la vez en **Ajustes → Privacidad**.

# 17. Cómo actualizar el programa

Abra **Acerca de** y pulse **Buscar actualizaciones**. ScriptLens consulta GitHub solo cuando usted lo pide, no envía datos de su equipo y nunca instala nada por sí mismo. Si hay una versión nueva, descárguela desde la página oficial e instálela encima de la actual.

Figura: docs/capturas/17_acerca_de.png | Pantalla Acerca de en modo claro | Muestra la versión, el autor y el repositorio oficial.

# 18. Cómo solucionar errores

Tabla: Problemas frecuentes y soluciones
| Problema | Solución |
|---|---|
| Se queda en «Iniciando el motor de análisis» | Espere 30 segundos la primera vez; si continúa, cierre y vuelva a abrir |
| «Motor desconectado» en la barra superior | Cierre ScriptLens y ábralo de nuevo |
| La firma dice «Verificando…» | Espere un minuto; se verifican cientos de programas en segundo plano |
| El asistente responde «sin IA» | Abra Ollama y descargue el modelo desde la pantalla del asistente |
| «Información insuficiente» en seguridad | Algunos datos requieren permisos de administrador |
| Una sección muestra «Esta sección tuvo un problema» | Pulse «Reintentar» o cambie de sección |

# 19. Cómo desinstalarlo

Abra **Configuración → Aplicaciones → Aplicaciones instaladas**, busque **ScriptLens IA** y pulse **Desinstalar**. Sus diagnósticos e informes se conservan; para borrarlos, use **Ajustes → Privacidad** antes de desinstalar o elimine la carpeta `Documentos\ScriptLens IA`.

Figura: docs/capturas/20_ajustes_privacidad.png | Ajustes de privacidad | Muestra dónde se guardan sus datos y permite borrarlos.

# 20. Qué operaciones deben evitarse

- No finalice procesos que no conoce sin leer antes su ficha.
- No desactive el antivirus, el firewall ni las actualizaciones para «acelerar» el equipo.
- No ejecute un script que ScriptLens marca como sensible si no sabe de dónde viene.
- No borre archivos a ciegas: primero desactive la entrada de inicio y compruebe que nada deja de funcionar.
- No descargue «limpiadores» o «aceleradores» de sitios desconocidos.
- No instale ScriptLens desde páginas distintas del repositorio oficial.
