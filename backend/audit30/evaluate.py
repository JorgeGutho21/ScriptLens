"""Evaluación de los 30 controles del taller a partir de las evidencias recolectadas.

Estados: CUMPLE · NO CUMPLE · REQUIERE REVISIÓN · NO APLICA.
Regla general: un control solo se marca CUMPLE con evidencia suficiente. Si falta el dato
(por ejemplo, porque exige administrador) el resultado es REQUIERE REVISIÓN, nunca CUMPLE.
La numeración, las áreas y los nombres siguen ``Controles_Windows10_30.ps1``.
"""

from __future__ import annotations

import datetime as dt

CUMPLE, NO_CUMPLE, REVISION, NO_APLICA = "CUMPLE", "NO CUMPLE", "REQUIERE REVISIÓN", "NO APLICA"

# Fin de soporte de Windows para ediciones Home/Pro según el ciclo de vida publicado por Microsoft.
# Enterprise y Education reciben 12 meses más en las versiones de otoño (H2).
SUPPORT_END = {
    19045: ("Windows 10 22H2", dt.date(2025, 10, 14)),
    22000: ("Windows 11 21H2", dt.date(2023, 10, 10)),
    22621: ("Windows 11 22H2", dt.date(2024, 10, 8)),
    22631: ("Windows 11 23H2", dt.date(2025, 11, 11)),
    26100: ("Windows 11 24H2", dt.date(2026, 10, 13)),
    26200: ("Windows 11 25H2", dt.date(2027, 10, 12)),
}

NEED_ADMIN = "No se pudo leer sin permisos de administrador."


def _t(v) -> str:
    if v is None:
        return "no disponible"
    if isinstance(v, bool):
        return "Sí" if v else "No"
    if isinstance(v, list):
        return ", ".join(map(str, v)) or "ninguno"
    return str(v)


def _bool(v, expected=True):
    if v is None:
        return REVISION
    return CUMPLE if bool(v) == expected else NO_CUMPLE


# (n, área, nombre, propósito, explicación sencilla, recomendación)
CONTROLS = [
    (1, "Sistema", "Windows 10 versión 22H2", "Comprobar que un equipo con Windows 10 tenga la última versión publicada (22H2).", "Las versiones antiguas dejan de recibir parches de seguridad.", "Actualizar a una versión soportada del sistema operativo."),
    (2, "Sistema", "Cobertura de soporte de seguridad", "Verificar que la versión instalada siga recibiendo actualizaciones de seguridad de Microsoft.", "Un Windows sin soporte no recibe arreglos para fallos nuevos.", "Planificar la actualización o verificar la suscripción ESU."),
    (3, "Sistema", "Actualizaciones recientes", "Confirmar que se instalaron actualizaciones en las últimas semanas.", "Las actualizaciones corrigen fallos que los atacantes aprovechan.", "Revisar Windows Update e instalar las actualizaciones acumulativas pendientes."),
    (4, "Firewall", "Firewall perfil Dominio", "El firewall de Windows debe estar activo en redes de dominio.", "El firewall bloquea conexiones no solicitadas desde la red.", "Activar el firewall en este perfil."),
    (5, "Firewall", "Firewall perfil Privado", "El firewall de Windows debe estar activo en redes privadas (casa, oficina).", "El firewall bloquea conexiones no solicitadas desde la red.", "Activar el firewall en este perfil."),
    (6, "Firewall", "Firewall perfil Público", "El firewall de Windows debe estar activo en redes públicas (cafés, universidad).", "En redes públicas hay desconocidos: es el perfil más importante.", "Activar el firewall en este perfil."),
    (7, "Defender", "Antivirus activo", "Debe haber un antivirus activo.", "El antivirus detecta y bloquea programas maliciosos conocidos.", "Activar Microsoft Defender u otro antivirus actualizado."),
    (8, "Defender", "Protección en tiempo real", "Defender debe analizar los archivos en el momento en que se usan.", "Sin tiempo real, un archivo malicioso puede ejecutarse antes de ser analizado.", "Activar la protección en tiempo real en Seguridad de Windows."),
    (9, "Defender", "Protección de comportamiento", "Defender debe vigilar el comportamiento de los programas.", "Detecta amenazas nuevas por lo que hacen, no solo por su firma.", "Activar la supervisión de comportamiento."),
    (10, "Defender", "Protección contra aplicaciones potencialmente no deseadas (PUA)", "Bloquear programas no deseados (publicidad, barras, mineros).", "Muchos instaladores gratuitos incluyen programas que no se pidieron.", "Activar «Bloqueo de aplicaciones potencialmente no deseadas»."),
    (11, "Acceso remoto", "Escritorio remoto (RDP) deshabilitado si no se necesita", "Reducir las puertas de entrada remotas.", "RDP permite controlar el equipo a distancia; si no se usa, es mejor tenerlo apagado.", "Si RDP es necesario, limitar orígenes, exigir NLA y contraseñas robustas."),
    (12, "Acceso remoto", "RDP exige autenticación a nivel de red (NLA)", "Si RDP está activo, exigir autenticación antes de abrir la sesión.", "NLA evita que alguien vea la pantalla de inicio sin identificarse.", "Activar Network Level Authentication."),
    (13, "SMB", "Servidor SMBv1 deshabilitado", "SMBv1 es un protocolo antiguo e inseguro para compartir archivos.", "SMBv1 fue usado por el ransomware WannaCry.", "Deshabilitar SMBv1 tras verificar que nada lo necesite."),
    (14, "SMB", "Firma SMB requerida en servidor", "Exigir firma en las conexiones de archivos compartidos que recibe el equipo.", "La firma impide que alguien en la red altere los datos en tránsito.", "Evaluar exigir la firma SMB según compatibilidad y política."),
    (15, "SMB", "Firma SMB requerida en cliente", "Exigir firma al conectarse a carpetas compartidas de otros equipos.", "Protege contra suplantación de servidores de archivos.", "Evaluar exigir la firma SMB en el cliente."),
    (16, "Acceso remoto", "WinRM no expuesto sin necesidad", "La administración remota de Windows (WinRM) solo debe estar activa si se usa.", "WinRM permite ejecutar órdenes a distancia.", "Detener y dejar en manual si no se necesita."),
    (17, "Cuentas", "Control de cuentas de usuario (UAC) habilitado", "Pedir confirmación antes de cambios que requieren administrador.", "UAC evita que un programa obtenga permisos totales sin que usted lo note.", "Habilitar UAC."),
    (18, "Cuentas", "UAC solicita confirmación al administrador", "UAC no debe elevar permisos en silencio.", "Si no pregunta, un programa puede tomar el control sin aviso.", "Configurar la elevación con confirmación o credenciales."),
    (19, "Cuentas", "UAC usa escritorio seguro", "El aviso de UAC se muestra en un escritorio aislado.", "Impide que otro programa haga clic en «Sí» por usted.", "Habilitar el escritorio seguro para los avisos de UAC."),
    (20, "Cuentas", "Cuenta Invitado deshabilitada", "La cuenta Invitado no debe estar disponible.", "Permite entrar al equipo sin contraseña propia.", "Mantener deshabilitada la cuenta Invitado."),
    (21, "Cuentas", "Administrador integrado deshabilitado", "La cuenta «Administrador» incluida en Windows debe estar desactivada.", "Es un objetivo conocido de ataques de contraseña.", "Deshabilitarla y usar cuentas administrativas personales."),
    (22, "Cuentas", "Política de contraseñas y bloqueo", "Contraseñas de longitud mínima y bloqueo tras intentos fallidos.", "Dificulta adivinar contraseñas probando muchas veces.", "Exigir al menos 8 caracteres y bloquear tras 10 intentos o menos (o usar cuenta Microsoft con PIN/Windows Hello)."),
    (23, "Cifrado", "BitLocker en la unidad del sistema", "El disco del sistema debe estar cifrado.", "Si roban el equipo, sin cifrado se pueden leer los archivos sacando el disco.", "Activar BitLocker (o Cifrado de dispositivo) y guardar la clave de recuperación."),
    (24, "Arranque", "Secure Boot habilitado", "Arranque seguro UEFI activado.", "Impide que un programa malicioso se cargue antes que Windows.", "Activar Secure Boot en la configuración UEFI del equipo."),
    (25, "Arranque", "TPM disponible y preparado", "Chip de seguridad TPM presente y listo.", "Guarda claves de cifrado y de Windows Hello de forma protegida.", "Activar el TPM (fTPM/PTT) en la UEFI si existe."),
    (26, "Auditoría", "Políticas de auditoría de seguridad", "Registrar inicios de sesión y cambios de cuentas.", "Sin registros no se puede investigar un acceso indebido.", "Auditar al menos «Inicio de sesión» y «Administración de cuentas de usuario»."),
    (27, "Auditoría", "Registro de bloques de PowerShell", "Guardar lo que ejecutan los scripts de PowerShell.", "Ayuda a detectar scripts maliciosos ocultos.", "Habilitar Script Block Logging si la política lo requiere."),
    (28, "Recursos", "Carpetas compartidas no administrativas", "Revisar qué carpetas comparte el equipo en la red.", "Una carpeta compartida con permisos amplios expone archivos.", "Revisar permisos; dejar de compartir lo que no se necesite."),
    (29, "Servicios", "Registro remoto deshabilitado si no se utiliza", "El servicio Registro remoto debe estar deshabilitado.", "Permite leer y cambiar el registro desde otro equipo.", "Deshabilitarlo si no lo requiere una administración autorizada."),
    (30, "Dispositivos", "Restricción de AutoRun", "Impedir que memorias USB o CD ejecuten programas solos.", "Muchos virus se propagaban por USB con AutoRun.", "Aplicar la política «Desactivar Reproducción automática» en todas las unidades (valor 255)."),
]


def evaluate(r: dict, today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    os_ = r.get("os") or {}
    build = os_.get("build") or 0
    caption = os_.get("caption") or ""
    is10 = "Windows 10" in caption
    admin = bool(r.get("admin"))
    out: dict[int, tuple[str, str]] = {}

    # 1-3 Sistema
    os_txt = f"{caption} {os_.get('display') or ''} (build {build}.{os_.get('ubr') or 0}, {os_.get('edition') or '—'})"
    if not os_:
        out[1] = (REVISION, "No se pudo leer el sistema operativo.")
    elif not is10:
        out[1] = (NO_APLICA, f"{os_txt}: el control es específico de Windows 10.")
    else:
        out[1] = (CUMPLE if build >= 19045 else NO_CUMPLE, os_txt)
    sup = SUPPORT_END.get(build)
    if sup is None:
        out[2] = (REVISION, f"{os_txt}: versión no incluida en la tabla de ciclo de vida de ScriptLens.")
    else:
        name, end = sup
        if any(k in (os_.get("edition") or "") for k in ("Enterprise", "Education")) and build != 19045:
            end = end.replace(year=end.year + 1)
        if today <= end:
            out[2] = (CUMPLE, f"{name}: soporte hasta {end.isoformat()} (ciclo de vida de Microsoft).")
        elif is10:
            out[2] = (REVISION, f"{name}: el soporte general terminó el {end.isoformat()}. Las actualizaciones extendidas (ESU) no se pueden verificar de forma fiable.")
        else:
            out[2] = (NO_CUMPLE, f"{name}: el soporte terminó el {end.isoformat()}.")
    hf = r.get("hotfix")
    if not hf:
        out[3] = (REVISION, "Get-HotFix no devolvió actualizaciones con fecha.")
    else:
        age = (today - dt.date.fromisoformat(hf["fecha"])).days
        ev = f"Última actualización registrada: {hf['id']} del {hf['fecha']} (hace {age} días). Get-HotFix no muestra todas las actualizaciones."
        out[3] = (CUMPLE if age <= 45 else REVISION, ev)

    # 4-6 Firewall
    fw = {p["name"]: p["enabled"] for p in (r.get("firewall") or [])}
    for n, prof in ((4, "Domain"), (5, "Private"), (6, "Public")):
        out[n] = (_bool(fw.get(prof)), f"Perfil {prof}: Enabled={_t(fw.get(prof))}")

    # 7-10 Defender (con antivirus de terceros, los controles propios de Defender no aplican)
    d = r.get("defender") or {}
    others = [a for a in (r.get("av_products") or []) if "defender" not in a.lower()]
    if d and d.get("av"):
        out[7] = (CUMPLE, f"Microsoft Defender activo (modo {d.get('mode') or '—'}). Productos registrados: {_t(r.get('av_products'))}")
    elif others:
        out[7] = (CUMPLE, f"Antivirus de terceros registrado en el Centro de seguridad: {_t(others)}")
    else:
        out[7] = (_bool(d.get("av")) if d else REVISION, f"AntivirusEnabled={_t(d.get('av'))}; productos: {_t(r.get('av_products'))}")
    third = bool(others) and not d.get("av")
    for n, key, label in ((8, "rtp", "RealTimeProtectionEnabled"), (9, "behavior", "BehaviorMonitorEnabled")):
        out[n] = (NO_APLICA, f"Defender en modo pasivo; protege {_t(others)}.") if third else (_bool(d.get(key)) if d else REVISION, f"{label}={_t(d.get(key))}")
    pua = r.get("pua")
    if third:
        out[10] = (NO_APLICA, f"Defender en modo pasivo; protege {_t(others)}.")
    else:
        out[10] = ({1: CUMPLE, 0: NO_CUMPLE}.get(pua, REVISION), f"PUAProtection={_t(pua)} (0 desactivado, 1 bloqueo, 2 solo auditoría)")

    # 11-16 Acceso remoto y SMB
    rdp = r.get("rdp_deny")
    out[11] = (REVISION if rdp is None else CUMPLE if rdp == 1 else REVISION, f"fDenyTSConnections={_t(rdp)} (1 = conexiones remotas denegadas)")
    nla = r.get("rdp_nla")
    out[12] = (NO_APLICA, "RDP deshabilitado: NLA no se usa.") if rdp == 1 else ((REVISION if nla is None else CUMPLE if nla == 1 else NO_CUMPLE), f"RDP habilitado; UserAuthentication={_t(nla)}")
    smb = r.get("smb_server") or {}
    s1 = smb.get("smb1")
    out[13] = (REVISION if s1 is None else CUMPLE if not s1 else NO_CUMPLE, f"EnableSMB1Protocol={_t(s1)} (fuente: {smb.get('origen', '—')})")
    out[14] = (_bool(smb.get("sign")), f"Servidor RequireSecuritySignature={_t(smb.get('sign'))}")
    out[15] = (_bool(r.get("smb_client_sign")), f"Cliente RequireSecuritySignature={_t(r.get('smb_client_sign'))}")
    w = r.get("winrm")
    if not w:
        out[16] = (REVISION, "No se pudo leer el servicio WinRM.")
    else:
        stopped = w["status"] == "Stopped" and w["start"] in ("Manual", "Disabled")
        out[16] = (CUMPLE if stopped else REVISION, f"Servicio WinRM: {w['status']}, inicio {w['start']}" + ("" if stopped else ". Confirmar si es necesario y revisar listeners y firewall."))

    # 17-22 Cuentas
    u = r.get("uac") or {}
    out[17] = (REVISION if u.get("lua") is None else CUMPLE if u["lua"] == 1 else NO_CUMPLE, f"EnableLUA={_t(u.get('lua'))}")
    c = u.get("consent")
    out[18] = (REVISION if c is None else NO_CUMPLE if c == 0 else CUMPLE, f"ConsentPromptBehaviorAdmin={_t(c)} (0 = eleva sin preguntar)")
    sd = u.get("secure")
    out[19] = (REVISION if sd is None else CUMPLE if sd == 1 else NO_CUMPLE, f"PromptOnSecureDesktop={_t(sd)}")
    out[20] = (_bool(r.get("guest_enabled"), False), f"Cuenta Invitado habilitada: {_t(r.get('guest_enabled'))}")
    out[21] = (_bool(r.get("admin_enabled"), False), f"Administrador integrado habilitado: {_t(r.get('admin_enabled'))}")
    na = r.get("net_accounts") or []
    # «net accounts» tiene un orden fijo en todos los idiomas: 4.ª línea = longitud mínima, 6.ª = umbral de bloqueo.
    try:
        minlen = int(na[3])
        lock_raw = na[5]
        lock = int(lock_raw) if lock_raw.isdigit() else 0
        ev = f"Longitud mínima: {minlen}; umbral de bloqueo: {lock_raw}; vigencia máxima: {na[2]} días (net accounts)"
        out[22] = (CUMPLE if minlen >= 8 and 1 <= lock <= 10 else NO_CUMPLE, ev + ". Las cuentas Microsoft siguen además su propia política en línea.")
    except (IndexError, ValueError):
        out[22] = (REVISION, "No se pudo interpretar la salida de «net accounts».")

    # 23-27 Cifrado, arranque y auditoría
    bl = r.get("bitlocker") or {}
    st = bl.get("estado")
    mapping = {"On": CUMPLE, "Off": NO_CUMPLE, 1: CUMPLE, 2: NO_CUMPLE}
    labels = {1: "protección activada", 2: "sin protección", 3: "cifrando", 4: "descifrando", 5: "suspendido", 6: "activado (bloqueado)"}
    out[23] = (mapping.get(st, REVISION), f"Estado de BitLocker: {labels.get(st, _t(st))} (fuente: {bl.get('origen', '—')})")
    sb = r.get("secureboot") or {}
    on = sb.get("on")
    out[24] = (REVISION if on is None else CUMPLE if bool(on) else NO_CUMPLE, f"Secure Boot: {_t(None if on is None else bool(on))} (fuente: {sb.get('origen', '—')})" + (". Puede que el equipo arranque en modo BIOS heredado." if on is None else ""))
    tpm = r.get("tpm") or {}
    if tpm.get("ready") is None:
        out[25] = (REVISION if tpm.get("present") else NO_CUMPLE if tpm.get("origen") == "Get-Tpm" else REVISION, f"TPM presente: {_t(tpm.get('present'))}; «preparado» no se puede comprobar sin administrador (fuente: {tpm.get('origen', '—')}).")
    else:
        out[25] = (CUMPLE if tpm.get("present") and tpm.get("ready") else NO_CUMPLE if not tpm.get("present") else REVISION, f"TpmPresent={_t(tpm.get('present'))}; TpmReady={_t(tpm.get('ready'))}")
    audit = r.get("audit") or []
    if not audit:
        out[26] = (REVISION, NEED_ADMIN + " auditpol /get requiere privilegios elevados.")
    else:
        vals = [a["valor"] for a in audit]
        none = [v for v in vals if any(k in v.lower() for k in ("no auditing", "sin auditor", "no audit"))]
        out[26] = (NO_CUMPLE if none else CUMPLE if len(vals) == 2 else REVISION, "; ".join(f"{a['sub']}: {a['valor']}" for a in audit))
    ps = r.get("ps_logging")
    out[27] = (REVISION if ps is None else CUMPLE if ps == 1 else NO_CUMPLE, f"EnableScriptBlockLogging={_t(ps)}" + (" (política no configurada)" if ps is None else ""))

    # 28-30 Recursos y servicios
    sh = r.get("shares")
    out[28] = (REVISION if sh is None else CUMPLE if not sh else REVISION, f"Carpetas compartidas no administrativas: {_t(sh)}")
    rr = r.get("remote_registry")
    out[29] = (REVISION, "No se pudo leer el servicio.") if not rr else ((CUMPLE if rr["status"] == "Stopped" and rr["start"] == "Disabled" else REVISION), f"Registro remoto: {rr['status']}, inicio {rr['start']}")
    ar = r.get("autorun") if r.get("autorun") is not None else r.get("autorun_user")
    out[30] = (REVISION if ar is None else CUMPLE if (int(ar) & 0xFF) == 0xFF else REVISION, f"NoDriveTypeAutoRun={_t(ar)}" + (" (política no configurada: Windows usa su valor predeterminado, que no cubre todas las unidades)" if ar is None else ""))

    results = []
    for n, area, nombre, proposito, explicacion, recomendacion in CONTROLS:
        estado, evidencia = out[n]
        results.append({"numero": n, "area": area, "nombre": nombre, "proposito": proposito, "estado": estado, "evidencia": evidencia, "explicacion": explicacion, "recomendacion": recomendacion if estado in (NO_CUMPLE, REVISION) else "Mantener la configuración actual."})
    counts = {k: sum(1 for x in results if x["estado"] == k) for k in (CUMPLE, NO_CUMPLE, REVISION, NO_APLICA)}
    concl = counts[CUMPLE] + counts[NO_CUMPLE]
    return {
        "administrador": admin,
        "sistema": os_txt,
        "controles": results,
        "resumen": counts,
        "cumplimiento_concluyente_pct": round(100 * counts[CUMPLE] / concl, 1) if concl else None,
        "nota": "El porcentaje solo considera los controles concluyentes (CUMPLE y NO CUMPLE). No es un índice validado de vulnerabilidad.",
    }
