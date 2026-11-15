"""Catálogo de reglas del analizador de scripts.

Origen: las reglas C01–A03 reproducen el catálogo del proyecto académico original
(«ScriptLens IA», guía 03B, sección 10.1, Jorge Gutiérrez, 2026). Se conservan
sus identificadores, patrones, categorías y técnicas para mantener la trazabilidad.
Corrección heredada de la guía: E03 excluye las redirecciones a «nul».

Las reglas marcadas ``ampliacion=True`` se añadieron en esta versión para cubrir
operaciones frecuentes de PowerShell y CMD que el catálogo original no contemplaba.
Usan los identificadores vigentes en ATT&CK 20.1: T1562.001→T1685,
T1070.001→T1685.005 y T1562.004→T1686 fueron revocadas y reemplazadas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    id: str
    pattern: str
    categoria: str
    attack: str
    explicacion: str
    ampliacion: bool = False


# Catálogo original (24 reglas, 9 categorías)
ORIGINAL = [
    Rule("C01", r"\bsysteminfo\b", "consulta", "T1082", "Muestra información del sistema"),
    Rule("C02", r"\btasklist\b|\bGet-Process\b", "consulta", "T1057", "Lista los procesos"),
    Rule("C03", r"\bipconfig\b|\bgetmac\b", "consulta", "T1016", "Muestra la configuración de red"),
    Rule("C04", r"\bnetstat\b|\bGet-NetTCPConnection\b", "consulta", "T1049", "Lista conexiones y puertos"),
    Rule("C05", r"\bwhoami\b|%USERNAME%", "consulta", "T1033", "Identifica al usuario"),
    Rule("C06", r"\breg(\.exe)?\s+query\b|\bGet-ItemProperty\b", "consulta", "T1012", "Lee el Registro"),
    Rule("E01", r"\bmkdir\b|\bmd\s|\bNew-Item\b", "escritura", "-", "Crea carpetas o archivos"),
    Rule("E02", r"\bcopy\b|\bxcopy\b|\brobocopy\b|\bCopy-Item\b", "escritura", "-", "Copia archivos"),
    Rule("E03", r">>?\s*(?!nul\b)\"?[\w%\\:.]", "escritura", "-", "Escribe la salida en un archivo"),
    Rule("R01", r"\breg(\.exe)?\s+add\b|\bSet-ItemProperty\b|\bNew-ItemProperty\b", "registro", "T1112", "Modifica el Registro"),
    Rule("P01", r"CurrentVersion\\Run(Once)?\b", "persistencia", "T1547.001", "Clave de inicio automático Run/RunOnce"),
    Rule("P02", r"\bschtasks\b.*\/create|\bRegister-ScheduledTask\b", "persistencia", "T1053.005", "Crea una tarea programada"),
    Rule("P03", r"shell:startup|\\Start Menu\\Programs\\Startup", "persistencia", "T1547.001", "Carpeta de Inicio"),
    Rule("B01", r"\brmdir\b.*\/s|\brd\s.*\/s|Remove-Item\b.*-Recurse", "borrado", "T1070.004", "Borrado recursivo de carpetas"),
    Rule("B02", r"\bdel\b.*\/[fsq]|\berase\b", "borrado", "T1070.004", "Borrado forzado de archivos"),
    Rule("O01", r"\battrib\b.*\+h|\battrib\b.*\+s", "ocultamiento", "T1564.001", "Oculta archivos con atributos"),
    Rule("O02", r"-WindowStyle\s+Hidden|\bwscript\b|\.vbs\b", "ocultamiento", "T1564.003", "Ejecución en ventana oculta"),
    Rule("O03", r"-enc(odedcommand)?\s", "ocultamiento", "T1027", "Comando codificado (ofuscación)"),
    Rule("N01", r"\bftp\b\s+-s:|\bftp\.exe\b", "red", "T1048.003", "Transferencia automática por FTP"),
    Rule("N02", r"Invoke-WebRequest|\bcurl\b|\bbitsadmin\b|Net\.WebClient", "red", "T1105", "Descarga o envío por red"),
    Rule("K01", r"\btaskkill\b|\bStop-Process\b", "procesos", "-", "Termina procesos"),
    Rule("A01", r"\bnet\s+user\b.*\/add", "cuentas", "T1136.001", "Crea una cuenta local"),
    Rule("A02", r"\bnet\s+localgroup\b.*administrators|administradores", "cuentas", "T1098", "Cambia grupos de administradores"),
    Rule("A03", r"\bnet\s+share\b", "cuentas", "-", "Comparte carpetas en red"),
]

# Ampliación de esta versión
AMPLIACION = [
    Rule("C07", r"\bGet-(WmiObject|CimInstance)\b|\bwmic\b(?!.*\b(delete|call\s+create)\b)", "consulta", "T1047", "Consulta información mediante WMI", True),
    Rule("C08", r"\bdir\b.*\/s\b|\bGet-ChildItem\b.*-Recurse|\btree\b", "consulta", "T1083", "Recorre carpetas para listar archivos", True),
    Rule("C09", r"\bGet-(Service|ComputerInfo|NetIPConfiguration|LocalUser|Disk|Volume)\b|\bsc(\.exe)?\s+query\b", "consulta", "T1082", "Consulta configuración del sistema", True),
    Rule("E04", r"\b(Set|Add|Out)-Content\b|\bOut-File\b|\bExport-Csv\b", "escritura", "-", "Escribe contenido en un archivo", True),
    Rule("E05", r"\bmove\b|\bren(ame)?\b\s|\bMove-Item\b|\bRename-Item\b", "escritura", "-", "Mueve o renombra archivos", True),
    Rule("R02", r"\breg(\.exe)?\s+delete\b|\bRemove-ItemProperty\b", "registro", "T1112", "Elimina valores del Registro", True),
    Rule("P04", r"\bsc(\.exe)?\s+create\b|\bNew-Service\b", "persistencia", "T1543.003", "Crea un servicio de Windows", True),
    Rule("P05", r"\\Winlogon\\?.*\b(Shell|Userinit)\b", "persistencia", "T1547.004", "Modifica el inicio de sesión de Windows (Winlogon)", True),
    Rule("B03", r"\bformat\b\s+[a-z]:|\bcipher\b\s+/w|\bClear-RecycleBin\b", "borrado", "T1485", "Borra o sobrescribe datos de forma masiva", True),
    Rule("O04", r"FromBase64String|\bcertutil\b.*-decode", "ocultamiento", "T1140", "Decodifica contenido oculto", True),
    Rule("N03", r"DownloadString|DownloadFile|Start-BitsTransfer|\bcertutil\b.*-urlcache", "red", "T1105", "Descarga archivos o código desde Internet", True),
    Rule("K02", r"\bshutdown\b\s+/[srf]|\bStop-Computer\b|\bRestart-Computer\b", "procesos", "T1529", "Apaga o reinicia el equipo", True),
    Rule("X01", r"\bInvoke-Expression\b|\biex\b|\bInvoke-Command\b.*-ScriptBlock", "ejecucion", "T1059.001", "Ejecuta código construido dinámicamente", True),
    Rule("X02", r"\bmshta\b|\brundll32\b|\bregsvr32\b.*\/i:", "ejecucion", "T1218", "Usa un programa de Windows para ejecutar otro código", True),
    Rule("X03", r"Start-Process\b.*-Verb\s+RunAs|\brunas\b", "ejecucion", "-", "Solicita ejecutar con privilegios de administrador", True),
    Rule("D01", r"Set-MpPreference\b.*-Disable|Add-MpPreference\b.*-Exclusion", "defensa", "T1685", "Desactiva o debilita Microsoft Defender", True),
    Rule("D02", r"\bvssadmin\b.*delete|\bwmic\b.*shadowcopy.*delete|\bbcdedit\b.*recoveryenabled\s+no", "defensa", "T1490", "Elimina copias de recuperación del sistema", True),
    Rule("D03", r"\bwevtutil\b\s+cl\b|\bClear-EventLog\b", "defensa", "T1685.005", "Borra los registros de eventos", True),
    Rule("D04", r"netsh\b.*(advfirewall|firewall).*(state\s+off|disable)|Set-NetFirewallProfile\b.*-Enabled\s+(False|0)", "defensa", "T1686", "Desactiva el firewall", True),
]

RULES = ORIGINAL + AMPLIACION

# Las 9 categorías originales más 2 de la ampliación
CATEGORIAS = ["consulta", "escritura", "registro", "persistencia", "borrado", "ocultamiento", "red", "procesos", "cuentas", "ejecucion", "defensa"]

CATEGORIA_ES = {
    "consulta": "Consulta (solo lee información)",
    "escritura": "Escritura de archivos",
    "registro": "Cambios en el Registro",
    "persistencia": "Persistencia (se ejecuta solo en el futuro)",
    "borrado": "Borrado de datos",
    "ocultamiento": "Ocultamiento u ofuscación",
    "red": "Comunicación por red",
    "procesos": "Control de procesos o del equipo",
    "cuentas": "Cuentas y recursos compartidos",
    "ejecucion": "Ejecución indirecta de código",
    "defensa": "Debilita protecciones del sistema",
}

# Tipo de operación por categoría (consulta / modificación / sensible)
OPERACION = {
    "consulta": "consulta",
    "escritura": "modificacion",
    "registro": "modificacion",
    "persistencia": "sensible",
    "borrado": "sensible",
    "ocultamiento": "sensible",
    "red": "sensible",
    "procesos": "sensible",
    "cuentas": "sensible",
    "ejecucion": "sensible",
    "defensa": "sensible",
}

COMPILED = [(r, re.compile(r.pattern, re.IGNORECASE)) for r in RULES]
_BLOCK_START = re.compile(r"^\s*<#")
_BLOCK_END = re.compile(r"#>\s*$")


def is_comment(line: str) -> bool:
    s = line.strip().lower()
    return s.startswith(("rem ", "::", "#")) or s == "rem"


def hallazgos(texto: str) -> list[dict]:
    """Una fila por coincidencia: línea, regla, categoría, ATT&CK y explicación.

    Igual que el original, omite comentarios de BAT (rem, ::) y de PowerShell (#);
    además omite los bloques de comentario de PowerShell <# … #>.
    """
    filas = []
    in_block = False
    for n, linea in enumerate(texto.splitlines(), start=1):
        if in_block:
            if _BLOCK_END.search(linea):
                in_block = False
            continue
        if _BLOCK_START.match(linea):
            in_block = not _BLOCK_END.search(linea)
            continue
        if is_comment(linea):
            continue
        matched = [(rule, rx) for rule, rx in COMPILED if rx.search(linea)]
        ids = {rule.id for rule, _ in matched}
        # Corrección por contexto (hallada en el análisis de errores): leer la clave
        # Run (reg query / Get-ItemProperty) es una consulta, no persistencia.
        if ids & {"P01", "P03"} and "C06" in ids and not ids & {"R01", "R02", "E02", "E04"}:
            matched = [(rule, rx) for rule, rx in matched if rule.id not in ("P01", "P03")]
        for rule, _ in matched:
            filas.append(
                {
                    "linea": n,
                    "regla": rule.id,
                    "categoria": rule.categoria,
                    "attack": rule.attack,
                    "explicacion": rule.explicacion,
                    "codigo": linea.strip()[:160],
                    "ampliacion": rule.ampliacion,
                }
            )
    return filas
