<#
.SYNOPSIS
  Carga en la sesión actual de PowerShell las rutas de MSVC y del SDK de Windows
  necesarias para compilar el contenedor Tauri con Rust.

.DESCRIPTION
  Úselo solo si `cargo build` informa "linker `link.exe` not found" aunque las
  Build Tools de Visual Studio estén instaladas (ocurre cuando la instancia no
  quedó registrada y vcvars64.bat no puede localizarla).

  Ejecutar en PowerShell, desde la raíz del repositorio:
      . .\scripts\msvc-env.ps1
#>

$ErrorActionPreference = 'Stop'

$vsRoots = @(
  "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools",
  "${env:ProgramFiles}\Microsoft Visual Studio\2022\BuildTools",
  "${env:ProgramFiles}\Microsoft Visual Studio\2022\Community",
  "${env:ProgramFiles}\Microsoft Visual Studio\2022\Enterprise"
)
$msvc = $vsRoots | ForEach-Object { Join-Path $_ 'VC\Tools\MSVC' } | Where-Object { Test-Path $_ } |
  ForEach-Object { Get-ChildItem $_ -Directory } | Sort-Object Name -Descending | Select-Object -First 1
if (-not $msvc) { throw 'No se encontró MSVC. Instale Visual Studio Build Tools con "Desarrollo de escritorio con C++".' }

$kits = "${env:ProgramFiles(x86)}\Windows Kits\10"
$sdk = Get-ChildItem (Join-Path $kits 'Lib') -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'um\x64') } |
  Sort-Object Name -Descending | Select-Object -First 1
if (-not $sdk) { throw 'No se encontró el SDK de Windows 10/11.' }
$v = $sdk.Name

$env:PATH = "$($msvc.FullName)\bin\Hostx64\x64;$kits\bin\$v\x64;$HOME\.cargo\bin;$env:PATH"
$env:LIB = "$($msvc.FullName)\lib\x64;$kits\Lib\$v\um\x64;$kits\Lib\$v\ucrt\x64"
$env:INCLUDE = "$($msvc.FullName)\include;$kits\Include\$v\ucrt;$kits\Include\$v\um;$kits\Include\$v\shared;$kits\Include\$v\winrt"

Write-Host "MSVC $($msvc.Name) y SDK $v cargados en esta sesión."
