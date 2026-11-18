# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versionado semántico.

## [0.2.0] — 2026-11-18

### Añadido
- **Acceso remoto de solo lectura** («Ver mi PC desde otro dispositivo»): servidor HTTPS en la red local, apagado por defecto, con certificado propio, código temporal, frase de verificación, aprobación en la PC, sesiones revocables y página adaptada a celulares.
- **Mis computadoras**: consola para vincular y supervisar varias PC con ScriptLens (estado conectado/desconectado, última lectura, CPU, RAM, disco, tiempo encendido, alertas, historial de 24 h, comparación y desvinculación).
- **Estadísticas de mi PC**: historial por hora, día y semana; tiempo desde el arranque, sesión y uso activo por separado; sesiones de uso; horarios de actividad; procesos y (con consentimiento) aplicaciones más usadas; alertas por consumo sostenido; informes HTML y CSV; pausa, borrado y retención.
- **Auditoría de Windows — 30 controles** del taller, de solo lectura, con evidencia, explicación, recomendación e informes PDF y HTML.
- **Asistente más rápido**: respuesta inmediata con datos medidos, modos IA rápida (Qwen3 1.7B) e IA detallada (Qwen3 4B Instruct), cancelación y estadísticas de cada respuesta. Mediana medida: de 32,7 s a 3,5 s en modo Automático.
- Guía «Conectar y supervisar computadoras con ScriptLens IA» y documento de arquitectura de la versión 0.2.

### Cambiado
- Navegación agrupada en «Mi PC», «Seguridad», «Conectar» y «Herramientas»; «Ajustes» pasa a llamarse «Configuración».
- Guía de bienvenida con las funciones nuevas.
- CI: pasos explícitos para las pruebas de seguridad remota, auditoría y estadísticas, oxlint y sintaxis de la vista remota.

### Seguridad
- La API local (Tauri, 127.0.0.1 y token interno) no cambia. Ninguna ruta de acciones, ajustes, asistente o archivos existe en el servidor remoto.

## [0.1.1] — 2026-11-15

### Cambiado
- **Instalador:** barra lateral y encabezado rediseñados a partir del logotipo vectorial, con los créditos del autor, dibujados al tamaño exacto que el asistente usa a escala 125 % para que el texto se vea nítido.
- **Documentación:** informe ExpoSoftware reorganizado en orden APA; guía de instalación con las siete pantallas reales del asistente; instrucciones corregidas según los botones reales («Siguiente» en la carpeta de instalación).

El motor y la interfaz no cambian respecto a 0.1.0, salvo el número de versión.

## [0.1.0] — 2026-11-15

### Añadido
- **Monitoreo:** CPU total y por núcleo, RAM, paginación, disco, red y tiempo encendido con psutil; diagnóstico de consumo sostenido.
- **Procesos:** lectura nativa con `NtQuerySystemInformation`, rutas, firmas Authenticode por lotes (incluye catálogos), base de conocimiento de procesos de Windows, árbol padre-hijo, explicaciones comprobadas/estimadas.
- **Historial:** SQLite con migraciones, diagnósticos guardados, comparación sin atribución causal, controles de privacidad.
- **Seguridad:** Defender, Centro de seguridad, firewall, inicio automático, tareas, servicios, eventos, cuentas y plan de energía; hallazgos con ocho puntos.
- **Scripts:** catálogo original de 24 reglas + 19 de ampliación, ATT&CK 20.1, desofuscación estática, flujo, explicación por línea, regresión logística balanceada, baseline, política híbrida y evaluación reproducible.
- **Acciones supervisadas:** confirmación con token de un solo uso, revalidación de identidad, procesos protegidos, inicio automático reversible, limpieza acotada de temporales, desinstaladores oficiales, auditoría con mediciones antes/después.
- **Asistente IA:** Ollama + Qwen3 4B Instruct, herramientas de solo lectura, defensa ante inyección de instrucciones, verificación de cifras, modo sin IA, descarga de modelos con autorización.
- **Informes:** PDF y HTML con marca de agua discreta.
- **Distribución:** motor empaquetado con PyInstaller, instalador NSIS por usuario, instancia única, SHA-256, comprobación de actualizaciones bajo demanda, flujo de GitHub Actions que genera el instalador como artefacto.
- **Interfaz:** modo sencillo/avanzado, claro/oscuro, tamaño de texto, reducción de animaciones, glosario, asistente de primera ejecución, elemento 3D con Three.js en carga diferida, límite de errores por pantalla.

### Corregido
- La regla P01 contaba la lectura de la clave Run como persistencia.
- Windows PowerShell 5.1 no cargaba `Get-AuthenticodeSignature` al heredar `PSModulePath` de PowerShell 7.
- La pantalla del asistente quedaba en blanco porque `scrollIntoView` devuelve una Promise en WebView2.
- Interruptores dibujados como activados en celdas alineadas a la derecha.
- Motor huérfano al cerrar la aplicación; instancias duplicadas.
- Análisis de scripts de 1 MB: de 10,4 s a 3,4 s.
- **(P1)** El motor empaquetado en modo ventana no podía anunciar su puerto a la aplicación: se empaqueta en modo consola (ventana oculta) y, como defensa, escribe en el descriptor heredado si falta `sys.stdout`.
- **(P1)** Con `TEMP` vacía, la limpieza de temporales actuaba sobre el directorio de trabajo: se rechazan rutas ausentes, relativas, personales, del sistema o enlazadas, en la vista previa y otra vez al ejecutar, y no se entra en uniones NTFS.
- Los informes no llegaban a la carpeta Documentos visible cuando OneDrive la redirige.
- El asistente tomaba «esta alerta» como nombre de proceso, no consultaba los elementos en revisión ante «¿qué proceso requiere investigación?» y daba un ranking de CPU nulo recién iniciado.
- Acerca de y el README indicaban una carpeta de datos incorrecta.

### Cambiado
- El instalador se publica como `ScriptLens-IA_<versión>_x64-setup.exe` (sin espacios) con su `.sha256`.
- README reescrito como página de instalación; nueva *Guía de instalación* (DOCX y PDF) y matriz de compatibilidad.
- Acerca de muestra la identidad oficial, la información técnica y las rutas reales; la tabla de procesos se adapta a ventanas estrechas; el asistente permite comprobar de nuevo Ollama.
