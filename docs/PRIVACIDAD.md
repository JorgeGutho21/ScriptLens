# Política de privacidad de ScriptLens IA

Versión 0.1.0 · 15 de noviembre de 2026

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

Ajustes muestra las rutas reales y permite desactivar el historial y las conversaciones y borrar diagnósticos, conversaciones y registro de acciones.

## Conexiones de red

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
