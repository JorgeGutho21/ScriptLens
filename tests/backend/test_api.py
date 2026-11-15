"""Pruebas de la API local: autenticación por token y contratos de respuesta."""

import time

import pytest
from fastapi.testclient import TestClient

from backend.core.api import Engine, create_app
from backend.core.config import Settings


@pytest.fixture(scope="module")
def client():
    settings = Settings(token="prueba-token", sample_interval=0.2, process_interval=0.4)
    engine = Engine(settings)
    app = create_app(settings, engine)
    engine.start()
    time.sleep(1.0)
    with TestClient(app) as c:
        c.headers["X-ScriptLens-Token"] = "prueba-token"
        yield c
    engine.stop()


def test_rejects_missing_or_wrong_token(client):
    for headers in ({"X-ScriptLens-Token": ""}, {"X-ScriptLens-Token": "otro"}):
        r = client.get("/api/health", headers=headers)
        assert r.status_code == 401


def test_health_identifies_project(client):
    data = client.get("/api/health").json()
    assert data["app"] == "ScriptLens IA"
    assert data["github"] == "@JorgeGutho21"


def test_current_and_history(client):
    cur = client.get("/api/metrics/current").json()
    assert cur["sample"] is not None
    assert cur["uptime_seconds"] > 0
    hist = client.get("/api/metrics/history", params={"seconds": 60}).json()["samples"]
    assert len(hist) >= 2
    assert [s["ts"] for s in hist] == sorted(s["ts"] for s in hist)


def test_history_parameter_is_validated(client):
    assert client.get("/api/metrics/history", params={"seconds": 99999}).status_code == 422


def test_processes_endpoints(client):
    r = client.get("/api/processes/top", params={"by": "memory", "limit": 3}).json()
    assert len(r["processes"]) == 3
    assert client.get("/api/processes/top", params={"by": "rm -rf"}).status_code == 422
    s = client.get("/api/processes/sustained").json()
    assert "processes" in s


def test_summary_contains_findings_and_self_usage(client):
    data = client.get("/api/metrics/summary").json()
    assert data["findings"]
    assert data["scriptlens"]["memory_rss"] > 0


def test_no_public_docs_exposed(client):
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
