"""Recolección de evidencias para los 30 controles (``Controles_Windows10_30.ps1`` del taller).

Diferencias deliberadas con el script original:
- Todo es de SOLO LECTURA (``Get-*``, lectura de registro, ``auditpol /get``, ``net accounts``).
  No se modifica ninguna configuración.
- No se vuelcan variables de entorno, seriales de BIOS/placa, ``whoami /all`` ni ``netstat``:
  pueden contener secretos y no son necesarios para evaluar los controles.
- Cuando un cmdlet exige administrador, se usa una fuente equivalente que no lo exige
  (registro de Secure Boot, propiedad BitLocker del Shell) y se deja constancia del origen.
- La salida es JSON, evaluado en Python (``evaluate.py``) para poder probar cada regla.
"""

from __future__ import annotations

from backend.core.winps import run_ps

SCRIPT = r"""
function Safe([scriptblock]$s){ try { & $s } catch { $null } }
function Reg([string]$p,[string]$n){ try { (Get-ItemProperty -LiteralPath $p -Name $n -ErrorAction Stop).$n } catch { $null } }
$r=[ordered]@{}
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$r.admin=([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$os=Safe { Get-CimInstance Win32_OperatingSystem -ErrorAction Stop }
$r.os=if($os){[ordered]@{caption=$os.Caption;version=$os.Version;build=[int]$os.BuildNumber;ubr=(Reg 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' 'UBR');display=(Reg 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' 'DisplayVersion');edition=(Reg 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' 'EditionID')}}else{$null}
$hf=@(Safe { Get-HotFix -ErrorAction Stop | Where-Object InstalledOn | Sort-Object InstalledOn -Descending | Select-Object -First 1 })
$r.hotfix=if($hf.Count -and $hf[0]){[ordered]@{id=$hf[0].HotFixID;fecha=$hf[0].InstalledOn.ToString('yyyy-MM-dd')}}else{$null}
$r.firewall=@(Safe { Get-NetFirewallProfile -ErrorAction Stop | ForEach-Object { [ordered]@{name="$($_.Name)";enabled=[bool]$_.Enabled} } })
$d=Safe { Get-MpComputerStatus -ErrorAction Stop }
$r.defender=if($d){[ordered]@{av=$d.AntivirusEnabled;rtp=$d.RealTimeProtectionEnabled;behavior=$d.BehaviorMonitorEnabled;mode="$($d.AMRunningMode)"}}else{$null}
$r.pua=Safe { (Get-MpPreference -ErrorAction Stop).PUAProtection }
$r.av_products=@(Safe { Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct -ErrorAction Stop | ForEach-Object { "$($_.displayName)" } })
$r.rdp_deny=Reg 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server' 'fDenyTSConnections'
$r.rdp_nla=Reg 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' 'UserAuthentication'
$smb=Safe { Get-SmbServerConfiguration -ErrorAction Stop }
$r.smb_server=if($smb){[ordered]@{smb1=$smb.EnableSMB1Protocol;sign=$smb.RequireSecuritySignature;origen='Get-SmbServerConfiguration'}}else{[ordered]@{smb1=(Reg 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters' 'SMB1');sign=(Reg 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters' 'RequireSecuritySignature');origen='registro'}}
$smbc=Safe { Get-SmbClientConfiguration -ErrorAction Stop }
$r.smb_client_sign=if($smbc){$smbc.RequireSecuritySignature}else{Reg 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters' 'RequireSecuritySignature'}
$w=Safe { Get-Service WinRM -ErrorAction Stop }
$r.winrm=if($w){[ordered]@{status="$($w.Status)";start="$($w.StartType)"}}else{$null}
$p='HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
$r.uac=[ordered]@{lua=(Reg $p 'EnableLUA');consent=(Reg $p 'ConsentPromptBehaviorAdmin');secure=(Reg $p 'PromptOnSecureDesktop')}
$u=@(Safe { Get-LocalUser -ErrorAction Stop })
$g=$u | Where-Object { $_.SID.Value -match '-501$' } | Select-Object -First 1
$a=$u | Where-Object { $_.SID.Value -match '-500$' } | Select-Object -First 1
$r.guest_enabled=if($g){[bool]$g.Enabled}else{$null}
$r.admin_enabled=if($a){[bool]$a.Enabled}else{$null}
$r.net_accounts=@(& cmd.exe /c 'net accounts' 2>$null | Where-Object { $_ -match ':' } | ForEach-Object { ($_ -split ':',2)[1].Trim() })
$bl=Safe { Get-BitLockerVolume -MountPoint $env:SystemDrive -ErrorAction Stop }
$r.bitlocker=if($bl){[ordered]@{estado="$($bl.ProtectionStatus)";origen='Get-BitLockerVolume'}}else{[ordered]@{estado=(Safe { (New-Object -ComObject Shell.Application).NameSpace($env:SystemDrive).Self.ExtendedProperty('System.Volume.BitLockerProtection') });origen='Shell (System.Volume.BitLockerProtection)'}}
$sb=Safe { Confirm-SecureBootUEFI -ErrorAction Stop }
$r.secureboot=if($null -ne $sb){[ordered]@{on=[bool]$sb;origen='Confirm-SecureBootUEFI'}}else{[ordered]@{on=(Reg 'HKLM:\SYSTEM\CurrentControlSet\Control\SecureBoot\State' 'UEFISecureBootEnabled');origen='registro SecureBoot\State'}}
# Sin administrador Get-Tpm devuelve TpmPresent=False aunque el TPM exista: solo se usa elevado.
$t=if($r.admin){Safe { Get-Tpm -ErrorAction Stop }}else{$null}
$r.tpm=if($t){[ordered]@{present=[bool]$t.TpmPresent;ready=[bool]$t.TpmReady;origen='Get-Tpm'}}else{[ordered]@{present=[bool](Safe { Get-PnpDevice -Class SecurityDevices -ErrorAction Stop | Where-Object { $_.FriendlyName -match 'TPM|plataforma segura|Trusted Platform' -and $_.Status -eq 'OK' } });ready=$null;origen='Administrador de dispositivos'}}
$r.audit=@(foreach($guid in '{0CCE9215-69AE-11D9-BED3-505054503030}','{0CCE9235-69AE-11D9-BED3-505054503030}'){ $o=& auditpol.exe /get /subcategory:$guid /r 2>$null; if($LASTEXITCODE -eq 0 -and $o){ $row=($o | Where-Object {$_ -match $guid} | Select-Object -First 1); if($row){ $c=$row -split ','; [ordered]@{sub=$c[2];valor=$c[4]} } } })
$r.ps_logging=Reg 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging' 'EnableScriptBlockLogging'
$r.shares=@(Safe { Get-CimInstance Win32_Share -ErrorAction Stop | Where-Object { $_.Name -notmatch '\$$' } | ForEach-Object { "$($_.Name)" } })
$rr=Safe { Get-Service RemoteRegistry -ErrorAction Stop }
$r.remote_registry=if($rr){[ordered]@{status="$($rr.Status)";start="$($rr.StartType)"}}else{$null}
$r.autorun=Reg 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer' 'NoDriveTypeAutoRun'
$r.autorun_user=Reg 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer' 'NoDriveTypeAutoRun'
$r | ConvertTo-Json -Depth 5 -Compress
"""


def collect() -> dict:
    return run_ps(SCRIPT, timeout=120) or {}
