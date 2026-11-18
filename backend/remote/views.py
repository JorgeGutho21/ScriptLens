"""Datos que la PC comparte en modo remoto. Solo lectura y sin rutas, comandos ni datos personales.

Se construyen a partir del mismo ``Engine`` que usa la interfaz local, de modo que no se
duplica ningún muestreo. Cada respuesta indica cuándo se midió (``medido_en``) para que el
dispositivo remoto nunca presente cifras antiguas como actuales.
"""

from __future__ import annotations

import time

from backend.assistant import tools
from backend.core.config import APP_VERSION

from .netinfo import device_name

_SAMPLE_FIELDS = ("ts", "cpu_percent", "cpu_per_core", "mem_total", "mem_used", "mem_percent", "swap_percent", "disk_read_bps", "disk_write_bps", "net_sent_bps", "net_recv_bps", "process_count")


def _sample(s) -> dict | None:
    if s is None:
        return None
    d = s.to_dict()
    return {k: d[k] for k in _SAMPLE_FIELDS}


def overview(engine, device_id: str) -> dict:
    info = engine.info()
    s = engine.sampler.latest()
    return {
        "device_id": device_id,
        "equipo": device_name(),
        "version": APP_VERSION,
        "so": info["os"],
        "so_version": info["os_version"],
        "procesador": info["processor"],
        "nucleos_fisicos": info["cpu_physical"],
        "nucleos_logicos": info["cpu_logical"],
        "ram_total": info["mem_total"],
        "arranque": info["boot_time"],
        "tiempo_encendido_s": round(time.time() - info["boot_time"]),
        "discos": [{"unidad": d["mountpoint"], "total": d["total"], "usado": d["used"], "libre": d["free"], "porcentaje": d["percent"]} for d in info["disks"]],
        "actual": _sample(s),
        "medido_en": s.ts if s else None,
        "hora_servidor": time.time(),
        "solo_lectura": True,
    }


def history(engine, seconds: int) -> dict:
    return {"muestras": [_sample(s) for s in engine.sampler.history(seconds)], "hora_servidor": time.time()}


def processes(engine, by: str, limit: int) -> dict:
    """Procesos agrupados por nombre (sin PID, ruta, usuario ni línea de comandos)."""
    data = tools.procesos_top(engine, by, limit)
    ts, _ = engine.processes.latest()
    return {
        "criterio": data["criterio"],
        "medido_en": ts or None,
        "programas": [{k: p[k] for k in ("nombre", "instancias", "ram_mb", "cpu_ahora_pct", "cpu_prom_1min_pct", "tipo")} for p in data["programas"]],
    }


def findings(engine, share_security: bool) -> dict:
    r = tools.resumen_rendimiento(engine)
    out: dict = {"rendimiento": r["hallazgos"], "medido_en": time.time(), "seguridad": None}
    if share_security:
        # No se ejecuta la auditoría desde un dispositivo remoto: solo se comparte el último resultado.
        sec = tools.seguridad(engine, ejecutar=False)
        if sec.get("disponible"):
            out["seguridad"] = {
                "medido": sec["medido"],
                "antivirus_activo": sec["antivirus_activo"],
                "proteccion_tiempo_real": sec["proteccion_tiempo_real"],
                "firewall": sec["firewall"],
                "amenazas_activas_defender": sec["amenazas_activas_defender"],
                # Sin la columna «dónde»: puede contener rutas personales.
                "hallazgos": [{"estado": h["estado"], "que": h["que"]} for h in sec["hallazgos"]],
            }
    return out
