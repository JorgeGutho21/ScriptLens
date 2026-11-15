"""Reúne los datos de un informe a partir de mediciones reales del momento."""

from __future__ import annotations

import platform
import time

from backend.assistant import tools
from backend.core.config import APP_NAME, APP_VERSION, AUTHOR, AUTHOR_GITHUB, REPOSITORY_URL
from backend.storage import diagnostics as dg

WATERMARK = f"{APP_NAME} · {AUTHOR} · {AUTHOR_GITHUB}"


def recommendations(perf: dict, sec: dict | None, top_mem: list[dict], disks: list[dict]) -> list[str]:
    out = []
    if (perf.get("ram_prom_1min_pct") or 0) >= 85:
        names = ", ".join(p["nombre"] for p in top_mem[:3])
        out.append(f"La memoria RAM está muy ocupada ({perf['ram_prom_1min_pct']} % en promedio). Cierre programas que no use; los que más memoria ocupan son: {names}.")
    if (perf.get("cpu_prom_1min_pct") or 0) >= 80:
        out.append("El procesador estuvo muy ocupado durante el último minuto. Revise en «Procesos» cuál consume más de forma sostenida.")
    for d in disks:
        if d["usado_pct"] >= 90:
            out.append(f"La unidad {d['unidad']} tiene poco espacio ({d['libre_gb']} GB libres). Revise sus archivos grandes; ScriptLens no borra archivos personales.")
    if sec and sec.get("disponible"):
        if sec.get("proteccion_tiempo_real") is False:
            out.append("Active la protección en tiempo real de Microsoft Defender.")
        if any(not v for v in (sec.get("firewall") or {}).values()):
            out.append("Active el firewall de Windows en todos los perfiles.")
        if sec.get("amenazas_activas_defender"):
            out.append("Microsoft Defender registró amenazas activas: abra Seguridad de Windows → Historial de protección y siga sus indicaciones.")
        for h in sec.get("hallazgos", []):
            if h["estado"] == "requiere_revision":
                out.append(f"Revise: {h['que']}. {h['que_hacer']}")
    if not out:
        out.append("No se identificaron acciones necesarias: el equipo funciona con normalidad según las mediciones disponibles.")
    return out[:10]


def collect(engine, include_security: bool = True, compare_with: int | None = None) -> dict:
    info = engine.info()
    perf = tools.resumen_rendimiento(engine)
    top_mem = tools.procesos_top(engine, "memory", 10)["programas"]
    top_cpu = tools.procesos_top(engine, "cpu", 10)["programas"]
    disks = tools.disco(engine)["unidades"]
    sec = tools.seguridad(engine, ejecutar=include_security) if include_security else None
    review = tools.en_revision(engine)
    comparison = None
    if compare_with is not None:
        a = dg.load(engine.db, compare_with)
        if a:
            now = dg.capture(engine)
            now["label"] = "Momento del informe"
            comparison = dg.compare(a, now)
    actions = engine.db.actions(20)
    limitations = [
        "Las métricas corresponden al último minuto medido antes de generar el informe; no representan todo el día.",
        "ScriptLens no es un antivirus: solo las detecciones de Microsoft Defender se consideran amenazas confirmadas.",
        "Algunos datos (usuario de procesos de sistema, historial de amenazas) pueden requerir permisos de administrador y aparecer como no disponibles.",
        "Los consumos de memoria por proceso usan el conjunto de trabajo (working set); pueden diferir levemente del Administrador de tareas.",
    ]
    if not info["temperature"]["available"]:
        limitations.append("La temperatura del hardware no está disponible en Windows mediante las API usadas.")
    return {
        "meta": {
            "titulo": "Informe de diagnóstico del equipo",
            "app": APP_NAME,
            "version": APP_VERSION,
            "autor": AUTHOR,
            "github": AUTHOR_GITHUB,
            "repositorio": REPOSITORY_URL,
            "generado": time.strftime("%Y-%m-%d %H:%M:%S"),
            "marca_agua": WATERMARK,
        },
        "sistema": {
            "so": f"{info['os']} ({info['os_version']})",
            "procesador": info["processor"],
            "nucleos": f"{info['cpu_physical']} físicos / {info['cpu_logical']} lógicos",
            "ram_total_gb": round(info["mem_total"] / 1024**3, 1),
            "equipo": platform.node(),
        },
        "rendimiento": perf,
        "top_memoria": top_mem,
        "top_cpu": top_cpu,
        "discos": disks,
        "seguridad": sec,
        "procesos_revision": review,
        "recomendaciones": recommendations(perf, sec, top_mem, disks),
        "acciones": actions,
        "comparacion": comparison,
        "limitaciones": limitations,
    }
