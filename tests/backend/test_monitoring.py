"""Pruebas del monitoreo real: unidades, rangos y robustez."""

import time

import psutil
import pytest

from backend.monitoring.diagnosis import MIN_WINDOW_SAMPLES, summarize
from backend.monitoring.sampler import Sample, SystemSampler, _rate, average, system_info


def test_sample_units_are_consistent():
    sampler = SystemSampler(history_seconds=10, interval=0.2)
    time.sleep(0.25)
    s = sampler.take()
    assert 0.0 <= s.cpu_percent <= 100.0
    assert len(s.cpu_per_core) == psutil.cpu_count(logical=True)
    assert all(0.0 <= c <= 100.0 for c in s.cpu_per_core)
    # used + available == total (definición de Windows/psutil)
    assert s.mem_used + s.mem_available == s.mem_total
    assert 0.0 <= s.mem_percent <= 100.0
    assert s.process_count > 0
    # La RAM total reportada coincide con la lectura directa de psutil
    assert s.mem_total == psutil.virtual_memory().total


def test_rates_are_non_negative_and_handle_counter_reset():
    assert _rate(2000, 1000, 2.0) == 500.0
    assert _rate(100, 1000, 1.0) == 0.0  # reinicio de contador
    assert _rate(100, 0, 0.0) == 0.0  # intervalo inválido


def test_history_window_is_bounded():
    sampler = SystemSampler(history_seconds=3, interval=1.0)
    for _ in range(10):
        sampler.take()
    assert len(sampler.history()) == 3


def test_system_info_reports_real_hardware():
    info = system_info()
    assert info["cpu_logical"] == psutil.cpu_count(logical=True)
    assert info["mem_total"] == psutil.virtual_memory().total
    assert info["boot_time"] < time.time()
    assert info["disks"], "debe existir al menos una unidad"
    for d in info["disks"]:
        assert d["used"] <= d["total"]
    # No se inventan temperaturas cuando no están disponibles
    if not info["temperature"]["available"]:
        assert info["temperature"]["reason"]


def _fake(cpu, ram, ts=0.0):
    return Sample(ts, cpu, [cpu], 100, int(ram), 100 - int(ram), ram, 0.0, 0.0, 0.0, 0.0, 0.0, 10)


def test_diagnosis_requires_enough_samples():
    out = summarize([_fake(99, 99)] * 3, [], [])
    codes = [f["code"] for f in out["findings"]]
    assert codes == ["datos_insuficientes"]


def test_diagnosis_detects_sustained_cpu_not_single_spike():
    spike = [_fake(5, 30)] * (MIN_WINDOW_SAMPLES - 1) + [_fake(100, 30)]
    codes = [f["code"] for f in summarize(spike, spike, [])["findings"]]
    assert "cpu_sostenida" not in codes
    assert "estado_normal" in codes

    sustained = [_fake(95, 30)] * MIN_WINDOW_SAMPLES
    codes = [f["code"] for f in summarize(sustained, sustained, [])["findings"]]
    assert "cpu_sostenida" in codes
    assert "estado_normal" not in codes


def test_diagnosis_flags_full_disk():
    window = [_fake(5, 30)] * MIN_WINDOW_SAMPLES
    out = summarize(window, window, [{"mountpoint": "C:\\", "percent": 95.0}])
    assert any(f["estado"] == "requiere_revision" for f in out["findings"])


@pytest.mark.parametrize("values,expected", [([10, 20, 30], 20.0), ([], None)])
def test_average(values, expected):
    samples = [_fake(v, 10) for v in values]
    assert average(samples, "cpu_percent") == expected
