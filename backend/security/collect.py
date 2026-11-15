"""Recolección de información de seguridad de Windows (solo lectura).

Inspirado en el modelo de osquery: cada fuente se trata como una «tabla» de
datos consultable y se registra su procedencia, la hora de medición y el
motivo cuando no se pudo leer (por ejemplo, permisos insuficientes).
No se instala ningún servicio ni se modifica configuración alguna.
"""

from __future__ import annotations

import os
import shlex
import time
import winreg
from pathlib import Path

import psutil

from backend.core.winps import PowerShellError, run_ps

# Una sola invocación de PowerShell. Cada bloque captura sus propios errores para
# que la falta de permisos en una fuente no impida leer las demás.
_PS_AUDIT = r"""
function Try-Get($block) { try { & $block } catch { @{ error = $_.Exception.Message } } }
$r = [ordered]@{}
$r.defender = Try-Get { Get-MpComputerStatus -ErrorAction Stop | Select-Object AMServiceEnabled, AntivirusEnabled, RealTimeProtectionEnabled,
    BehaviorMonitorEnabled, IsTamperProtected, AMRunningMode, AntivirusSignatureAge, QuickScanAge, FullScanAge,
    @{n='SignatureLastUpdated';e={$_.AntivirusSignatureLastUpdated.ToString('o')}},
    @{n='QuickScanEnd';e={ if ($_.QuickScanEndTime) { $_.QuickScanEndTime.ToString('o') } }} }
$r.threats = Try-Get { @(Get-MpThreat -ErrorAction Stop | Select-Object ThreatID, ThreatName, SeverityID, IsActive, DidThreatExecute) }
$r.detections = Try-Get { @(Get-MpThreatDetection -ErrorAction Stop | Select-Object ThreatID, ThreatStatusID, ActionSuccess, Resources,
    @{n='Time';e={$_.InitialDetectionTime.ToString('o')}}) }
$r.av_products = Try-Get { @(Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct -ErrorAction Stop |
    Select-Object displayName, productState) }
$r.firewall = Try-Get { @(Get-NetFirewallProfile -ErrorAction Stop | Select-Object Name, @{n='Enabled';e={[bool]$_.Enabled}}) }
$r.tasks = Try-Get { @(Get-ScheduledTask -ErrorAction Stop | Where-Object { $_.State -ne 'Disabled' } | ForEach-Object {
    [pscustomobject]@{ name = $_.TaskName; path = $_.TaskPath; state = [string]$_.State; author = $_.Author;
      actions = @($_.Actions | ForEach-Object { [pscustomobject]@{ exe = $_.Execute; args = $_.Arguments } });
      triggers = @($_.Triggers | ForEach-Object { $_.CimClass.CimClassName }) } }) }
$r.events = Try-Get { @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; Level = 1, 2; StartTime = (Get-Date).AddDays(-7) } -MaxEvents 300 -ErrorAction Stop |
    Select-Object Id, ProviderName, LevelDisplayName, @{n='Time';e={$_.TimeCreated.ToString('o')}}) }
$r.users = Try-Get { @(Get-LocalUser -ErrorAction Stop | Select-Object Name, Enabled, @{n='Sid';e={$_.SID.Value}}) }
$r.power = Try-Get { (powercfg /getactivescheme) -join ' ' }
ConvertTo-Json -InputObject $r -Depth 6 -Compress
"""


def _err(value):
    return isinstance(value, dict) and "error" in value and len(value) == 1


def powershell_sources() -> dict:
    try:
        data = run_ps(_PS_AUDIT, timeout=90) or {}
    except PowerShellError as e:
        return {"_error": str(e)}
    return data


# --- Inicio automático (Registro y carpetas de Inicio) ----------------------

_RUN_KEYS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "Registro (usuario) · Run", "HKCU"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "Registro (usuario) · RunOnce", "HKCU"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "Registro (equipo) · Run", "HKLM"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "Registro (equipo) · RunOnce", "HKLM"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "Registro (equipo, 32 bits) · Run", "HKLM32"),
]
_APPROVED = {
    "HKCU": (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
    "HKLM": (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
    "HKLM32": (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32"),
    "FOLDER_USER": (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"),
    "FOLDER_ALL": (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"),
}


def _read_values(hive, path) -> dict:
    out = {}
    try:
        with winreg.OpenKey(hive, path) as k:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(k, i)
                except OSError:
                    break
                out[name] = value
                i += 1
    except OSError:
        pass
    return out


def approved_state(scope: str, name: str) -> bool:
    """Estado en «Aplicaciones de arranque» de Windows: el primer byte impar indica desactivado."""
    hive, path = _APPROVED[scope]
    value = _read_values(hive, path).get(name)
    if isinstance(value, bytes) and value:
        return value[0] % 2 == 0
    return True


def command_executable(command: str) -> str | None:
    """Extrae la ruta del ejecutable de una línea de comandos de inicio."""
    if not command:
        return None
    cmd = os.path.expandvars(command.strip())
    try:
        first = shlex.split(cmd, posix=False)[0].strip('"')
    except ValueError:
        first = cmd.split(" ")[0].strip('"')
    if not os.path.isabs(first):
        # Rutas con espacios sin comillas: se prueba acumulando fragmentos.
        parts = cmd.split(" ")
        for i in range(1, len(parts) + 1):
            candidate = " ".join(parts[:i]).strip('"')
            if candidate.lower().endswith((".exe", ".bat", ".cmd", ".vbs", ".ps1", ".lnk")) and os.path.isabs(candidate):
                return candidate
        return first or None
    if not first.lower().endswith((".exe", ".bat", ".cmd", ".vbs", ".ps1", ".lnk", ".com")):
        parts = cmd.split(" ")
        for i in range(1, len(parts) + 1):
            candidate = " ".join(parts[:i]).strip('"')
            if candidate.lower().endswith((".exe", ".bat", ".cmd", ".vbs", ".ps1", ".lnk", ".com")):
                return candidate
    return first


def startup_entries() -> list[dict]:
    entries = []
    for hive, path, origin, scope in _RUN_KEYS:
        for name, value in _read_values(hive, path).items():
            command = str(value)
            entries.append(
                {
                    "id": f"{scope}:{name}",
                    "nombre": name,
                    "comando": command,
                    "ejecutable": command_executable(command),
                    "origen": origin,
                    "ambito": "usuario" if scope == "HKCU" else "equipo",
                    "habilitado": approved_state(scope, name) if scope in _APPROVED else True,
                    "modificable_sin_admin": scope == "HKCU",
                    "scope": scope,
                }
            )
    folders = [
        (Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup", "Carpeta Inicio (usuario)", "FOLDER_USER", "usuario"),
        (Path(os.environ.get("PROGRAMDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup", "Carpeta Inicio (todos los usuarios)", "FOLDER_ALL", "equipo"),
    ]
    for folder, origin, scope, ambito in folders:
        if not folder.is_dir():
            continue
        for f in folder.iterdir():
            if f.name.lower() == "desktop.ini" or not f.is_file():
                continue
            entries.append(
                {
                    "id": f"{scope}:{f.name}",
                    "nombre": f.stem,
                    "comando": str(f),
                    "ejecutable": str(f),
                    "origen": origin,
                    "ambito": ambito,
                    "habilitado": approved_state(scope, f.name),
                    "modificable_sin_admin": scope == "FOLDER_USER",
                    "scope": scope,
                }
            )
    return entries


# --- Servicios ----------------------------------------------------------------


def services() -> list[dict]:
    out = []
    for s in psutil.win_service_iter():
        try:
            d = s.as_dict()
        except (psutil.Error, OSError):
            continue
        out.append(
            {
                "nombre": d.get("name"),
                "mostrado": d.get("display_name"),
                "estado": d.get("status"),
                "inicio": d.get("start_type"),
                "binario": d.get("binpath"),
                "ejecutable": command_executable(d.get("binpath") or ""),
                "cuenta": d.get("username"),
                "pid": d.get("pid"),
            }
        )
    return out


def collect() -> dict:
    started = time.time()
    data = powershell_sources()
    data["startup"] = startup_entries()
    try:
        data["services"] = services()
    except Exception as e:  # noqa: BLE001
        data["services"] = {"error": str(e)}
    data["sessions"] = [{"terminal": u.terminal, "desde": u.started} for u in psutil.users()]
    data["measured_at"] = time.time()
    data["duration_s"] = round(data["measured_at"] - started, 2)
    return data
