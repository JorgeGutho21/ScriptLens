"""Pruebas del historial SQLite y de la comparación de diagnósticos (fase 3)."""

import time

import pytest
from fastapi.testclient import TestClient

from backend.core.api import Engine, create_app
from backend.core.config import Settings
from backend.storage import diagnostics as dg
from backend.storage.db import SCHEMA_VERSION, Database


def diag(ram, cpu, procs, window=60, t=0.0):
    return {
        "created_at": t,
        "window_seconds": window,
        "enough_data": window >= 20,
        "cpu_avg": cpu,
        "ram_avg": ram,
        "ram_used": int(ram * 1e8),
        "ram_total": int(1e10),
        "swap_avg": 0.0,
        "process_count": len(procs),
        "disks": [],
        "findings": [],
        "processes": [{"name": n, "instances": 1, "cpu_avg": c, "memory": m} for n, c, m in procs],
    }


def test_migrations_create_schema(tmp_path):
    db = Database(tmp_path / "x.db")
    assert db.query("PRAGMA user_version")[0]["user_version"] == SCHEMA_VERSION
    tables = {r["name"] for r in db.query("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"diagnostics", "diagnostic_processes", "actions", "conversations", "messages", "settings"} <= tables
    db.close()
    Database(tmp_path / "x.db").close()  # reabrir no vuelve a migrar


def test_save_load_delete_cascade(tmp_path):
    db = Database(tmp_path / "x.db")
    did = dg.save(db, diag(50, 10, [("chrome.exe", 5.0, 800 * 1024**2)]), "Antes")
    loaded = dg.load(db, did)
    assert loaded["label"] == "Antes" and loaded["processes"][0]["name"] == "chrome.exe"
    assert dg.delete(db, did)
    assert dg.load(db, did) is None
    assert db.query("SELECT COUNT(*) AS n FROM diagnostic_processes")[0]["n"] == 0


def test_compare_answers_more_ram_question():
    a = diag(45.0, 10.0, [("chrome.exe", 3.0, 900 * 1024**2), ("code.exe", 1.0, 300 * 1024**2)])
    b = diag(62.0, 12.0, [("chrome.exe", 4.0, 1500 * 1024**2), ("teams.exe", 2.0, 400 * 1024**2)])
    out = dg.compare(a, b)
    assert out["metrics"]["ram_avg"]["delta"] == 17.0
    assert out["summary"][0].startswith("Sí, el equipo usa más memoria RAM")
    names = {p["name"]: p for p in out["processes"]}
    assert names["teams.exe"]["estado"] == "nuevo"
    assert names["code.exe"]["estado"] == "ausente"
    assert names["chrome.exe"]["memory_delta"] == 600 * 1024**2
    # Nunca afirma causalidad
    assert any("no prueban una causa" in s for s in out["summary"])
    assert not any("debido a" in s or "causó" in s for s in out["summary"])


def test_compare_similar_ram():
    out = dg.compare(diag(50.0, 10.0, []), diag(51.0, 11.0, []))
    assert "similar" in out["summary"][0]


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    settings = Settings(token="t", sample_interval=0.1, process_interval=0.3, data_dir=tmp_path_factory.mktemp("hist"))
    engine = Engine(settings)
    app = create_app(settings, engine)
    engine.start()
    time.sleep(2.5)
    with TestClient(app) as c:
        c.headers["X-ScriptLens-Token"] = "t"
        yield c
    engine.stop()


def test_api_save_compare_and_privacy(client):
    r = client.post("/api/history/diagnostics", json={"label": "Antes de cerrar programas"})
    assert r.status_code == 200, r.text
    first = r.json()
    assert first["ram_total"] > 0 and first["processes"]
    cmp_now = client.get("/api/history/compare", params={"a": first["id"], "b": "actual"}).json()
    assert cmp_now["b"]["label"] == "Ahora"
    assert cmp_now["summary"] and cmp_now["limitaciones"]

    second = client.post("/api/history/diagnostics", json={"label": "Después"}).json()
    cmp2 = client.get("/api/history/compare", params={"a": second["id"], "b": str(first["id"])}).json()
    assert cmp2["a"]["id"] == first["id"]  # se ordena de más antiguo a más reciente

    assert len(client.get("/api/history/diagnostics").json()["diagnostics"]) == 2
    assert client.delete(f"/api/history/diagnostics/{first['id']}").status_code == 200

    client.post("/api/settings", json={"key": "history_enabled", "value": False})
    assert client.post("/api/history/diagnostics", json={}).status_code == 409
    client.post("/api/settings", json={"key": "history_enabled", "value": True})

    assert client.delete("/api/privacy/diagnostics").json()["deleted"] == 1
    assert client.delete("/api/privacy/usuarios").status_code == 400
    assert client.post("/api/settings", json={"key": "otra", "value": True}).status_code == 422
