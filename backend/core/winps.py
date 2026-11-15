"""Ejecución controlada de consultas de solo lectura en Windows PowerShell.

Reglas de seguridad:
- Solo se ejecutan scripts escritos en este repositorio (constantes del código),
  nunca texto proveniente del usuario, de la IA ni de archivos analizados.
- Los datos variables (rutas, nombres) se envían por la entrada estándar como JSON;
  jamás se concatenan dentro del script, lo que evita inyección de comandos.
- Se usa ``-Command`` (no ``-File``), por lo que no es necesario alterar la
  directiva de ejecución del equipo.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

CREATE_NO_WINDOW = 0x08000000
POWERSHELL = "powershell.exe"

# Prefijo común: salida UTF-8 y errores que no detienen la consulta.
_PRELUDE = (
    "$ErrorActionPreference='SilentlyContinue';"
    "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
    "$ProgressPreference='SilentlyContinue';"
)


class PowerShellError(RuntimeError):
    pass


def run_ps(script: str, data=None, timeout: float = 60.0):
    """Ejecuta ``script`` (constante del código) y devuelve su salida JSON decodificada.

    ``data`` se entrega serializado en JSON por stdin; el script lo lee con
    ``$in = [Console]::In.ReadToEnd() | ConvertFrom-Json``.
    """
    if sys.platform != "win32":
        raise PowerShellError("Consulta disponible solo en Windows")
    payload = json.dumps(data) if data is not None else ""
    # Si ScriptLens se inicia desde PowerShell 7, PSModulePath apunta a módulos de la
    # versión 7, incompatibles con Windows PowerShell 5.1 (falla Get-AuthenticodeSignature).
    env = {k: v for k, v in os.environ.items() if k.upper() != "PSMODULEPATH"}
    try:
        proc = subprocess.run(
            [POWERSHELL, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", _PRELUDE + script],
            input=payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            creationflags=CREATE_NO_WINDOW,
        )
    except FileNotFoundError as e:
        raise PowerShellError("Windows PowerShell no está disponible") from e
    except subprocess.TimeoutExpired as e:
        raise PowerShellError("La consulta tardó demasiado") from e
    out = proc.stdout.strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        raise PowerShellError("Respuesta no válida de PowerShell") from e
