<#
.SYNOPSIS
  Guarda una captura de cada pantalla del instalador de ScriptLens IA mientras usted lo recorre.
.DESCRIPTION
  Abre el instalador y, cada vez que cambia su ventana, guarda una imagen numerada en
  docs\instalacion\capturas\instalador_NN.png. Usted pulsa los botones (Siguiente,
  Instalar, Terminar); este script solo observa la ventana y no hace clic en nada.
  Termina cuando el instalador se cierra.
.EXAMPLE
  PowerShell (raíz del repositorio):
      .\scripts\capturar-instalador.ps1 -Instalador .\build\release\ScriptLens-IA_0.2.0_x64-setup.exe
#>
param([Parameter(Mandatory)][string]$Instalador, [string]$Carpeta = 'docs\instalacion\capturas')
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force $Carpeta | Out-Null
$proc = Start-Process (Resolve-Path $Instalador).Path -PassThru
$name = [IO.Path]::GetFileNameWithoutExtension($Instalador)
$tmp = Join-Path $env:TEMP 'sl-instalador-actual.png'
$prevHash = ''; $n = 0
while (-not $proc.HasExited) {
  Start-Sleep -Milliseconds 700
  try {
    & (Join-Path $PSScriptRoot 'capturar-ventana.ps1') -Salida $tmp -Titulo 'ScriptLens IA' -Proceso $name *> $null
  } catch { continue }
  if (-not (Test-Path $tmp)) { continue }
  $hash = (Get-FileHash $tmp -Algorithm SHA256).Hash
  if ($hash -ne $prevHash) {
    # Esperar a que la pantalla termine de dibujarse antes de guardarla.
    Start-Sleep -Milliseconds 500
    & (Join-Path $PSScriptRoot 'capturar-ventana.ps1') -Salida $tmp -Titulo 'ScriptLens IA' -Proceso $name *> $null
    $n++
    $dest = Join-Path $Carpeta ('instalador_{0:D2}.png' -f $n)
    Copy-Item $tmp $dest -Force
    Write-Host "Guardada $dest"
    $prevHash = (Get-FileHash $tmp -Algorithm SHA256).Hash
  }
}
Remove-Item $tmp -ErrorAction SilentlyContinue
Write-Host "Instalador cerrado. $n capturas en $Carpeta."
