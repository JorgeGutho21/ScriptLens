"""Recolector de procesos con tolerancia a fallos.

Principios:
- Un proceso puede terminar entre que se lista y se lee (NoSuchProcess): se omite.
- Algunos procesos del sistema niegan acceso (AccessDenied): se reporta el dato
  como ``None`` y se marca ``acceso_limitado`` en lugar de inventarlo.
- El CPU por proceso que entrega psutil puede superar 100 % (100 % por núcleo).
  Aquí se normaliza al total del equipo (0–100 %) para que coincida con la
  lectura global y con el Administrador de tareas.
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Iterable

import psutil

from . import ntquery

# Ruta portable (no Windows o respaldo). En Windows se usa ntquery.snapshot().
_ATTRS = ["pid", "name", "ppid", "create_time"]


def normalize_cpu(raw_percent: float | None, logical_cpus: int) -> float | None:
    """Convierte el porcentaje por núcleo de psutil a porcentaje del equipo."""
    if raw_percent is None:
        return None
    if logical_cpus <= 0:
        logical_cpus = 1
    value = raw_percent / logical_cpus
    return round(min(max(value, 0.0), 100.0), 2)


@dataclass
class ProcessSnapshot:
    pid: int
    name: str
    ppid: int | None
    status: str | None
    create_time: float | None
    threads: int | None
    cpu_percent: float | None
    memory_rss: int | None
    acceso_limitado: bool = False
    session_id: int | None = None
    private_bytes: int | None = None
    handles: int | None = None

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "name": self.name,
            "ppid": self.ppid,
            "status": self.status,
            "create_time": self.create_time,
            "threads": self.threads,
            "cpu_percent": self.cpu_percent,
            "memory_rss": self.memory_rss,
            "acceso_limitado": self.acceso_limitado,
            "session_id": self.session_id,
            "private_bytes": self.private_bytes,
            "handles": self.handles,
        }


def read_process(proc: psutil.Process, logical_cpus: int) -> ProcessSnapshot | None:
    """Lee un proceso. Devuelve None si el proceso dejó de existir."""
    limited = False
    try:
        with proc.oneshot():
            info = proc.as_dict(attrs=_ATTRS, ad_value=None)
            try:
                cpu_raw = proc.cpu_percent(interval=None)
            except psutil.AccessDenied:
                cpu_raw, limited = None, True
            try:
                rss = proc.memory_info().rss
            except psutil.AccessDenied:
                rss, limited = None, True
    except (psutil.NoSuchProcess, psutil.ZombieProcess):
        return None
    except psutil.AccessDenied:
        # Ni siquiera oneshot fue posible: se conserva lo mínimo conocido.
        return ProcessSnapshot(proc.pid, "", None, None, None, None, None, None, True)

    if any(info.get(k) is None for k in ("name", "ppid", "create_time")):
        limited = True
    return ProcessSnapshot(
        pid=info["pid"],
        name=info.get("name") or "",
        ppid=info.get("ppid"),
        status=info.get("status"),
        create_time=info.get("create_time"),
        threads=info.get("num_threads"),
        cpu_percent=normalize_cpu(cpu_raw, logical_cpus),
        memory_rss=rss,
        acceso_limitado=limited,
    )


@dataclass
class _Series:
    """Historial breve de un proceso para detectar consumo sostenido."""

    name: str
    points: deque = field(default_factory=lambda: deque(maxlen=300))


class ProcessMonitor:
    """Mide periódicamente los procesos y mantiene un historial corto por PID."""

    def __init__(self, window_seconds: int = 600, logical_cpus: int | None = None):
        self.logical_cpus = logical_cpus or psutil.cpu_count(logical=True) or 1
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._latest: list[ProcessSnapshot] = []
        self._latest_ts: float = 0.0
        self._series: dict[tuple[int, float | None], _Series] = {}
        self._self_pid = os.getpid()
        self._prev_cpu: dict[tuple[int, float | None], int] = {}
        self._prev_cpu_ts: float = 0.0

    def _sample_native(self) -> list[ProcessSnapshot]:
        """Ruta rápida en Windows: una llamada al sistema para todos los procesos."""
        now = time.monotonic()
        raw = ntquery.snapshot()
        prev, prev_ts = self._prev_cpu, self._prev_cpu_ts
        elapsed_100ns = (now - prev_ts) * 1e7 if prev_ts else 0.0
        current: dict[tuple[int, float | None], int] = {}
        snaps: list[ProcessSnapshot] = []
        for r in raw:
            key = (r.pid, r.create_time)
            current[key] = r.cpu_time_100ns
            cpu = None
            if elapsed_100ns > 0 and key in prev:
                delta = max(0, r.cpu_time_100ns - prev[key])
                cpu = normalize_cpu(delta / elapsed_100ns * 100.0, self.logical_cpus)
            snaps.append(
                ProcessSnapshot(
                    pid=r.pid,
                    name=r.name,
                    ppid=r.ppid,
                    status=None,  # Windows no expone un estado equivalente al de Unix
                    create_time=r.create_time,
                    threads=r.threads,
                    cpu_percent=cpu,
                    memory_rss=r.working_set,
                    acceso_limitado=False,
                    session_id=r.session_id,
                    private_bytes=r.private_bytes,
                    handles=r.handles,
                )
            )
        self._prev_cpu, self._prev_cpu_ts = current, now
        return snaps

    def sample(self, processes: Iterable[psutil.Process] | None = None) -> list[ProcessSnapshot]:
        now = time.time()
        snaps: list[ProcessSnapshot] = []
        if processes is None and ntquery.IS_WINDOWS:
            try:
                snaps = self._sample_native()
            except OSError:
                processes = psutil.process_iter()
        elif processes is None:
            processes = psutil.process_iter()
        if processes is not None:
            for proc in processes:
                snap = read_process(proc, self.logical_cpus)
                if snap is not None:
                    snaps.append(snap)
        with self._lock:
            self._latest = snaps
            self._latest_ts = now
            alive: set[tuple[int, float | None]] = set()
            for s in snaps:
                # La clave incluye create_time para no mezclar PIDs reutilizados.
                key = (s.pid, s.create_time)
                alive.add(key)
                series = self._series.get(key)
                if series is None:
                    series = self._series[key] = _Series(name=s.name)
                series.points.append((now, s.cpu_percent, s.memory_rss))
            for key in list(self._series):
                if key not in alive:
                    del self._series[key]
        return snaps

    def latest(self) -> tuple[float, list[ProcessSnapshot]]:
        with self._lock:
            return self._latest_ts, list(self._latest)

    def top(self, by: str = "cpu", limit: int = 10) -> list[dict]:
        _, snaps = self.latest()
        key = (lambda s: s.cpu_percent or 0.0) if by == "cpu" else (lambda s: s.memory_rss or 0)
        # El proceso "System Idle Process" (PID 0) representa tiempo libre, no consumo.
        ranked = sorted((s for s in snaps if s.pid != 0), key=key, reverse=True)
        return [s.to_dict() for s in ranked[:limit]]

    def sustained(self, seconds: int = 60, limit: int = 10) -> list[dict]:
        """Procesos con mayor CPU promedio en la ventana indicada (no solo picos)."""
        cutoff = time.time() - seconds
        results = []
        with self._lock:
            for (pid, ctime), series in self._series.items():
                if pid == 0:
                    continue
                pts = [p for p in series.points if p[0] >= cutoff]
                cpus = [p[1] for p in pts if p[1] is not None]
                mems = [p[2] for p in pts if p[2] is not None]
                if not cpus:
                    continue
                results.append(
                    {
                        "pid": pid,
                        "name": series.name,
                        "samples": len(cpus),
                        "cpu_avg": round(sum(cpus) / len(cpus), 2),
                        "cpu_max": round(max(cpus), 2),
                        "memory_avg": int(sum(mems) / len(mems)) if mems else None,
                    }
                )
        results.sort(key=lambda r: r["cpu_avg"], reverse=True)
        return results[:limit]

    def find(self, pid: int) -> ProcessSnapshot | None:
        _, snaps = self.latest()
        return next((s for s in snaps if s.pid == pid), None)

    def stats(self, pid: int, create_time: float | None, seconds: int = 60) -> dict | None:
        """Promedio y máximo de CPU/RAM de un proceso concreto en la ventana indicada."""
        cutoff = time.time() - seconds
        with self._lock:
            series = self._series.get((pid, create_time))
            pts = [p for p in series.points if p[0] >= cutoff] if series else []
        cpus = [p[1] for p in pts if p[1] is not None]
        mems = [p[2] for p in pts if p[2] is not None]
        if not cpus and not mems:
            return None
        return {
            "seconds": seconds,
            "samples": len(pts),
            "cpu_avg": round(sum(cpus) / len(cpus), 2) if cpus else None,
            "cpu_max": round(max(cpus), 2) if cpus else None,
            "memory_avg": int(sum(mems) / len(mems)) if mems else None,
            "memory_max": max(mems) if mems else None,
        }

    def self_usage(self) -> dict:
        """Consumo del propio backend de ScriptLens (transparencia de recursos)."""
        try:
            p = psutil.Process(self._self_pid)
            return {
                "pid": self._self_pid,
                "memory_rss": p.memory_info().rss,
                "cpu_percent": normalize_cpu(p.cpu_percent(interval=None), self.logical_cpus),
            }
        except psutil.Error:
            return {"pid": self._self_pid, "memory_rss": None, "cpu_percent": None}
