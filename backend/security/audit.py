"""Reglas de auditoría y hallazgos de seguridad.

Cada hallazgo responde a las ocho preguntas del requisito: qué se encontró,
dónde, por qué requiere revisión, qué evidencia existe, qué información falta,
qué consecuencias podría tener, qué puede hacer el usuario y qué NO conviene hacer.

Estados: informativo · normal · consumo_elevado · requiere_revision ·
actividad_sospechosa · amenaza_detectada · info_insuficiente.
ScriptLens no es un antivirus: solo «amenaza_detectada» proviene de una
herramienta de seguridad (Microsoft Defender); el resto son señales para revisar.
"""

from __future__ import annotations

import os
import re
import time

from backend.processes.signatures import verify_batch

SCRIPT_HOSTS = re.compile(r"(?i)\b(powershell|pwsh|wscript|cscript|mshta|cmd(\.exe)?\s*/c|rundll32|regsvr32)\b|\.(bat|cmd|vbs|vbe|js|jse|ps1|hta)\b")
HIDDEN_FLAGS = re.compile(r"(?i)(-w(indowstyle)?\s+hidden|-enc(odedcommand)?\s|-nop\b|bypass|frombase64string|downloadstring|iex\b|invoke-expression)")
USER_WRITABLE = ("\\appdata\\local\\temp\\", "\\windows\\temp\\", "\\users\\public\\", "\\$recycle.bin\\", "\\downloads\\")

THREAT_STATUS = {
    0: "estado desconocido",
    1: "detectada",
    2: "limpiada",
    3: "en cuarentena",
    4: "eliminada",
    5: "permitida por el usuario",
    6: "bloqueada",
    102: "falló la cuarentena",
    103: "falló la eliminación",
    104: "falló el permiso",
    105: "abandonada",
    107: "falló el bloqueo",
}
RESOLVED = {2, 3, 4, 6}

NOTABLE_EVENTS = {
    ("Microsoft-Windows-Kernel-Power", 41): ("El equipo se reinició sin apagarse correctamente (corte de energía, bloqueo o botón de apagado).", "requiere_revision"),
    ("EventLog", 6008): ("El apagado anterior fue inesperado.", "informativo"),
    ("Microsoft-Windows-WER-SystemErrorReporting", 1001): ("Windows se recuperó de un error grave (pantalla azul).", "requiere_revision"),
    ("disk", 7): ("El disco informó sectores defectuosos.", "requiere_revision"),
    ("disk", 11): ("El controlador detectó un error en el disco.", "requiere_revision"),
    ("disk", 153): ("Una operación de disco se reintentó.", "informativo"),
    ("Ntfs", 55): ("Se detectó daño en la estructura de archivos del disco.", "requiere_revision"),
    ("Microsoft-Windows-WHEA-Logger", 18): ("El hardware informó un error grave.", "requiere_revision"),
    ("Microsoft-Windows-WHEA-Logger", 1): ("El hardware informó un error corregido.", "informativo"),
}


def finding(code, estado, categoria, que, donde, por_que, evidencia, falta, consecuencias, que_hacer, no_hacer, fuente, medido_en) -> dict:
    return {
        "code": code,
        "estado": estado,
        "categoria": categoria,
        "que": que,
        "donde": donde,
        "por_que": por_que,
        "evidencia": evidencia,
        "falta": falta,
        "consecuencias": consecuencias,
        "que_hacer": que_hacer,
        "no_hacer": no_hacer,
        "fuente": fuente,
        "medido_en": medido_en,
    }


def _err(v) -> str | None:
    if isinstance(v, dict) and set(v) == {"error"}:
        return v["error"]
    return None


def _as_list(v) -> list:
    if v is None or _err(v):
        return []
    return v if isinstance(v, list) else [v]


def _is_microsoft(sig: dict | None) -> bool:
    return bool(sig and sig.get("estado") == "valida" and "microsoft" in (sig.get("firmante") or "").lower())


def evaluate(raw: dict) -> dict:
    t = raw.get("measured_at", time.time())
    findings: list[dict] = []
    sources: dict[str, dict] = {}

    def source(name, value, label):
        e = _err(value)
        sources[name] = {"etiqueta": label, "ok": e is None and value is not None, "error": e, "registros": len(_as_list(value)) if e is None else 0}

    for key, label in [
        ("defender", "Microsoft Defender (estado)"),
        ("threats", "Microsoft Defender (amenazas)"),
        ("detections", "Microsoft Defender (detecciones)"),
        ("av_products", "Centro de seguridad de Windows"),
        ("firewall", "Firewall de Windows"),
        ("tasks", "Tareas programadas"),
        ("events", "Registro de eventos del Sistema (7 días)"),
        ("users", "Cuentas locales"),
        ("startup", "Inicio automático (Registro y carpetas)"),
        ("services", "Servicios"),
    ]:
        source(key, raw.get(key), label)

    # --- Verificación de firmas de lo que arranca automáticamente -------------
    startup = _as_list(raw.get("startup"))
    tasks = _as_list(raw.get("tasks"))
    services = _as_list(raw.get("services"))
    third_tasks = [tk for tk in tasks if not (tk.get("path") or "").startswith("\\Microsoft\\")]
    auto_services = [s for s in services if s.get("inicio") == "automatic" and s.get("ejecutable") and not s["ejecutable"].lower().startswith("c:\\windows\\")]
    paths = set()
    for e in startup:
        if e.get("ejecutable") and os.path.isfile(e["ejecutable"]):
            paths.add(e["ejecutable"])
    for tk in third_tasks:
        for a in tk.get("actions") or []:
            exe = os.path.expandvars((a.get("exe") or "").strip('"'))
            if exe and os.path.isfile(exe):
                paths.add(exe)
    for s in auto_services:
        if os.path.isfile(s["ejecutable"]):
            paths.add(s["ejecutable"])
    try:
        sigs = {i.path.lower(): i.to_dict() for i in verify_batch(sorted(paths))}
    except Exception:  # noqa: BLE001
        sigs = {}

    # --- Defender ------------------------------------------------------------
    d = raw.get("defender")
    av = _as_list(raw.get("av_products"))
    defender = None
    if _err(d) or not d:
        other = [p.get("displayName") for p in av if "defender" not in (p.get("displayName") or "").lower()]
        findings.append(
            finding(
                "defender_no_disponible",
                "informativo" if other else "info_insuficiente",
                "Protección",
                "No se pudo consultar el estado de Microsoft Defender",
                "Microsoft Defender",
                "Puede deberse a que otro antivirus está activo o a permisos insuficientes.",
                f"Antivirus registrados en Windows: {', '.join(p.get('displayName') or '?' for p in av) or 'ninguno informado'}.",
                "El estado detallado de la protección en tiempo real.",
                "Si no hay ningún antivirus activo, el equipo queda más expuesto.",
                "Abra «Seguridad de Windows» y compruebe que un antivirus esté activo.",
                "No instale varios antivirus a la vez: pueden interferir entre sí.",
                "Get-MpComputerStatus / SecurityCenter2",
                t,
            )
        )
    else:
        defender = d
        if not d.get("AntivirusEnabled") or not d.get("RealTimeProtectionEnabled"):
            findings.append(
                finding(
                    "proteccion_desactivada",
                    "requiere_revision",
                    "Protección",
                    "La protección en tiempo real de Microsoft Defender está desactivada",
                    "Seguridad de Windows → Protección antivirus y contra amenazas",
                    "Sin protección en tiempo real, los archivos no se analizan al abrirse o descargarse.",
                    f"AntivirusEnabled={d.get('AntivirusEnabled')}, RealTimeProtectionEnabled={d.get('RealTimeProtectionEnabled')}",
                    "Si otro antivirus de confianza está protegiendo el equipo.",
                    "Mayor exposición a programas maliciosos.",
                    "Active la protección en tiempo real desde Seguridad de Windows, salvo que use otro antivirus.",
                    "No desactive la protección para «acelerar» el equipo.",
                    "Get-MpComputerStatus",
                    t,
                )
            )
        age = d.get("AntivirusSignatureAge")
        if isinstance(age, int) and 7 <= age < 4000:
            findings.append(
                finding(
                    "firmas_desactualizadas",
                    "requiere_revision",
                    "Protección",
                    "Las definiciones del antivirus están desactualizadas",
                    "Microsoft Defender",
                    "Las definiciones permiten reconocer amenazas recientes.",
                    f"Antigüedad de las definiciones: {age} días.",
                    "Si el equipo ha estado sin conexión.",
                    "Las amenazas nuevas podrían no detectarse.",
                    "Abra Windows Update o Seguridad de Windows y busque actualizaciones.",
                    "No descargue «actualizaciones de antivirus» desde sitios no oficiales.",
                    "Get-MpComputerStatus",
                    t,
                )
            )
        if d.get("IsTamperProtected") is False:
            findings.append(
                finding(
                    "tamper_off",
                    "informativo",
                    "Protección",
                    "La protección contra alteraciones está desactivada",
                    "Seguridad de Windows → Configuración de antivirus",
                    "Impide que otros programas cambien la configuración de Defender.",
                    "IsTamperProtected=False",
                    "Si una política de la organización la administra.",
                    "Un programa podría desactivar la protección sin avisar.",
                    "Actívela en Seguridad de Windows si el equipo es personal.",
                    "No la desactive salvo que un técnico de confianza lo indique.",
                    "Get-MpComputerStatus",
                    t,
                )
            )

    # --- Amenazas registradas por Defender -----------------------------------
    threats = {x.get("ThreatID"): x for x in _as_list(raw.get("threats"))}
    detections = _as_list(raw.get("detections"))
    det_error = _err(raw.get("detections")) or _err(raw.get("threats"))
    if det_error:
        findings.append(
            finding(
                "historial_amenazas_inaccesible",
                "info_insuficiente",
                "Protección",
                "No se pudo leer el historial de amenazas de Defender",
                "Microsoft Defender",
                "Windows puede exigir permisos de administrador para esta consulta.",
                det_error[:200],
                "El historial de detecciones.",
                "No es posible confirmar si hubo detecciones recientes.",
                "Revise «Historial de protección» en Seguridad de Windows.",
                "No suponga que el equipo está libre de amenazas solo por este resultado.",
                "Get-MpThreatDetection",
                t,
            )
        )
    for det in detections:
        th = threats.get(det.get("ThreatID"), {})
        status = det.get("ThreatStatusID")
        resolved = status in RESOLVED
        res = det.get("Resources") or []
        res = res if isinstance(res, list) else [res]
        findings.append(
            finding(
                f"amenaza_{det.get('ThreatID')}_{det.get('Time')}",
                "informativo" if resolved else "amenaza_detectada",
                "Amenazas",
                f"Microsoft Defender detectó «{th.get('ThreatName') or det.get('ThreatID')}»",
                "; ".join(str(r) for r in res[:3]) or "Recurso no informado",
                "La detección proviene de Microsoft Defender, no de ScriptLens.",
                f"Estado: {THREAT_STATUS.get(status, status)}. Fecha: {det.get('Time')}. Gravedad (1-5): {th.get('SeverityID', '?')}.",
                "Cómo llegó el archivo al equipo.",
                "Si no fue neutralizada, podría afectar sus datos o su privacidad." if not resolved else "Defender ya la neutralizó.",
                "Abra Seguridad de Windows → Historial de protección y siga las acciones recomendadas por Defender.",
                "No restaure ni permita el archivo si no está seguro de su origen.",
                "Get-MpThreatDetection",
                t,
            )
        )

    # --- Firewall ------------------------------------------------------------
    fw = _as_list(raw.get("firewall"))
    off = [p["Name"] for p in fw if not p.get("Enabled")]
    if off:
        findings.append(
            finding(
                "firewall_desactivado",
                "requiere_revision",
                "Red",
                "El firewall de Windows está desactivado en algunos perfiles",
                "Firewall de Windows Defender",
                "El firewall bloquea conexiones no autorizadas desde la red.",
                f"Perfiles desactivados: {', '.join(off)}.",
                "Si otro firewall de confianza está activo.",
                "Otros equipos de la red podrían conectarse a servicios de este computador.",
                "Active el firewall en Seguridad de Windows → Firewall y protección de red.",
                "No lo desactive para que un programa «funcione»; cree una excepción si es necesario.",
                "Get-NetFirewallProfile",
                t,
            )
        )

    # --- Inicio automático ---------------------------------------------------
    startup_out = []
    for e in startup:
        exe = e.get("ejecutable") or ""
        sig = sigs.get(exe.lower())
        cmd = e.get("comando") or ""
        low = exe.lower()
        issues = []
        if e.get("habilitado") and SCRIPT_HOSTS.search(cmd):
            issues.append(("Ejecuta un script o un intérprete de comandos al iniciar Windows", "requiere_revision"))
        if e.get("habilitado") and HIDDEN_FLAGS.search(cmd):
            issues.append(("La orden incluye opciones de ejecución oculta o código codificado", "requiere_revision"))
        if any(p in low for p in USER_WRITABLE):
            issues.append(("El programa está en una carpeta temporal, pública o de descargas", "requiere_revision"))
        if re.search(r"(?i)microsoft|windows", e.get("nombre") or "") and not _is_microsoft(sig) and e.get("habilitado"):
            issues.append(("El nombre alude a Microsoft o Windows, pero el archivo no está firmado por Microsoft", "requiere_revision"))
        if exe and not os.path.exists(exe):
            issues.append(("La entrada apunta a un archivo que no existe", "informativo"))
        estado = "requiere_revision" if any(s == "requiere_revision" for _, s in issues) else ("informativo" if issues else "normal")
        item = {**e, "firma": sig, "estado": estado, "motivos": [m for m, _ in issues]}
        startup_out.append(item)
        if estado == "requiere_revision":
            findings.append(
                finding(
                    f"inicio_{e['id']}",
                    "requiere_revision",
                    "Inicio automático",
                    f"Entrada de inicio automático «{e['nombre']}»",
                    f"{e['origen']} → {cmd}",
                    "; ".join(item["motivos"]) + ".",
                    f"Firma: {sig['descripcion_estado'] if sig else 'no verificable'}" + (f" ({sig['firmante']})" if sig and sig.get("firmante") else "") + f". Habilitada: {'sí' if e.get('habilitado') else 'no'}.",
                    "Quién creó la entrada y qué hace exactamente el archivo.",
                    "Se ejecuta cada vez que inicia sesión; si no es confiable, podría persistir en el equipo.",
                    "Si no reconoce el programa, analícelo en «Analizar scripts» (si es un script) y desactive la entrada desde «Inicio automático».",
                    "No borre el archivo a ciegas: primero desactive la entrada y compruebe que nada deja de funcionar.",
                    "Registro de Windows (Run/RunOnce) y carpetas de Inicio",
                    t,
                )
            )

    # --- Tareas programadas ----------------------------------------------------
    tasks_out = []
    for tk in third_tasks:
        acts = tk.get("actions") or []
        text = " ".join(f"{a.get('exe') or ''} {a.get('args') or ''}" for a in acts)
        exe0 = os.path.expandvars(((acts[0].get("exe") if acts else "") or "").strip('"'))
        sig = sigs.get(exe0.lower())
        issues = []
        if HIDDEN_FLAGS.search(text):
            issues.append("Incluye opciones de ejecución oculta o código codificado")
        if SCRIPT_HOSTS.search(text):
            issues.append("Ejecuta un script o un intérprete de comandos")
        if any(p in text.lower() for p in USER_WRITABLE):
            issues.append("Usa archivos en una carpeta temporal, pública o de descargas")
        estado = "requiere_revision" if issues else "normal"
        tasks_out.append({"nombre": tk.get("name"), "ruta": tk.get("path"), "estado_tarea": tk.get("state"), "autor": tk.get("author"), "acciones": acts, "disparadores": tk.get("triggers"), "firma": sig, "estado": estado, "motivos": issues})
        if issues:
            findings.append(
                finding(
                    f"tarea_{tk.get('path')}{tk.get('name')}",
                    "requiere_revision",
                    "Tareas programadas",
                    f"Tarea programada «{tk.get('name')}»",
                    f"Programador de tareas{tk.get('path')}",
                    "; ".join(issues) + ".",
                    f"Acción: {text.strip()[:300]}. Autor: {tk.get('author') or 'no indicado'}.",
                    "Quién creó la tarea y con qué propósito.",
                    "Las tareas se ejecutan automáticamente y pueden mantener programas activos sin que el usuario lo note.",
                    "Abra el Programador de tareas de Windows para revisarla; si no la reconoce, analícela antes de desactivarla.",
                    "No elimine tareas de Microsoft ni de controladores (audio, vídeo): pueden ser necesarias.",
                    "Get-ScheduledTask",
                    t,
                )
            )

    # --- Servicios -------------------------------------------------------------
    flagged_services = []
    for s in auto_services:
        low = (s.get("ejecutable") or "").lower()
        if any(p in low for p in USER_WRITABLE):
            flagged_services.append(s)
            findings.append(
                finding(
                    f"servicio_{s['nombre']}",
                    "requiere_revision",
                    "Servicios",
                    f"Servicio «{s.get('mostrado') or s['nombre']}» ejecutado desde una carpeta inusual",
                    s.get("binario") or "",
                    "Los servicios normales se instalan en Program Files o en Windows.",
                    f"Inicio: {s.get('inicio')}, estado: {s.get('estado')}. Firma: {(sigs.get(low) or {}).get('descripcion_estado', 'no verificada')}.",
                    "Qué programa instaló el servicio.",
                    "Un servicio funciona con privilegios elevados y arranca con Windows.",
                    "Investigue el servicio en «Servicios» de Windows o consulte a un técnico.",
                    "No detenga servicios que no conoce sin investigar: algunos son necesarios.",
                    "psutil.win_service_iter",
                    t,
                )
            )

    # --- Eventos ---------------------------------------------------------------
    events = _as_list(raw.get("events"))
    groups: dict[tuple, dict] = {}
    for ev in events:
        key = (ev.get("ProviderName"), ev.get("Id"))
        g = groups.setdefault(key, {"proveedor": key[0], "id": key[1], "nivel": ev.get("LevelDisplayName"), "veces": 0, "ultima": ev.get("Time")})
        g["veces"] += 1
    event_groups = sorted(groups.values(), key=lambda g: g["veces"], reverse=True)
    for (prov, eid), (text, estado) in NOTABLE_EVENTS.items():
        g = groups.get((prov, eid))
        if g:
            findings.append(
                finding(
                    f"evento_{prov}_{eid}",
                    estado,
                    "Eventos del sistema",
                    text,
                    f"Visor de eventos → Sistema → {prov} (ID {eid})",
                    "Windows registró este evento en los últimos 7 días.",
                    f"{g['veces']} vez/veces; última: {g['ultima']}.",
                    "La causa exacta (puede requerir revisar el hardware o los controladores).",
                    "Puede indicar inestabilidad del sistema o del hardware.",
                    "Si se repite, guarde su trabajo con frecuencia y consulte el Visor de eventos o a un técnico.",
                    "No ejecute «limpiadores de registro» para corregir estos errores.",
                    "Get-WinEvent (System)",
                    t,
                )
            )

    # --- Cuentas ---------------------------------------------------------------
    users = _as_list(raw.get("users"))
    guest = [u for u in users if (u.get("Sid") or "").endswith("-501") and u.get("Enabled")]
    admin = [u for u in users if (u.get("Sid") or "").endswith("-500") and u.get("Enabled")]
    if guest:
        findings.append(
            finding("invitado_activo", "requiere_revision", "Cuentas", "La cuenta de invitado está habilitada", "Cuentas locales de Windows", "Permite usar el equipo sin contraseña.", "Cuenta integrada de invitado (SID terminado en 501) habilitada.", "Si se habilitó intencionalmente.", "Otra persona podría usar el equipo sin credenciales.", "Deshabilítela desde Administración de equipos si no la necesita.", "No comparta cuentas con privilegios de administrador.", "Get-LocalUser", t)
        )
    if admin:
        findings.append(
            finding("admin_integrado", "informativo", "Cuentas", "La cuenta integrada «Administrador» está habilitada", "Cuentas locales de Windows", "Es una cuenta con todos los privilegios que normalmente permanece deshabilitada.", "SID terminado en 500 habilitado.", "Si se activó a propósito.", "Si su contraseña es débil, el equipo es más vulnerable.", "Use una cuenta normal para el trabajo diario.", "No navegue por Internet con la cuenta de administrador.", "Get-LocalUser", t)
        )

    # --- Plan de energía (rendimiento) ---------------------------------------
    power = raw.get("power") if isinstance(raw.get("power"), str) else None
    m = re.search(r"\(([^)]+)\)\s*$", power or "")
    power_name = m.group(1) if m else None
    if power_name and re.search(r"(?i)econom|ahorro|saver", power_name):
        findings.append(
            finding("plan_ahorro", "informativo", "Rendimiento", f"Plan de energía «{power_name}»", "Configuración → Sistema → Inicio/apagado y batería", "Este plan reduce el rendimiento para ahorrar energía.", power or "", "—", "El equipo puede responder más lento.", "Use «Equilibrado» si el equipo está conectado a la corriente.", "No use herramientas de terceros que modifiquen planes ocultos.", "powercfg /getactivescheme", t)
        )

    counts: dict[str, int] = {}
    for f in findings:
        counts[f["estado"]] = counts.get(f["estado"], 0) + 1

    return {
        "measured_at": t,
        "duration_s": raw.get("duration_s"),
        "sources": sources,
        "defender": defender,
        "av_products": av,
        "firewall": fw,
        "startup": startup_out,
        "tasks": {"total": len(tasks), "de_microsoft": len(tasks) - len(third_tasks), "otras": tasks_out},
        "services": {
            "total": len(services),
            "en_ejecucion": sum(1 for s in services if s.get("estado") == "running"),
            "automaticos": sum(1 for s in services if s.get("inicio") == "automatic"),
            "de_terceros_automaticos": [{**s, "firma": sigs.get((s.get("ejecutable") or "").lower())} for s in auto_services],
            "revisar": flagged_services,
        },
        "events": {"total": len(events), "grupos": event_groups[:25]},
        "users": {"total": len(users), "habilitadas": sum(1 for u in users if u.get("Enabled")), "sesiones": len(raw.get("sessions") or [])},
        "power_plan": power_name,
        "findings": sorted(findings, key=lambda f: ["amenaza_detectada", "actividad_sospechosa", "requiere_revision", "info_insuficiente", "consumo_elevado", "informativo", "normal"].index(f["estado"])),
        "counts": counts,
    }
