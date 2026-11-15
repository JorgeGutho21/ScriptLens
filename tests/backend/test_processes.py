"""Pruebas del recolector de procesos: procesos que terminan y permisos."""

import subprocess
import sys
import time

import psutil

from backend.processes.collector import ProcessMonitor, normalize_cpu, read_process


def test_normalize_cpu_to_whole_machine():
    assert normalize_cpu(800.0, 8) == 100.0
    assert normalize_cpu(200.0, 8) == 25.0
    assert normalize_cpu(None, 8) is None
    assert normalize_cpu(50.0, 0) == 50.0


class _GoneProcess:
    pid = 999999

    def oneshot(self):
        raise psutil.NoSuchProcess(self.pid)


class _DeniedProcess:
    pid = 4

    def oneshot(self):
        raise psutil.AccessDenied(self.pid)


def test_process_that_exits_is_skipped():
    assert read_process(_GoneProcess(), 8) is None


def test_access_denied_is_reported_not_invented():
    snap = read_process(_DeniedProcess(), 8)
    assert snap is not None
    assert snap.acceso_limitado is True
    assert snap.cpu_percent is None and snap.memory_rss is None


def test_real_child_process_lifecycle():
    """Un proceso real que termina durante la medición no rompe el monitor."""
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        mon = ProcessMonitor(window_seconds=60)
        mon.sample()
        _, snaps = mon.latest()
        assert any(s.pid == child.pid for s in snaps)
        proc = psutil.Process(child.pid)
        child.kill()
        child.wait(timeout=10)
        # Medir un objeto de proceso ya terminado devuelve None sin excepción
        assert read_process(proc, 8) is None
        mon.sample()
        _, snaps = mon.latest()
        assert not any(s.pid == child.pid for s in snaps)
    finally:
        if child.poll() is None:
            child.kill()


def test_top_and_sustained_rankings():
    mon = ProcessMonitor(window_seconds=60)
    mon.sample()
    time.sleep(0.3)
    mon.sample()
    top = mon.top("memory", 5)
    assert 0 < len(top) <= 5
    rss = [p["memory_rss"] or 0 for p in top]
    assert rss == sorted(rss, reverse=True)
    assert all(p["pid"] != 0 for p in top)
    for p in mon.sustained(60, 5):
        assert 0.0 <= p["cpu_avg"] <= p["cpu_max"] <= 100.0
        assert p["samples"] >= 1
    usage = mon.self_usage()
    assert usage["memory_rss"] and usage["memory_rss"] > 0
