# Política de privacidad de ScriptLens IA

Versión 0.2.0 · 18 de noviembre de 2026

## Principio

ScriptLens IA analiza el equipo **localmente**. No existe ningún servidor de ScriptLens y la aplicación no envía a Internet contraseñas, tokens, datos personales, contenidos de archivos, listas de procesos, registros del sistema, scripts analizados ni conversaciones.

## Qué información se procesa y dónde se guarda

| Información | Para qué | Dónde | Cuánto tiempo |
|---|---|---|---|
| Mediciones de CPU, RAM, disco, red y procesos | Panel, procesos, asistente | Solo en memoria | 10 minutos (ventana móvil); se borra al cerrar |
| Diagnósticos guardados | «Comparar mi PC» | `%LOCALAPPDATA%\io.github.jorgegutho21.scriptlens\scriptlens.db` | Hasta que el usuario los borre |
| Conversaciones con el asistente | Historial del chat | Misma base de datos | Hasta que el usuario las borre (puede desactivarse) |
| Registro de acciones | Auditoría de lo realizado | Misma base de datos | Hasta que el usuario lo borre |
| Resultado de la auditoría de seguridad | Centro de seguridad | Solo en memoria | Hasta cerrar la aplicación |
| Último script analizado | Explicación por el asistente | Solo en memoria | Hasta analizar otro o cerrar |
| Informes | Documentos del usuario | `Documentos\ScriptLens IA\Informes` | Hasta que el usuario los borre |
| Preferencias de interfaz | Tema, tamaño de letra, modo | Almacenamiento local de la ventana | Hasta desinstalar |
| Estadísticas de rendimiento (resúmenes por minuto y hora) | «Estadísticas de mi PC» | Misma base de datos | Minutos: 7 días; horas: 90 días por defecto (configurable de 7 a 365); se pueden pausar y borrar |
| Contador de inactividad (segundos sin teclado ni ratón) | Distinguir uso activo de inactivo | Misma base de datos, como segundos activos por minuto | Igual que las estadísticas. **No** se registran teclas, textos, clics ni ventanas |
| Aplicaciones en primer plano (solo nombre del ejecutable) | «Aplicaciones más utilizadas» | Misma base de datos | **Desactivado por defecto**; requiere consentimiento; se puede pausar y borrar. No se guardan títulos de ventana ni direcciones web |
| Arranques y apagados (registro de eventos de Windows) | Horas de encendido | Misma base de datos | Igual que las estadísticas |
| Dispositivos vinculados al acceso remoto | Saber quién puede consultar la PC | Misma base de datos: nombre, IP, fechas y **hash** del token | Hasta su caducidad (12 h navegador, 30 días consola), revocación o «Desactivar» |
| Equipos vinculados en «Mis computadoras» | Consultar otras PC | Misma base de datos; el token, cifrado con DPAPI de Windows | Hasta desvincular |
| Historial de otras PC | Gráficas de la consola | Misma base de datos | 7 días |
| Certificado y clave del acceso remoto | Cifrar la conexión en la red local | `…\scriptlens\remote\` en la carpeta de datos | Hasta desinstalar |
| Resultado de la auditoría de 30 controles | Pantalla de auditoría e informes | Solo en memoria (y en el informe si se genera) | Hasta cerrar la aplicación |

Ajustes muestra las rutas reales y permite desactivar el historial y las conversaciones y borrar diagnósticos, conversaciones y registro de acciones.

## Conexiones de red

- **Acceso remoto** (puerto 8765 por defecto): **apagado** al abrir ScriptLens. Solo cuando el usuario lo activa, atiende en las direcciones IPv4 privadas del equipo, por HTTPS, y solo a dispositivos autorizados con código y aprobación. Comparte únicamente mediciones de rendimiento, el resumen de seguridad y estadísticas resumidas; cada categoría opcional se puede desactivar. No abre puertos en el router.
- **Mis computadoras**: solo se conecta a las PC que el usuario vinculó, dentro de la red local.

- **Ollama** (`127.0.0.1:11434`): local; los datos no salen del equipo.
- **Descarga de un modelo de IA**: solo si el usuario la autoriza explícitamente; la realiza Ollama desde su registro oficial.
- **Buscar actualizaciones**: solo al pulsar el botón; consulta `api.github.com` con un agente genérico y sin datos del equipo. Nunca descarga ni instala nada.
- **Enlaces externos**: solo el repositorio oficial y la página de descarga de Ollama, abiertos en el navegador del usuario.

## Lo que ScriptLens no hace

No instala servicios de vigilancia, no se ejecuta en segundo plano al cerrar la ventana, no ejecuta los scripts analizados, no desactiva el antivirus, el firewall ni las actualizaciones y no permite que la IA ejecute acciones.

## Eliminar todos los datos

1. Desinstale ScriptLens IA desde Configuración → Aplicaciones.
2. Borre la carpeta `%LOCALAPPDATA%\io.github.jorgegutho21.scriptlens` y, si lo desea, `Documentos\ScriptLens IA`.
3. Para eliminar el modelo de IA: `ollama rm qwen3:4b-instruct` en PowerShell.
