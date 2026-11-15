"""Captura y comparación de diagnósticos.

Un diagnóstico resume el último minuto medido: promedios de CPU y RAM, discos,
hallazgos y el consumo de cada programa agrupado por nombre (los PID cambian
entre sesiones, los nombres permiten comparar).

La comparación describe QUÉ cambió; nunca afirma POR QUÉ. Si el usuario indica
una acción entre ambos diagnósticos, el texto dice que los cambios «coinciden
en el tiempo» con ella, no que ella los causó.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict

from backend.monitoring.diagnosis import MIN_WINDOW_SAMPLES, summarize
from backend.monitoring.sampler import average

TOP_PROCESSES = 60
RAM_DELTA_NOTABLE = 5.0  # puntos porcentuales
CPU_DELTA_NOTABLE = 10.0
PROC_MEM_NOTABLE = 100 * 1024**2  # 100 MB


def capture(engine, seconds: int = 60) -> dict:
    """Construye un diagnóstico con las mediciones reales de la ventana indicada."""
    window = engine.sampler.history(seconds)
    if not window:
        raise ValueError("Aún no hay mediciones")
    last = window[-1]
    info = engine.info()
    summary = summarize(window, engine.sampler.history(), info["disks"])

    _, snaps = engine.processes.latest()
    agg: dict[str, dict] = defaultdict(lambda: {"instances": 0, "cpu_avg": 0.0, "memory": 0})
    for s in snaps:
        if s.pid == 0 or not s.name:
            continue
        st = engine.processes.stats(s.pid, s.create_time, seconds)
        a = agg[s.name]
        a["instances"] += 1
        a["cpu_avg"] += (st["cpu_avg"] or 0.0) if st else (s.cpu_percent or 0.0)
        a["memory"] += (st["memory_avg"] or 0) if st else (s.memory_rss or 0)
    ranked = sorted(agg.items(), key=lambda kv: (kv[1]["memory"], kv[1]["cpu_avg"]), reverse=True)
    by_cpu = sorted(agg.items(), key=lambda kv: kv[1]["cpu_avg"], reverse=True)[:15]
    keep = dict(ranked[:TOP_PROCESSES])
    keep.update(dict(by_cpu))

    return {
        "created_at": time.time(),
        "window_seconds": len(window),
        "enough_data": len(window) >= MIN_WINDOW_SAMPLES,
        "cpu_avg": average(window, "cpu_percent"),
        "ram_avg": average(window, "mem_percent"),
        "ram_used": int(sum(s.mem_used for s in window) / len(window)),
        "ram_total": last.mem_total,
        "swap_avg": average(window, "swap_percent"),
        "process_count": last.process_count,
        "disks": info["disks"],
        "findings": summary["findings"],
        "processes": [{"name": n, "instances": v["instances"], "cpu_avg": round(v["cpu_avg"], 2), "memory": int(v["memory"])} for n, v in keep.items()],
    }


def save(db, diag: dict, label: str) -> int:
    cur = db.execute(
        "INSERT INTO diagnostics(created_at, label, window_seconds, cpu_avg, ram_avg, ram_used, ram_total, swap_avg, process_count, disks_json, findings_json)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            diag["created_at"],
            label,
            diag["window_seconds"],
            diag["cpu_avg"],
            diag["ram_avg"],
            diag["ram_used"],
            diag["ram_total"],
            diag["swap_avg"],
            diag["process_count"],
            json.dumps(diag["disks"]),
            json.dumps(diag["findings"]),
        ),
    )
    did = cur.lastrowid
    for p in diag["processes"]:
        db.execute(
            "INSERT INTO diagnostic_processes(diagnostic_id, name, instances, cpu_avg, memory) VALUES (?,?,?,?,?)",
            (did, p["name"], p["instances"], p["cpu_avg"], p["memory"]),
        )
    return did


def load(db, did: int) -> dict | None:
    rows = db.query("SELECT * FROM diagnostics WHERE id = ?", (did,))
    if not rows:
        return None
    d = rows[0]
    d["disks"] = json.loads(d.pop("disks_json"))
    d["findings"] = json.loads(d.pop("findings_json"))
    d["processes"] = db.query("SELECT name, instances, cpu_avg, memory FROM diagnostic_processes WHERE diagnostic_id = ? ORDER BY memory DESC", (did,))
    return d


def listing(db) -> list[dict]:
    return db.query("SELECT id, created_at, label, window_seconds, cpu_avg, ram_avg, ram_used, ram_total, process_count FROM diagnostics ORDER BY created_at DESC")


def delete(db, did: int) -> bool:
    return db.execute("DELETE FROM diagnostics WHERE id = ?", (did,)).rowcount > 0


def _delta(a, b):
    if a is None or b is None:
        return None
    return round(b - a, 2)


def compare(a: dict, b: dict) -> dict:
    """Diferencias de B respecto de A (B es el más reciente o el estado actual)."""
    metrics = {
        "cpu_avg": {"antes": a["cpu_avg"], "despues": b["cpu_avg"], "delta": _delta(a["cpu_avg"], b["cpu_avg"])},
        "ram_avg": {"antes": a["ram_avg"], "despues": b["ram_avg"], "delta": _delta(a["ram_avg"], b["ram_avg"])},
        "ram_used": {"antes": a["ram_used"], "despues": b["ram_used"], "delta": _delta(a["ram_used"], b["ram_used"])},
        "process_count": {"antes": a["process_count"], "despues": b["process_count"], "delta": _delta(a["process_count"], b["process_count"])},
    }
    pa = {p["name"]: p for p in a["processes"]}
    pb = {p["name"]: p for p in b["processes"]}
    procs = []
    for name in set(pa) | set(pb):
        x, y = pa.get(name), pb.get(name)
        procs.append(
            {
                "name": name,
                "estado": "nuevo" if x is None else ("ausente" if y is None else "presente"),
                "memory_antes": x["memory"] if x else None,
                "memory_despues": y["memory"] if y else None,
                "memory_delta": (y["memory"] if y else 0) - (x["memory"] if x else 0),
                "cpu_antes": x["cpu_avg"] if x else None,
                "cpu_despues": y["cpu_avg"] if y else None,
                "cpu_delta": round((y["cpu_avg"] if y else 0) - (x["cpu_avg"] if x else 0), 2),
                "instancias_antes": x["instances"] if x else 0,
                "instancias_despues": y["instances"] if y else 0,
            }
        )
    procs.sort(key=lambda p: abs(p["memory_delta"]), reverse=True)

    # Advertencia: los procesos fuera del top guardado no se comparan.
    return {
        "a": {k: a.get(k) for k in ("id", "label", "created_at", "window_seconds")},
        "b": {k: b.get(k) for k in ("id", "label", "created_at", "window_seconds")},
        "metrics": metrics,
        "processes": procs,
        "summary": explain(metrics, procs, a, b),
        "limitaciones": [
            "Se comparan los programas con más consumo en cada diagnóstico (hasta 60 por memoria y 15 por CPU); los de consumo muy bajo pueden no aparecer.",
            "Los promedios corresponden al minuto previo a cada diagnóstico; una actividad breve puede no reflejarse.",
            "Una diferencia en el tiempo no demuestra que una acción concreta la haya causado.",
        ],
    }


def _mb(v: int) -> str:
    return f"{abs(v) / 1024**2:,.0f} MB".replace(",", ".")


def explain(metrics: dict, procs: list[dict], a: dict, b: dict) -> list[str]:
    out: list[str] = []
    ram = metrics["ram_avg"]["delta"]
    cpu = metrics["cpu_avg"]["delta"]
    if ram is not None:
        if ram >= RAM_DELTA_NOTABLE:
            out.append(f"Sí, el equipo usa más memoria RAM que antes: el promedio pasó de {a['ram_avg']} % a {b['ram_avg']} % (+{ram} puntos).")
        elif ram <= -RAM_DELTA_NOTABLE:
            out.append(f"El equipo usa menos memoria RAM que antes: el promedio pasó de {a['ram_avg']} % a {b['ram_avg']} % ({ram} puntos).")
        else:
            out.append(f"El uso de memoria RAM es similar ({a['ram_avg']} % antes, {b['ram_avg']} % después).")
    if cpu is not None:
        if abs(cpu) >= CPU_DELTA_NOTABLE:
            word = "más" if cpu > 0 else "menos"
            out.append(f"El procesador trabajó {word}: promedio de {a['cpu_avg']} % a {b['cpu_avg']} %.")
        else:
            out.append(f"La carga del procesador es similar ({a['cpu_avg']} % y {b['cpu_avg']} %).")
    up = [p for p in procs if p["memory_delta"] >= PROC_MEM_NOTABLE][:3]
    down = [p for p in procs if p["memory_delta"] <= -PROC_MEM_NOTABLE][:3]
    if up:
        out.append("Programas con mayor aumento de memoria: " + ", ".join(f"{p['name']} (+{_mb(p['memory_delta'])}{', nuevo' if p['estado'] == 'nuevo' else ''})" for p in up) + ".")
    if down:
        out.append("Programas con mayor reducción de memoria: " + ", ".join(f"{p['name']} (−{_mb(p['memory_delta'])}{', ya no está' if p['estado'] == 'ausente' else ''})" for p in down) + ".")
    if not a.get("enough_data", True) or not b.get("enough_data", True) or (a.get("window_seconds") or 0) < MIN_WINDOW_SAMPLES or (b.get("window_seconds") or 0) < MIN_WINDOW_SAMPLES:
        out.append("Atención: uno de los diagnósticos tiene menos de 20 segundos de mediciones; la comparación es menos confiable.")
    out.append("Estas diferencias coinciden en el tiempo con lo ocurrido entre ambos diagnósticos, pero no prueban una causa concreta.")
    return out
