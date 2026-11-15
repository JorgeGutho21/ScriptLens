"""Pruebas del administrador de procesos (fase 2)."""

import os
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.core.api import Engine, create_app
from backend.core.config import Settings
from backend.processes import analysis
from backend.processes.signatures import signer_name, verify_batch

WIN = sys.platform == "win32"


def snap(name, pid=1234, session=1, rss=100 * 1024**2, ctime=1.0):
    return SimpleNamespace(name=name, pid=pid, session_id=session, memory_rss=rss, create_time=ctime)


@pytest.fixture(scope="module")
def client():
    settings = Settings(token="t", sample_interval=0.2, process_interval=0.4)
    engine = Engine(settings)
    app = create_app(settings, engine)
    engine.start()
    time.sleep(1.5)
    with TestClient(app) as c:
        c.headers["X-ScriptLens-Token"] = "t"
        yield c
    engine.stop()


def test_signer_name_parsing():
    assert signer_name('CN=Microsoft Windows, O=Microsoft Corporation, L=Redmond, C=US') == "Microsoft Windows"
    assert signer_name('O="Empresa, S.A.", C=CO') == "Empresa, S.A."
    assert signer_name(None) is None


@pytest.mark.skipif(not WIN, reason="Solo Windows")
def test_catalog_signed_windows_binary_is_valid():
    """notepad.exe está firmado por catálogo: WinVerifyTrust directo fallaría, Authenticode no."""
    info = verify_batch([r"C:\Windows\System32\notepad.exe"])[0]
    assert info.estado == "valida"
    assert info.binario_windows is True
    assert "Microsoft" in (info.firmante or "")


@pytest.mark.skipif(not WIN, reason="Solo Windows")
def test_unsigned_file_reports_not_signed(tmp_path):
    f = tmp_path / "herramienta.ps1"
    f.write_text("Get-Date\n", encoding="utf-8")
    info = verify_batch([str(f)])[0]
    assert info.estado == "sin_firma"


@pytest.mark.skipif(not WIN, reason="Solo Windows")
def test_paths_with_quotes_are_data_not_code(tmp_path):
    """Una ruta con comillas y punto y coma no debe interpretarse como comando."""
    evil = tmp_path / "a'; Remove-Item x;'.txt"
    evil.write_text("x", encoding="utf-8")
    info = verify_batch([str(evil)])[0]
    assert info.path == str(evil)
    assert evil.exists()


def test_unsigned_alone_is_not_suspicious():
    sigs = analysis.signals(snap("herramienta.exe"), r"C:\Programas\herramienta.exe", {"estado": "sin_firma", "descripcion_estado": "x"}, None, 16 * 1024**3)
    assert analysis.overall(sigs) == analysis.NORMAL


def test_high_consumption_alone_is_not_suspicious():
    stats = {"cpu_avg": 90.0, "cpu_max": 100.0, "samples": 30, "seconds": 60}
    sigs = analysis.signals(snap("render.exe"), r"C:\Programas\render.exe", {"estado": "valida", "descripcion_estado": "ok"}, stats, 16 * 1024**3)
    assert analysis.overall(sigs) == analysis.CONSUMO


def test_masquerading_system_name_is_flagged():
    sigs = analysis.signals(snap("svchost.exe"), r"C:\Users\x\AppData\Local\Temp\svchost.exe", {"estado": "sin_firma", "descripcion_estado": "x"}, None, None)
    codes = {s["code"] for s in sigs}
    assert {"ubicacion_inesperada", "ubicacion_temporal", "posible_suplantacion"} <= codes
    assert analysis.overall(sigs) == analysis.SOSPECHOSA


def test_real_system_location_is_normal():
    sigs = analysis.signals(snap("svchost.exe", session=0), r"C:\Windows\System32\svchost.exe", {"estado": "valida", "descripcion_estado": "ok"}, None, None)
    assert analysis.overall(sigs) == analysis.NORMAL


def test_idle_and_kernel_processes_are_not_flagged():
    busy = {"cpu_avg": 95.0, "cpu_max": 100.0, "samples": 30, "seconds": 60}
    assert analysis.signals(snap("System Idle Process", pid=0), None, None, busy, None) == []
    assert analysis.overall(analysis.signals(snap("Secure System", pid=140), None, None, None, None)) == analysis.NORMAL


def test_critical_processes_cannot_be_terminated():
    for name in ("csrss.exe", "lsass.exe", "winlogon.exe", "MsMpEng.exe", "svchost.exe", "System"):
        ok, reason = analysis.can_terminate(name, 999, set())
        assert not ok and reason
    assert analysis.can_terminate("notepad.exe", 999, set())[0]
    assert not analysis.can_terminate("python.exe", 42, {42})[0]


def test_secrets_are_redacted_from_command_line():
    out = analysis.redact("app.exe --user ana --password=Secreto123 token: abc")
    assert "Secreto123" not in out and "abc" not in out


def test_process_list_has_categories(client):
    data = client.get("/api/processes").json()
    assert data["count"] > 50
    cats = {p["category"] for p in data["processes"]}
    assert "servicio" in cats and "sistema" in cats
    me = next(p for p in data["processes"] if p["pid"] == os.getpid())
    assert me["path"] and me["path"].lower().endswith("python.exe")


def test_detail_explains_in_plain_language(client):
    d = client.get(f"/api/processes/{os.getpid()}").json()
    preguntas = [q["pregunta"] for q in d["explicacion"]]
    assert "¿Qué hace este proceso?" in preguntas and "¿Puedo cerrarlo?" in preguntas
    assert all(q["tipo"] in ("comprobado", "estimado") for q in d["explicacion"])
    assert d["can_terminate"] is False  # es el propio motor


def test_detail_of_process_that_exited_returns_404(client):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    time.sleep(1.2)
    listed = {p["pid"] for p in client.get("/api/processes").json()["processes"]}
    assert child.pid in listed
    child.kill()
    child.wait(timeout=10)
    time.sleep(1.0)
    r = client.get(f"/api/processes/{child.pid}")
    assert r.status_code == 404


def test_detail_rejects_reused_pid(client):
    r = client.get(f"/api/processes/{os.getpid()}", params={"create_time": 1.0})
    assert r.status_code == 404
