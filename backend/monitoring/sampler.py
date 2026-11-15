"""Muestreo periódico y real de métricas globales del sistema.

Cada muestra se toma con psutil en el equipo local. Las tasas de disco y red
se calculan como diferencia entre dos lecturas de contadores acumulados
dividida por el tiempo transcurrido real (bytes/segundo).
"""

from __future__ import annotations

import platform
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass

import psutil


@dataclass
class Sample:
    ts: float
    cpu_percent: float
    cpu_per_core: list[float]
    mem_total: int
    mem_used: int
    mem_available: int
    mem_percent: float
    swap_percent: float
    disk_read_bps: float | None
    disk_write_bps: float | None
    net_sent_bps: float | None
    net_recv_bps: float | None
    process_count: int

    def to_dict(self) -> dict:
        return asdict(self)


def _rate(curr: float, prev: float, dt: float) -> float:
    # Los contadores pueden reiniciarse (p. ej. al desconectar un adaptador).
    if dt <= 0 or curr < prev:
        return 0.0
    return round((curr - prev) / dt, 1)


class SystemSampler:
    """Toma una muestra por intervalo y conserva una ventana de historial."""

    def __init__(self, history_seconds: int = 600, interval: float = 1.0):
        self.interval = interval
        self._history: deque[Sample] = deque(maxlen=max(1, int(history_seconds / interval)))
        self._lock = threading.Lock()
        self._prev_disk = psutil.disk_io_counters()
        self._prev_net = psutil.net_io_counters()
        self._prev_ts = time.monotonic()
        psutil.cpu_percent(interval=None, percpu=True)  # cebado: la 1.ª lectura no es válida
        self.started_at = time.time()

    def take(self) -> Sample:
        now_mono = time.monotonic()
        dt = now_mono - self._prev_ts
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        cpu_total = round(sum(per_core) / len(per_core), 1) if per_core else 0.0
        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()

        disk = psutil.disk_io_counters()
        if disk is not None and self._prev_disk is not None:
            d_read = _rate(disk.read_bytes, self._prev_disk.read_bytes, dt)
            d_write = _rate(disk.write_bytes, self._prev_disk.write_bytes, dt)
        else:
            d_read = d_write = None
        net = psutil.net_io_counters()
        if net is not None and self._prev_net is not None:
            n_sent = _rate(net.bytes_sent, self._prev_net.bytes_sent, dt)
            n_recv = _rate(net.bytes_recv, self._prev_net.bytes_recv, dt)
        else:
            n_sent = n_recv = None
        self._prev_disk, self._prev_net, self._prev_ts = disk, net, now_mono

        sample = Sample(
            ts=time.time(),
            cpu_percent=cpu_total,
            cpu_per_core=[round(c, 1) for c in per_core],
            mem_total=vm.total,
            mem_used=vm.total - vm.available,
            mem_available=vm.available,
            mem_percent=round(vm.percent, 1),
            swap_percent=round(sw.percent, 1),
            disk_read_bps=d_read,
            disk_write_bps=d_write,
            net_sent_bps=n_sent,
            net_recv_bps=n_recv,
            process_count=len(psutil.pids()),
        )
        with self._lock:
            self._history.append(sample)
        return sample

    def latest(self) -> Sample | None:
        with self._lock:
            return self._history[-1] if self._history else None

    def history(self, seconds: int | None = None) -> list[Sample]:
        with self._lock:
            items = list(self._history)
        if seconds is None:
            return items
        cutoff = time.time() - seconds
        return [s for s in items if s.ts >= cutoff]


def average(samples: list[Sample], attr: str) -> float | None:
    values = [getattr(s, attr) for s in samples if getattr(s, attr) is not None]
    return round(sum(values) / len(values), 1) if values else None


def system_info() -> dict:
    """Información estática del equipo (no cambia durante la sesión)."""
    freq = None
    try:
        f = psutil.cpu_freq()
        freq = round(f.max or f.current, 0) if f else None
    except (NotImplementedError, OSError):
        freq = None
    disks = []
    for part in psutil.disk_partitions(all=False):
        if "cdrom" in part.opts or not part.fstype:
            continue
        try:
            u = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        disks.append(
            {
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total": u.total,
                "used": u.used,
                "free": u.free,
                "percent": u.percent,
            }
        )
    temps_available = hasattr(psutil, "sensors_temperatures")
    return {
        "os": f"{platform.system()} {platform.release()}",
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_physical": psutil.cpu_count(logical=False),
        "cpu_logical": psutil.cpu_count(logical=True),
        "cpu_max_mhz": freq,
        "mem_total": psutil.virtual_memory().total,
        "boot_time": psutil.boot_time(),
        "disks": disks,
        # psutil no expone temperaturas en Windows; no se inventan valores.
        "temperature": {
            "available": temps_available,
            "reason": None if temps_available else "Windows no expone sensores de temperatura mediante psutil.",
        },
    }
