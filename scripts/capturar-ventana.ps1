<#
.SYNOPSIS
  Guarda una captura PNG de la ventana principal de ScriptLens IA (solo esa ventana).
.DESCRIPTION
  Si la ventana está minimizada, la restaura para capturarla y luego la vuelve a minimizar.
.EXAMPLE
  PowerShell: .\scripts\capturar-ventana.ps1 -Salida docs\capturas\01_panel.png
#>
param([Parameter(Mandatory)] [string] $Salida, [string] $Titulo = 'ScriptLens IA', [string] $Proceso = 'scriptlens')

Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class SLWin {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc p, IntPtr l);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  public static IntPtr Find(string title, uint[] pids) {
    IntPtr found = IntPtr.Zero;
    EnumWindows((h, l) => {
      uint pid; GetWindowThreadProcessId(h, out pid);
      var sb = new StringBuilder(256); GetWindowText(h, sb, 256);
      if (sb.ToString() == title && Array.IndexOf(pids, pid) >= 0) { found = h; return false; }
      return true;
    }, IntPtr.Zero);
    return found;
  }
}
'@
[SLWin]::SetProcessDPIAware() | Out-Null
$pids = [uint32[]]@(Get-Process $Proceso -ErrorAction Stop | ForEach-Object Id)
$hwnd = [SLWin]::Find($Titulo, $pids)
if ($hwnd -eq [IntPtr]::Zero) { throw "No se encontró la ventana $Titulo" }

$wasMin = [SLWin]::IsIconic($hwnd)
if ($wasMin) { [SLWin]::ShowWindow($hwnd, 9) | Out-Null; Start-Sleep -Milliseconds 1500 }  # SW_RESTORE

$r = New-Object SLWin+RECT
[SLWin]::GetWindowRect($hwnd, [ref]$r) | Out-Null
$bmp = New-Object System.Drawing.Bitmap ($r.R - $r.L), ($r.B - $r.T)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
[SLWin]::PrintWindow($hwnd, $hdc, 2) | Out-Null  # PW_RENDERFULLCONTENT
$g.ReleaseHdc($hdc); $g.Dispose()
if ($wasMin) { [SLWin]::ShowWindow($hwnd, 6) | Out-Null }  # SW_MINIMIZE

$dir = Split-Path $Salida
New-Item -ItemType Directory -Force $dir | Out-Null
$bmp.Save((Join-Path (Resolve-Path $dir).Path (Split-Path $Salida -Leaf)), [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Host "Captura guardada en $Salida"
