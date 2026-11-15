<#
.SYNOPSIS
  Construye el instalador de ScriptLens IA para Windows (NSIS) y calcula su SHA-256.

.DESCRIPTION
  1. Empaqueta el motor Python con PyInstaller (carpeta build\backend\scriptlens-backend).
  2. Compila la interfaz y el contenedor Tauri en modo release.
  3. Genera el instalador NSIS y el archivo .sha256 junto a él.

  Ejecutar en PowerShell desde la raíz del repositorio:
      .\scripts\construir_instalador.ps1
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$py = Join-Path $root '.venv\Scripts\python.exe'

Write-Host '1/3 Empaquetando el motor de análisis (PyInstaller)…'
& $py -m PyInstaller --noconfirm --clean --log-level WARN `
  --name scriptlens-backend --onedir --noconsole `
  --distpath build\backend --workpath build\pyinstaller --specpath build `
  --paths $root `
  --add-data "$root\backend\scripts\data;backend\scripts\data" `
  --collect-submodules uvicorn --collect-submodules backend `
  --hidden-import sklearn.utils._typedefs --hidden-import sklearn.neighbors._partition_nodes `
  --exclude-module tkinter --exclude-module matplotlib --exclude-module IPython --exclude-module pytest `
  scripts\scriptlens_backend.py
if ($LASTEXITCODE) { throw 'PyInstaller falló' }

Write-Host '2/3 Compilando la aplicación y el instalador (Tauri)…'
if (-not (Get-Command link.exe -ErrorAction SilentlyContinue)) { . (Join-Path $PSScriptRoot 'msvc-env.ps1') }
npm run build
if ($LASTEXITCODE) { throw 'tauri build falló' }

Write-Host '3/3 Calculando SHA-256…'
$nsis = Get-ChildItem src-tauri\target\release\bundle\nsis\*.exe | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$hash = (Get-FileHash $nsis.FullName -Algorithm SHA256).Hash
"$hash  $($nsis.Name)" | Set-Content "$($nsis.FullName).sha256" -Encoding ascii
Write-Host "Instalador: $($nsis.FullName)"
Write-Host "SHA-256:    $hash"
