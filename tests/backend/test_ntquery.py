"""Validación cruzada de la lectura nativa de procesos contra psutil."""

import os
import sys
import time

import psutil
import pytest

from backend.processes import ntquery
from backend.processes.collector import ProcessMonitor

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Solo Windows")


def test_snapshot_matches_psutil_for_own_process():
    procs = {p.pid: p for p in ntquery.snapshot()}
    me = procs[os.getpid()]
    ps = psutil.Process()
    assert me.name.lower() == ps.name().lower()
    assert me.ppid == ps.ppid()
    assert abs(me.create_time - ps.create_time()) < 1.0
    # El conjunto de trabajo cambia levemente entre lecturas: tolerancia 20 %
    rss = ps.memory_info().rss
    assert abs(me.working_set - rss) / rss < 0.2


def test_snapshot_covers_process_list():
    native = {p.pid for p in ntquery.snapshot()}
    listed = set(psutil.pids())
    # Ambas listas se toman en instantes distintos; deben coincidir casi por completo
    assert len(native & listed) / len(listed) > 0.95
    assert 0 in native and 4 in native  # Idle y System


def test_native_sampling_is_fast_and_cpu_is_bounded():
    mon = ProcessMonitor(window_seconds=60)
    t = time.perf_counter()
    mon.sample()
    first = time.perf_counter() - t
    assert first < 0.25, f"la lectura nativa tardó {first:.3f}s"
    end = time.time() + 0.5
    while time.time() < end:  # carga breve y controlada en este proceso
        sum(i * i for i in range(10000))
    snaps = mon.sample()
    cpus = [s.cpu_percent for s in snaps if s.cpu_percent is not None]
    assert cpus and all(0.0 <= c <= 100.0 for c in cpus)
    total = sum(cpus)
    assert total <= 100.0 * 1.05  # la suma no puede superar la capacidad del equipo
    mine = next(s for s in snaps if s.pid == os.getpid())
    assert mine.cpu_percent > 0
