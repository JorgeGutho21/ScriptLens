"""Estadísticas: agregación, tiempos separados, alertas, consentimiento, pausa, borrado y retención."""

from __future__ import annotations

import time

import pytest

from backend.core.api import Engine
from backend.core.config import Settings
from backend.monitoring.sampler import Sample
from backend.stats.service import StatsService


def S(ts, cpu=20.0, ram=50.0):
    return Sample(ts=ts, cpu_percent=cpu, cpu_per_core=[cpu], mem_total=8 << 30, mem_used=4 << 30, mem_available=4 << 30, mem_percent=ram, swap_percent=0, disk_read_bps=1000.0, disk_write_bps=500.0, net_sent_bps=2000.0, net_recv_bps=4000.0, process_count=100)


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("SCRIPTLENS_REPORTS_DIR", str(tmp_path / "informes"))
    e = Engine(Settings(token="t", data_dir=tmp_path))
    now = [time.mktime(time.strptime("2026-11-18 10:00:05", "%Y-%m-%d %H:%M:%S"))]
    state = {"idle": 5.0, "app": "chrome.exe"}
    st = StatsService(e, clock=lambda: now[0], idle=lambda: state["idle"], foreground=lambda: state["app"], session=lambda: True)
    e.stats = st
    return e, st, now, state


def minute(st, m, cpu=20.0, ram=50.0):
    return st.record_minute(m, [S(m + i, cpu, ram) for i in range(0, 60, 5)], session_open=True)


def test_minute_and_hour_aggregation(env):
    e, st, now, _ = env
    base = int(now[0] // 3600 * 3600)
    for i in range(3):
        minute(st, base + i * 60, cpu=10 + i * 10)
    rows = e.db.query("SELECT * FROM stats_minute ORDER BY ts")
    assert [r["cpu_avg"] for r in rows] == [10, 20, 30]
    h = e.db.query("SELECT * FROM stats_hour")[0]
    assert h["minutes"] == 3 and h["cpu_avg"] == pytest.approx(20) and h["cpu_max"] == 30
    s = st.summary("dia")
    assert s["serie"][0]["red_enviados"] == 2000 * 60 * 3  # bytes = tasa media × segundos registrados
    assert s["tiempos"]["registrado_s"] == 180


def test_active_time_and_session_are_distinct(env, monkeypatch):
    e, st, now, state = env
    # El reloj de la prueba es fijo; el arranque se fija relativo a él para no depender de cuándo arrancó la máquina.
    info = {**e.info(), "boot_time": now[0] - 3600}
    monkeypatch.setattr(e, "info", lambda: info)
    m = int(now[0] // 60 * 60)
    for _ in range(3):  # 30 s activos en este minuto
        st.tick()
        now[0] += 10
    state["idle"] = 600  # inactivo: no suma
    for _ in range(3):
        st.tick()
        now[0] += 10
    minute(st, m)
    t = st.summary("dia")["tiempos"]
    assert t["activo_s"] == 30 and t["sesion_s"] == 60 and t["inactivo_s"] == 30
    assert t["desde_ultimo_arranque_s"] == 3600 + 60  # lo informa Windows, independiente de los anteriores


def test_app_tracking_requires_consent_and_stores_only_names(env):
    e, st, now, state = env
    st.tick()
    st.flush_apps()
    assert e.db.query("SELECT * FROM app_usage") == []  # desactivado por defecto
    st.set_settings(True, 90, True)
    for _ in range(4):
        st.tick()
        now[0] += 10
    st.flush_apps()
    rows = e.db.query("SELECT app, seconds FROM app_usage")
    assert rows == [{"app": "chrome.exe", "seconds": 40.0}]
    assert st.delete("aplicaciones")["borrados"] == 1
    assert e.db.query("SELECT * FROM app_usage") == []


def test_pause_stops_recording(env):
    e, st, now, _ = env
    st.set_settings(False, 90, True)
    for _ in range(8):
        st.tick()
        now[0] += 10
    assert e.db.query("SELECT * FROM stats_minute") == [] and e.db.query("SELECT * FROM app_usage") == []


def test_sustained_alert_needs_consecutive_minutes(env):
    e, st, now, _ = env
    base = int(now[0] // 60 * 60)
    for i in range(4):
        minute(st, base + i * 60, cpu=95)
    minute(st, base + 5 * 60, cpu=95)  # hueco en el minuto 4: no hay 5 seguidos
    assert e.db.query("SELECT * FROM stats_alerts") == []
    for i in range(6, 11):
        minute(st, base + i * 60, cpu=95)
    alerts = e.db.query("SELECT * FROM stats_alerts")
    assert len(alerts) == 1 and alerts[0]["kind"] == "cpu_sostenida"
    minute(st, base + 11 * 60, cpu=95)
    assert len(e.db.query("SELECT * FROM stats_alerts")) == 1  # sin duplicados durante 30 min


def test_retention_and_full_delete(env):
    e, st, now, _ = env
    old = int(now[0] - 10 * 86400) // 60 * 60
    minute(st, old)
    minute(st, int(now[0] // 60 * 60))
    st.cleanup(now[0])
    assert len(e.db.query("SELECT * FROM stats_minute")) == 1  # detalle por minuto: 7 días
    assert len(e.db.query("SELECT * FROM stats_hour")) == 2  # horas: 90 días
    st.delete("todo")
    assert e.db.query("SELECT * FROM stats_hour") == []


def test_export_and_compare_days(env, tmp_path):
    from fastapi.testclient import TestClient

    from backend.core.api import create_app

    e, st, now, _ = env
    minute(st, int(now[0] // 60 * 60), cpu=40)
    days = st.compare_days(now[0])
    assert len(days) == 7 and days[0]["cpu_prom"] == 40 and days[1]["minutos_registrados"] == 0
    with TestClient(create_app(e.settings, e)) as c:
        c.headers["X-ScriptLens-Token"] = "t"
        for fmt in ("csv", "html"):
            r = c.post("/api/stats/export", json={"formato": fmt, "periodo": "dia"}).json()
            text = (tmp_path / "informes" / r["archivo"]).read_text(encoding="utf-8")
            assert ("cpu_prom_%" in text) if fmt == "csv" else ("Uso activo" in text and "Jorge Gutiérrez" in text)
        assert c.get("/api/stats/summary", params={"period": "semana"}).status_code == 200
        assert c.delete("/api/stats/data/otra").status_code == 400
