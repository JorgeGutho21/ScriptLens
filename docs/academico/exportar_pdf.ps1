<#
.SYNOPSIS
  Actualiza índices y campos de los documentos DOCX y los exporta a PDF con Microsoft Word.
.EXAMPLE
  PowerShell (raíz del repositorio): .\docs\academico\exportar_pdf.ps1
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$docs = @(
  "$root\docs\desarrollo\Documentacion_Tecnica_ScriptLens_IA.docx",
  "$root\docs\expo_software\ExpoSoftware_2026_II_ScriptLens_IA.docx",
  "$root\docs\manual_usuario\Manual_Usuario_ScriptLens_IA.docx"
)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  foreach ($path in $docs) {
    if (-not (Test-Path $path)) { continue }
    $d = $word.Documents.Open($path)
    foreach ($toc in $d.TablesOfContents) { $toc.Update() }
    $d.Fields.Update() | Out-Null
    $d.Save()
    $pdf = [IO.Path]::ChangeExtension($path, '.pdf')
    $d.SaveAs2([ref]$pdf, [ref]17)
    $pages = $d.ComputeStatistics(2)
    $d.Close([ref]0)
    Write-Host "$([IO.Path]::GetFileName($pdf)): $pages páginas"
  }
} finally {
  $word.Quit()
  [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
