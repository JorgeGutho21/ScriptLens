"""Herramientas internas del asistente: SOLO LECTURA y con parámetros validados.

El modelo de lenguaje no ejecuta comandos, no abre archivos y no llama a la API
de acciones. El enrutador decide qué herramientas consultar según la pregunta
y entrega al modelo únicamente sus resultados (datos medidos).

Todos los textos que provienen del equipo (nombres de procesos, rutas, comandos,
scripts) se tratan como DATOS NO CONFIABLES: se sanean y se marcan como tales.
"""

from __future__ import annotations

import re
import time
from collections import defaultdict

from backend.monitoring.diagnosis import summarize
from backend.processes import analysis
from backend.processes.knowledge import lookup
from backend.processes.winapi import visible_window_pids
from backend.storage import diagnostics as dg

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_FENCE = re.compile(r"(```|<\/?(datos|sistema|system|instrucciones)[^>]*>)", re.I)


def clean(value, limit: int = 160):
    """Sanea texto no confiable: sin caracteres de control, sin delimitadores, longitud acotada."""
    if value is None:
        return None
    s = _CTRL.sub(" ", str(value))
    s = _FENCE.sub("", s)
    return s[:limit]


def _mb(v) -> float | None:
    return round(v / 1024**2, 1) if v else None


def _grouped(engine, categories: set[str] | None = None) -> list[dict]:
    _, snaps = engine.processes.latest()
    windows = visible_window_pids()
    groups: dict[str, dict] = defaultdict(lambda: {"instancias": 0, "ram_mb": 0.0, "cpu_ahora": 0.0, "cpu_1min": 0.0, "tipos": set()})
    for s in snaps:
        if s.pid == 0 or not s.name:
            continue
        cat = analysis.category(s, windows)
        if categories and cat not in categories:
            continue
        g = groups[s.name]
        g["instancias"] += 1
        g["ram_mb"] += (s.memory_rss or 0) / 1024**2
        g["cpu_ahora"] += s.cpu_percent or 0
        st = engine.processes.stats(s.pid, s.create_time, 60)
        g["cpu_1min"] += (st or {}).get("cpu_avg") or 0
        g["tipos"].add(analysis.CATEGORY_ES[cat])
    out = []
    for name, g in groups.items():
        known = lookup(name)
        out.append(
            {
                "nombre": clean(name, 80),
                "instancias": g["instancias"],
                "ram_mb": round(g["ram_mb"], 1),
                "cpu_ahora_pct": round(g["cpu_ahora"], 1),
                "cpu_prom_1min_pct": round(g["cpu_1min"], 1),
                "tipo": ", ".join(sorted(g["tipos"])),
                "rol_conocido": known["rol"] if known else None,
            }
        )
    return out


def resumen_rendimiento(engine) -> dict:
    window = engine.sampler.history(60)
    info = engine.info()
    s = summarize(window, engine.sampler.history(), info["disks"])
    cur = s["current"] or {}
    return {
        "cpu_ahora_pct": cur.get("cpu_percent"),
        "cpu_prom_1min_pct": s["averages"]["cpu_1m"],
        "ram_ahora_pct": cur.get("mem_percent"),
        "ram_prom_1min_pct": s["averages"]["ram_1m"],
        "ram_usada_gb": round((cur.get("mem_used") or 0) / 1024**3, 1),
        "ram_total_gb": round((cur.get("mem_total") or 0) / 1024**3, 1),
        "procesos": cur.get("process_count"),
        "segundos_medidos": s["window_seconds"],
        "tiempo_encendido_h": round((time.time() - info["boot_time"]) / 3600, 1),
        "ultimo_arranque": time.strftime("%d/%m/%Y %H:%M", time.localtime(info["boot_time"])),
        "hallazgos": [{"estado": f["estado"], "titulo": f["titulo"], "evidencia": f["evidencia"]} for f in s["findings"]],
    }


def procesos_top(engine, by: str = "memory", n: int = 8) -> dict:
    if by not in ("memory", "cpu"):
        raise ValueError("by inválido")
    n = max(1, min(int(n), 10))
    rows = _grouped(engine)
    if by == "memory":
        rows.sort(key=lambda r: r["ram_mb"], reverse=True)
        return {"criterio": "memoria RAM", "programas": rows[:n]}
    measured = int(time.time() - getattr(engine.processes, "created", 0))
    out = {"criterio": "CPU promedio del último minuto", "segundos_medidos": min(measured, 60)}
    if measured < 60:
        # Recién iniciado: el promedio aún no cubre un minuto; se ordena también por el valor actual.
        rows.sort(key=lambda r: max(r["cpu_prom_1min_pct"], r["cpu_ahora_pct"]), reverse=True)
        out["nota"] = f"ScriptLens empezó a medir hace {measured} s: el promedio todavía no cubre un minuto completo y puede ser bajo. Use también cpu_ahora_pct."
    else:
        rows.sort(key=lambda r: r["cpu_prom_1min_pct"], reverse=True)
    out["programas"] = rows[:n]
    return out


def segundo_plano(engine) -> dict:
    rows = _grouped(engine, {"segundo_plano", "servicio"})
    rows.sort(key=lambda r: r["ram_mb"], reverse=True)
    _, snaps = engine.processes.latest()
    windows = visible_window_pids()
    cats = defaultdict(int)
    for s in snaps:
        if s.pid:
            cats[analysis.category(s, windows)] += 1
    return {"conteo_por_tipo": {analysis.CATEGORY_ES[k]: v for k, v in cats.items()}, "mayor_consumo_en_segundo_plano": rows[:10]}


def cerrables(engine) -> dict:
    rows = [r for r in _grouped(engine, {"aplicacion"}) if r["rol_conocido"] not in ("critico", "seguridad", "sistema")]
    rows = [r for r in rows if r["nombre"].lower() not in ("explorer.exe", "scriptlens.exe", "msedgewebview2.exe")]
    rows.sort(key=lambda r: r["ram_mb"], reverse=True)
    return {
        "aplicaciones_abiertas_no_esenciales": rows[:10],
        "nota": "Son programas con ventana abierta que no son componentes de Windows. Cerrarlos no afecta a Windows, pero puede perderse trabajo sin guardar.",
    }


def en_revision(engine) -> dict:
    _, snaps = engine.processes.latest()
    mem_total = engine.sampler.latest().mem_total if engine.sampler.latest() else None
    out = []
    for s in snaps:
        path = engine.paths.get(s.pid, s.create_time)
        sig = engine.signatures.get(path)
        stats = engine.processes.stats(s.pid, s.create_time, 60)
        sigs = analysis.signals(s, path, sig.to_dict() if sig else None, stats, mem_total, engine.detections_for(path))
        estado = analysis.overall(sigs)
        if estado in ("requiere_revision", "actividad_sospechosa", "amenaza_detectada", "consumo_elevado"):
            out.append({"nombre": clean(s.name, 80), "pid": s.pid, "estado": estado, "senales": [clean(x["titulo"]) for x in sigs if x["estado"] != "informativo"], "ruta": clean(path, 200)})
    return {"procesos": out[:15], "total": len(out), "auditoria_realizada": engine.security.result is not None}


def explicar_proceso(engine, nombre: str) -> dict:
    nombre = (nombre or "").strip().lower()
    _, snaps = engine.processes.latest()
    matches = [s for s in snaps if s.name.lower() == nombre or s.name.lower() == nombre + ".exe"]
    known = lookup(nombre if nombre.endswith(".exe") or " " in nombre else nombre + ".exe") or lookup(nombre)
    if not matches:
        return {"encontrado": False, "nombre": clean(nombre, 80), "conocimiento": known["que"] if known else None}
    s = max(matches, key=lambda x: x.memory_rss or 0)
    path = engine.paths.get(s.pid, s.create_time)
    sig = engine.signatures.verify_now(path) if path else None
    return {
        "encontrado": True,
        "nombre": clean(s.name, 80),
        "instancias": len(matches),
        "ram_total_mb": round(sum((m.memory_rss or 0) for m in matches) / 1024**2, 1),
        "ruta": clean(path, 200),
        "firma": sig.descripcion_estado if sig else "no verificada",
        "firmante": clean(sig.firmante, 100) if sig else None,
        "descripcion_archivo": clean(sig.descripcion, 120) if sig else None,
        "editor": clean(sig.editor, 100) if sig else None,
        "conocimiento": known["que"] if known else None,
        "rol": known["rol"] if known else "desconocido",
        "se_puede_finalizar_desde_scriptlens": analysis.can_terminate(s.name, s.pid, engine.own_pids)[0],
    }


def seguridad(engine, ejecutar: bool = True) -> dict:
    st = engine.security
    if st.result is None and ejecutar:
        st.run()  # auditoría de solo lectura (tarda unos segundos)
    r = st.result
    if r is None:
        return {"disponible": False}
    d = r.get("defender") or {}
    return {
        "disponible": True,
        "medido": time.strftime("%Y-%m-%d %H:%M", time.localtime(r["measured_at"])),
        "antivirus_activo": d.get("AntivirusEnabled"),
        "proteccion_tiempo_real": d.get("RealTimeProtectionEnabled"),
        "antiguedad_definiciones_dias": d.get("AntivirusSignatureAge"),
        "firewall": {p["Name"]: p["Enabled"] for p in r["firewall"]},
        "amenazas_activas_defender": r["counts"].get("amenaza_detectada", 0),
        "hallazgos": [{"estado": f["estado"], "que": clean(f["que"], 160), "donde": clean(f["donde"], 160), "que_hacer": f["que_hacer"]} for f in r["findings"][:10]],
    }


def inicio_automatico(engine) -> dict:
    seguridad(engine)
    r = engine.security.result
    if r is None:
        return {"disponible": False}
    entries = r["startup"]
    return {
        # Resumen explícito: todos los «habilitados» se inician con Windows, tengan o no advertencias.
        "se_inician_con_windows": [clean(e["nombre"], 80) for e in entries if e["habilitado"]],
        "deshabilitados": [clean(e["nombre"], 80) for e in entries if not e["habilitado"]],
        "entradas": [
            {"nombre": clean(e["nombre"], 80), "habilitado": e["habilitado"], "origen": e["origen"], "firma": (e.get("firma") or {}).get("descripcion_estado"), "estado": e["estado"], "motivos": e["motivos"]}
            for e in entries
        ],
    }


def tareas(engine, nombre: str | None = None) -> dict:
    seguridad(engine)
    r = engine.security.result
    if r is None:
        return {"disponible": False}
    tasks = r["tasks"]["otras"]
    if nombre:
        tasks = [t for t in tasks if nombre.lower() in (t["nombre"] or "").lower()]
    return {
        "total_activas": r["tasks"]["total"],
        "de_windows": r["tasks"]["de_microsoft"],
        "de_otros_programas": [
            {"nombre": clean(t["nombre"], 100), "autor": clean(t["autor"], 80), "accion": clean(" ".join(f"{a.get('exe') or ''} {a.get('args') or ''}" for a in t["acciones"]), 200), "estado": t["estado"], "motivos": t["motivos"]}
            for t in tasks[:15]
        ],
    }


def disco(engine) -> dict:
    info = engine.info()
    return {"unidades": [{"unidad": d["mountpoint"], "usado_pct": d["percent"], "libre_gb": round(d["free"] / 1024**3, 1), "total_gb": round(d["total"] / 1024**3, 1)} for d in info["disks"]]}


def cambios(engine) -> dict:
    saved = dg.listing(engine.db)
    if not saved:
        return {"disponible": False, "motivo": "No hay diagnósticos guardados para comparar. Guarde uno en «Comparar mi PC»."}
    last = dg.load(engine.db, saved[0]["id"])
    try:
        now = dg.capture(engine)
    except ValueError:
        return {"disponible": False, "motivo": "Aún no hay mediciones actuales."}
    now["label"] = "Ahora"
    c = dg.compare(last, now)
    return {"disponible": True, "desde": f"{last['label']} ({time.strftime('%Y-%m-%d %H:%M', time.localtime(last['created_at']))})", "resumen": c["summary"], "metricas": c["metrics"], "procesos_con_mas_cambio": [{k: p[k] for k in ("name", "estado", "memory_delta")} for p in c["processes"][:6]]}


def ultimo_script(engine) -> dict:
    r = engine.last_script_analysis
    if r is None:
        return {"disponible": False, "motivo": "Primero analice un script en la sección «Analizar scripts»."}
    return {
        "disponible": True,
        "archivo": clean(r["archivo"], 120),
        "tipo": r["tipo"],
        "decision_hibrida": r["clasificacion"]["hibrida"],
        "severidad": r["severidad"]["nivel"],
        "tecnicas": [f"{t['id']} {t['nombre']}" for t in r["tecnicas"]],
        "lineas": [{"n": l["linea"], "codigo": clean(l["codigo"], 160), "explicacion": l["explicacion"]} for l in r["explicacion_lineas"][:60]],
        "posible_ciclo_infinito": r["flujo"]["posible_ciclo_infinito"],
        "limitaciones": r["limitaciones"],
    }


def efecto_desactivar_inicio(engine, nombre: str | None) -> dict:
    data = inicio_automatico(engine)
    entradas = data.get("entradas", [])
    match = [e for e in entradas if nombre and nombre.lower() in e["nombre"].lower()]
    return {
        "entradas_coincidentes": match,
        "todas_las_entradas": [e["nombre"] for e in entradas],
        "efecto_general": "Desactivar una entrada solo evita que el programa se abra solo al iniciar sesión; no lo desinstala ni borra archivos y se puede revertir desde ScriptLens o desde Configuración → Aplicaciones → Inicio.",
    }


REGISTRY = {
    "resumen_rendimiento": resumen_rendimiento,
    "procesos_top_memoria": lambda e: procesos_top(e, "memory"),
    "procesos_top_cpu": lambda e: procesos_top(e, "cpu"),
    "segundo_plano": segundo_plano,
    "cerrables": cerrables,
    "en_revision": en_revision,
    "seguridad": seguridad,
    "inicio_automatico": inicio_automatico,
    "tareas": tareas,
    "disco": disco,
    "cambios": cambios,
    "ultimo_script": ultimo_script,
}
