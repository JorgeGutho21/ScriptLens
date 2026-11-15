"""Base de conocimiento de procesos habituales de Windows.

Cada entrada describe qué hace el proceso y si cerrarlo afecta a Windows. La
coincidencia por nombre NO basta: un programa malicioso puede llamarse
«svchost.exe». Por eso cada entrada indica también la carpeta esperada; si el
ejecutable real está en otra ubicación, el análisis lo señala.

Fuentes: documentación de Microsoft Learn sobre componentes de Windows y
servicios del sistema (consultada el 2026-11-14).
"""

from __future__ import annotations

SYS32 = r"c:\windows\system32"

# critico: cerrarlo puede bloquear, cerrar sesión o reiniciar Windows (ScriptLens nunca lo finaliza)
# sistema: componente de Windows; cerrarlo puede afectar funciones pero no suele ser fatal
# seguridad: protección de Windows; nunca se debe cerrar
# aplicacion: programa de usuario conocido
KNOWN: dict[str, dict] = {
    "system": {"rol": "critico", "carpeta": None, "que": "Núcleo de Windows. Gestiona la memoria, los controladores y el hardware."},
    "system idle process": {"rol": "critico", "carpeta": None, "que": "No es un programa real: representa el tiempo en que el procesador está libre."},
    "registry": {"rol": "critico", "carpeta": None, "que": "Mantiene en memoria el Registro de Windows, la base de datos de configuración del sistema."},
    "memory compression": {"rol": "critico", "carpeta": None, "que": "Comprime datos en la RAM para que quepan más programas sin usar el disco. Su consumo de memoria es normal."},
    "secure system": {"rol": "critico", "carpeta": None, "que": "Entorno aislado de seguridad basada en virtualización de Windows."},
    "smss.exe": {"rol": "critico", "carpeta": SYS32, "que": "Administrador de sesiones: inicia las sesiones de Windows al arrancar."},
    "csrss.exe": {"rol": "critico", "carpeta": SYS32, "que": "Subsistema cliente-servidor: gestiona ventanas de consola y el apagado. Imprescindible."},
    "wininit.exe": {"rol": "critico", "carpeta": SYS32, "que": "Inicializa Windows y lanza los servicios básicos durante el arranque."},
    "winlogon.exe": {"rol": "critico", "carpeta": SYS32, "que": "Gestiona el inicio y cierre de sesión y la pantalla de bloqueo."},
    "services.exe": {"rol": "critico", "carpeta": SYS32, "que": "Administrador de servicios: inicia y detiene los servicios de Windows."},
    "lsass.exe": {"rol": "critico", "carpeta": SYS32, "que": "Autoridad de seguridad local: valida contraseñas e inicios de sesión."},
    "lsaiso.exe": {"rol": "critico", "carpeta": SYS32, "que": "Proceso aislado de credenciales (Credential Guard)."},
    "svchost.exe": {"rol": "sistema", "carpeta": SYS32, "que": "Contenedor de servicios de Windows. Es normal ver muchos a la vez; cada uno aloja uno o varios servicios."},
    "dwm.exe": {"rol": "critico", "carpeta": SYS32, "que": "Administrador de ventanas del escritorio: dibuja las ventanas y efectos visuales."},
    "fontdrvhost.exe": {"rol": "critico", "carpeta": SYS32, "que": "Controlador de fuentes en modo usuario."},
    "explorer.exe": {"rol": "sistema", "carpeta": r"c:\windows", "que": "Explorador de Windows: muestra el escritorio, la barra de tareas y las carpetas. Si se cierra, Windows suele reiniciarlo."},
    "sihost.exe": {"rol": "sistema", "carpeta": SYS32, "que": "Host de infraestructura del shell: centro de notificaciones y elementos del escritorio."},
    "taskhostw.exe": {"rol": "sistema", "carpeta": SYS32, "que": "Ejecuta tareas de Windows basadas en bibliotecas (DLL)."},
    "ctfmon.exe": {"rol": "sistema", "carpeta": SYS32, "que": "Gestiona la entrada de texto, el teclado táctil y el cambio de idioma de teclado."},
    "runtimebroker.exe": {"rol": "sistema", "carpeta": SYS32, "que": "Administra los permisos de las aplicaciones de la Microsoft Store."},
    "searchhost.exe": {"rol": "sistema", "carpeta": None, "que": "Búsqueda de Windows del menú Inicio."},
    "searchindexer.exe": {"rol": "sistema", "carpeta": SYS32, "que": "Indexa archivos para que las búsquedas sean rápidas. Puede usar disco y CPU tras instalar programas o copiar muchos archivos."},
    "startmenuexperiencehost.exe": {"rol": "sistema", "carpeta": None, "que": "Muestra el menú Inicio."},
    "shellexperiencehost.exe": {"rol": "sistema", "carpeta": None, "que": "Elementos visuales del shell: calendario, reloj y paneles emergentes."},
    "textinputhost.exe": {"rol": "sistema", "carpeta": None, "que": "Teclado en pantalla, emojis y entrada de texto."},
    "spoolsv.exe": {"rol": "sistema", "carpeta": SYS32, "que": "Cola de impresión: gestiona los trabajos enviados a impresoras."},
    "audiodg.exe": {"rol": "sistema", "carpeta": SYS32, "que": "Procesa el audio del equipo (efectos y mezcla de sonido)."},
    "conhost.exe": {"rol": "sistema", "carpeta": SYS32, "que": "Ventana de consola asociada a un programa de línea de comandos."},
    "dllhost.exe": {"rol": "sistema", "carpeta": SYS32, "que": "Ejecuta componentes COM de Windows (por ejemplo, miniaturas de imágenes)."},
    "wmiprvse.exe": {"rol": "sistema", "carpeta": r"c:\windows\system32\wbem", "que": "Proveedor de WMI: responde consultas de información del sistema (ScriptLens y otras herramientas pueden activarlo)."},
    "wudfhost.exe": {"rol": "sistema", "carpeta": SYS32, "que": "Aloja controladores de dispositivos en modo usuario (USB, sensores)."},
    "lockapp.exe": {"rol": "sistema", "carpeta": None, "que": "Pantalla de bloqueo de Windows."},
    "smartscreen.exe": {"rol": "seguridad", "carpeta": SYS32, "que": "Filtro SmartScreen: advierte sobre programas y sitios potencialmente peligrosos."},
    "msmpeng.exe": {"rol": "seguridad", "carpeta": None, "que": "Motor antimalware de Microsoft Defender. Puede usar mucha CPU durante análisis o al compilar/copiar muchos archivos; es normal."},
    "nissrv.exe": {"rol": "seguridad", "carpeta": None, "que": "Inspección de red de Microsoft Defender."},
    "mpdefendercoreservice.exe": {"rol": "seguridad", "carpeta": None, "que": "Servicio principal de Microsoft Defender."},
    "securityhealthservice.exe": {"rol": "seguridad", "carpeta": SYS32, "que": "Servicio de Seguridad de Windows que informa el estado de protección."},
    "securityhealthsystray.exe": {"rol": "seguridad", "carpeta": SYS32, "que": "Icono de Seguridad de Windows en la barra de tareas."},
    "msedgewebview2.exe": {"rol": "aplicacion", "carpeta": None, "que": "Motor web de Microsoft Edge que usan otras aplicaciones (incluida ScriptLens) para mostrar su interfaz."},
    "msedge.exe": {"rol": "aplicacion", "carpeta": None, "que": "Navegador Microsoft Edge. Cada pestaña y extensión puede ser un proceso separado."},
    "chrome.exe": {"rol": "aplicacion", "carpeta": None, "que": "Navegador Google Chrome. Cada pestaña y extensión puede ser un proceso separado."},
    "firefox.exe": {"rol": "aplicacion", "carpeta": None, "que": "Navegador Mozilla Firefox."},
    "onedrive.exe": {"rol": "aplicacion", "carpeta": None, "que": "Sincroniza sus archivos con OneDrive. Al cerrarlo se pausa la sincronización."},
    "teams.exe": {"rol": "aplicacion", "carpeta": None, "que": "Microsoft Teams."},
    "ms-teams.exe": {"rol": "aplicacion", "carpeta": None, "que": "Microsoft Teams."},
    "code.exe": {"rol": "aplicacion", "carpeta": None, "que": "Editor Visual Studio Code."},
    "winword.exe": {"rol": "aplicacion", "carpeta": None, "que": "Microsoft Word. Guarde sus documentos antes de cerrarlo."},
    "excel.exe": {"rol": "aplicacion", "carpeta": None, "que": "Microsoft Excel. Guarde sus libros antes de cerrarlo."},
    "powerpnt.exe": {"rol": "aplicacion", "carpeta": None, "que": "Microsoft PowerPoint. Guarde sus presentaciones antes de cerrarlo."},
    "spotify.exe": {"rol": "aplicacion", "carpeta": None, "que": "Reproductor de música Spotify."},
    "whatsapp.exe": {"rol": "aplicacion", "carpeta": None, "que": "Aplicación de mensajería WhatsApp."},
    "ollama.exe": {"rol": "aplicacion", "carpeta": None, "que": "Ollama: ejecuta modelos de inteligencia artificial en este equipo (lo usa el asistente de ScriptLens)."},
    "ollama app.exe": {"rol": "aplicacion", "carpeta": None, "que": "Icono de bandeja de Ollama."},
    "python.exe": {"rol": "aplicacion", "carpeta": None, "que": "Intérprete de Python. Puede ser el motor de ScriptLens u otro programa escrito en Python."},
    "node.exe": {"rol": "aplicacion", "carpeta": None, "que": "Entorno Node.js para ejecutar programas JavaScript."},
    "powershell.exe": {"rol": "aplicacion", "carpeta": r"c:\windows\system32\windowspowershell\v1.0", "que": "Consola Windows PowerShell. ScriptLens la usa brevemente para consultas de solo lectura."},
    "pwsh.exe": {"rol": "aplicacion", "carpeta": None, "que": "PowerShell 7."},
    "cmd.exe": {"rol": "aplicacion", "carpeta": SYS32, "que": "Símbolo del sistema (consola de comandos)."},
    "scriptlens.exe": {"rol": "aplicacion", "carpeta": None, "que": "ScriptLens IA (esta aplicación)."},
    "scriptlens-backend.exe": {"rol": "aplicacion", "carpeta": None, "que": "Motor de análisis de ScriptLens IA."},
}

# Nunca se permite finalizar estos procesos desde ScriptLens.
PROTECTED = {n for n, v in KNOWN.items() if v["rol"] in ("critico", "seguridad")} | {
    "svchost.exe",
    "explorer.exe",
    "audiodg.exe",
    "spoolsv.exe",
    "wudfhost.exe",
}


def lookup(name: str) -> dict | None:
    return KNOWN.get((name or "").lower())
