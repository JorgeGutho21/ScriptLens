<#
.SYNOPSIS
  Inicia el motor de análisis para desarrollar la interfaz en el navegador.
.DESCRIPTION
  Puerto fijo 8765 y token de desarrollo; los datos se guardan en .dev-data\
  (ignorada por Git) para no mezclarlos con la instalación real.
  Ejecutar en PowerShell desde la raíz del repositorio: .\scripts\dev-backend.ps1
#>
$root = Split-Path $PSScriptRoot -Parent
$env:SCRIPTLENS_PORT = '8765'
$env:SCRIPTLENS_TOKEN = 'dev-local-token'
$env:SCRIPTLENS_DATA_DIR = Join-Path $root '.dev-data'
Set-Location $root
& (Join-Path $root '.venv\Scripts\python.exe') -m backend
