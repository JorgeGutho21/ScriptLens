<#
  Crea qr_scriptlens_poster.png (3000 x 4350 px, 20 x 29 cm a 381 ppp) y
  qr_scriptlens_poster.pdf (vectorial, 200 x 290 mm) a partir de
  docs/qr/qr_scriptlens_poster.svg, con Microsoft Edge en modo sin interfaz.
  No instala nada ni cambia la configuración del equipo.
#>
$ErrorActionPreference = 'Stop'
$raiz = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$qr = Join-Path $raiz 'docs\qr'
$svg = Join-Path $qr 'qr_scriptlens_poster.svg'
$edge = @(
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw 'No se encontró Microsoft Edge.' }

$tmp = Join-Path ([IO.Path]::GetTempPath()) ("scriptlens-poster-" + [guid]::NewGuid())
New-Item -ItemType Directory $tmp | Out-Null
try {
  $urlSvg = ([Uri]$svg).AbsoluteUri
  $png = Join-Path $tmp 'png.html'
  Set-Content $png -Encoding UTF8 "<!doctype html><html><body style='margin:0;background:#060D18'><img src='$urlSvg' style='display:block;width:2000px;height:2900px'></body></html>"
  $pdf = Join-Path $tmp 'pdf.html'
  Set-Content $pdf -Encoding UTF8 "<!doctype html><html><head><style>@page{size:200mm 290mm;margin:0}html,body{margin:0}img{display:block;width:200mm;height:290mm}</style></head><body><img src='$urlSvg'></body></html>"

  $comunes = @('--headless=new', '--disable-gpu', '--hide-scrollbars', "--user-data-dir=$tmp\perfil", '--virtual-time-budget=5000')
  & $edge @comunes '--window-size=2000,2900' '--force-device-scale-factor=1.5' "--screenshot=$qr\qr_scriptlens_poster.png" ([Uri]$png).AbsoluteUri 2>$null | Out-Null
  & $edge @comunes '--no-pdf-header-footer' "--print-to-pdf=$qr\qr_scriptlens_poster.pdf" ([Uri]$pdf).AbsoluteUri 2>$null | Out-Null
  Start-Sleep -Milliseconds 500
  foreach ($f in 'qr_scriptlens_poster.png', 'qr_scriptlens_poster.pdf') {
    if (-not (Test-Path (Join-Path $qr $f))) { throw "No se generó $f" }
    Write-Host ("{0}: {1:N0} bytes" -f $f, (Get-Item (Join-Path $qr $f)).Length)
  }
} finally {
  Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}
