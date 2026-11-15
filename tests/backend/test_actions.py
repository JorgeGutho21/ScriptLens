"""Pruebas de las acciones supervisadas (fase 6)."""

import os
import subprocess
import sys
import time
import winreg

import psutil
import pytest
from fastapi.testclient import TestClient

from backend.actions import operations
from backend.core.api import Engine, create_app
from backend.core.config import Settings

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Solo Windows")


@pytest.fixture(scope="module")
def ctx(tmp_path_factory):
    settings = Settings(token="t", sample_interval=0.2, process_interval=0.4, data_dir=tmp_path_factory.mktemp("acc"))
    engine = Engine(settings)
    app = create_app(settings, engine)
    engine.start()
    time.sleep(1.2)
    with TestClient(app) as c:
        c.headers["X-ScriptLens-Token"] = "t"
        yield c, engine
    engine.stop()


def spawn():
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    p = psutil.Process(child.pid)
    return child, {"pid": child.pid, "create_time": p.create_time(), "nombre": p.name()}


def test_terminate_requires_token_and_is_audited(ctx):
    c, engine = ctx
    child, ident = spawn()
    try:
        prep = c.post("/api/actions/process/prepare", json={"accion": "finalizar", **ident}).json()
        assert prep["token"] and prep["advertencias"]
        assert psutil.pid_exists(child.pid)  # preparar no ejecuta nada
        res = c.post("/api/actions/execute", json={"token": prep["token"]}).json()
        assert res["resultado"] == "completada"
        assert child.wait(timeout=5) is not None
        # El token es de un solo uso
        assert c.post("/api/actions/execute", json={"token": prep["token"]}).status_code == 409
        log = c.get("/api/actions/log").json()["actions"]
        assert log[0]["action"] == "finalizar" and log[0]["result"] == "completada" and log[0]["before"]
    finally:
        if child.poll() is None:
            child.kill()


def test_identity_is_revalidated_before_acting(ctx):
    c, _ = ctx
    child, ident = spawn()
    try:
        bad = {**ident, "create_time": ident["create_time"] - 100}
        r = c.post("/api/actions/process/prepare", json={"accion": "finalizar", **bad})
        assert r.status_code == 409 and "identidad" in r.json()["detail"]
        prep = c.post("/api/actions/process/prepare", json={"accion": "finalizar", **ident}).json()
        child.kill()
        child.wait(timeout=5)
        r = c.post("/api/actions/execute", json={"token": prep["token"]})
        assert r.status_code == 409  # el proceso desapareció entre preparar y ejecutar
    finally:
        if child.poll() is None:
            child.kill()


def test_protected_and_own_processes_are_refused(ctx):
    c, _ = ctx
    for proc in psutil.process_iter(["name", "create_time"]):
        if (proc.info["name"] or "").lower() in ("csrss.exe", "explorer.exe", "msmpeng.exe"):
            r = c.post("/api/actions/process/prepare", json={"accion": "finalizar", "pid": proc.pid, "create_time": proc.info["create_time"] or 0, "nombre": proc.info["name"]})
            assert r.status_code == 409
    me = psutil.Process()
    r = c.post("/api/actions/process/prepare", json={"accion": "finalizar", "pid": me.pid, "create_time": me.create_time(), "nombre": me.name()})
    assert r.status_code == 409


def test_close_request_needs_a_window(ctx):
    c, _ = ctx
    child, ident = spawn()
    try:
        r = c.post("/api/actions/process/prepare", json={"accion": "cerrar", **ident})
        assert r.status_code == 409 and "ventana" in r.json()["detail"]
    finally:
        child.kill()


def test_expired_token(ctx, monkeypatch):
    c, _ = ctx
    child, ident = spawn()
    try:
        prep = c.post("/api/actions/process/prepare", json={"accion": "finalizar", **ident}).json()
        monkeypatch.setattr(operations, "TOKEN_TTL", 0.0)
        assert c.post("/api/actions/execute", json={"token": prep["token"]}).status_code == 409
        assert child.poll() is None
    finally:
        child.kill()


def test_startup_toggle_is_reversible(ctx, monkeypatch):
    """Usa una clave de pruebas aislada; no toca las entradas reales de inicio."""
    c, _ = ctx
    test_key = r"Software\ScriptLensPruebas\StartupApproved\Run"
    monkeypatch.setitem(operations._APPROVED, "HKCU", (winreg.HKEY_CURRENT_USER, test_key))
    entry = {"id": "HKCU:Demo", "nombre": "Demo", "comando": "C:\\demo.exe", "habilitado": True, "modificable_sin_admin": True, "scope": "HKCU"}
    state = {"on": True}
    monkeypatch.setattr(operations, "startup_entries", lambda: [{**entry, "habilitado": state["on"]}])
    try:
        prep = c.post("/api/actions/startup/prepare", json={"id": "HKCU:Demo", "habilitar": False}).json()
        assert "puede revertirlo" in prep["resumen"]
        assert c.post("/api/actions/execute", json={"token": prep["token"]}).json()["resultado"] == "completada"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, test_key) as k:
            assert winreg.QueryValueEx(k, "Demo")[0][0] == 3
        state["on"] = False
        prep = c.post("/api/actions/startup/prepare", json={"id": "HKCU:Demo", "habilitar": True}).json()
        c.post("/api/actions/execute", json={"token": prep["token"]})
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, test_key) as k:
            assert winreg.QueryValueEx(k, "Demo")[0][0] == 2
        hklm = {**entry, "id": "HKLM:X", "modificable_sin_admin": False, "scope": "HKLM"}
        monkeypatch.setattr(operations, "startup_entries", lambda: [hklm])
        assert c.post("/api/actions/startup/prepare", json={"id": "HKLM:X", "habilitar": False}).status_code == 409
    finally:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\ScriptLensPruebas\StartupApproved\Run")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\ScriptLensPruebas\StartupApproved")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\ScriptLensPruebas")


def test_temp_cleanup_only_old_files_inside_temp(ctx, tmp_path, monkeypatch):
    c, _ = ctx
    temp = tmp_path / "temp"
    (temp / "sub").mkdir(parents=True)
    old = temp / "viejo.tmp"
    old2 = temp / "sub" / "viejo2.log"
    new = temp / "nuevo.tmp"
    outside = tmp_path / "documento_personal.docx"
    for f in (old, old2, new, outside):
        f.write_bytes(b"x" * 100)
    past = time.time() - 30 * 86400
    for f in (old, old2, outside):
        os.utime(f, (past, past))
    monkeypatch.setenv("TEMP", str(temp))
    preview = c.get("/api/actions/temp/preview").json()["categorias"][0]
    assert preview["archivos"] == 2 and preview["bytes"] == 200
    assert old.exists()  # la vista previa no borra
    prep = c.post("/api/actions/temp/prepare").json()
    res = c.post("/api/actions/execute", json={"token": prep["token"]}).json()
    assert res["eliminados"] == 2
    assert not old.exists() and not old2.exists()
    assert new.exists() and outside.exists()


def test_installed_programs_are_listed_without_uninstall_strings(ctx):
    c, _ = ctx
    progs = c.get("/api/actions/programs").json()["programas"]
    assert progs and all("_uninstall" not in p for p in progs)


@pytest.mark.parametrize("bad_temp", [None, "", ".", "relative\\temp"])
def test_temp_cleanup_rejects_unsafe_environment(ctx, tmp_path, monkeypatch, bad_temp):
    """La vista previa y la ejecución nunca deben operar desde el CWD."""
    c, _ = ctx
    if bad_temp is None:
        monkeypatch.delenv("TEMP", raising=False)
    else:
        monkeypatch.setenv("TEMP", bad_temp)
    outside = tmp_path / "documento_importante.txt"
    outside.write_text("NO BORRAR", encoding="utf-8")
    previous = os.getcwd()
    try:
        os.chdir(tmp_path)
        assert c.get("/api/actions/temp/preview").status_code == 409
        assert c.post("/api/actions/temp/prepare").status_code == 409
        assert outside.read_text(encoding="utf-8") == "NO BORRAR"
    finally:
        os.chdir(previous)


def test_temp_cleanup_revalidates_path_on_execution(ctx, tmp_path, monkeypatch):
    """Si TEMP cambia tras preparar, la ejecución se cancela sin borrar nada."""
    c, _ = ctx
    temp = tmp_path / "temp"
    temp.mkdir()
    monkeypatch.setenv("TEMP", str(temp))
    prep = c.post("/api/actions/temp/prepare").json()
    assert prep["token"]
    monkeypatch.delenv("TEMP")
    outside = tmp_path / "documento_importante.txt"
    outside.write_text("NO BORRAR", encoding="utf-8")
    previous = os.getcwd()
    try:
        os.chdir(tmp_path)
        assert c.post("/api/actions/execute", json={"token": prep["token"]}).status_code == 409
        assert outside.read_text(encoding="utf-8") == "NO BORRAR"
    finally:
        os.chdir(previous)


@pytest.mark.parametrize("target", ["home", "home_parent", "documents", "windows", "drive_root"])
def test_temp_cleanup_rejects_personal_or_system_folders(ctx, monkeypatch, target):
    """TEMP nunca puede apuntar al perfil, a una carpeta que lo contiene, a Documentos o a Windows."""
    from pathlib import Path

    c, _ = ctx
    home = Path.home()
    paths = {
        "home": home,
        "home_parent": home.parent,
        "documents": home / "Documents",
        "windows": Path(os.environ.get("SystemRoot", r"C:\Windows")),
        "drive_root": Path(home.anchor),
    }
    if not paths[target].is_dir():
        pytest.skip("carpeta no disponible en este equipo")
    monkeypatch.setenv("TEMP", str(paths[target]))
    assert c.get("/api/actions/temp/preview").status_code == 409
    assert c.post("/api/actions/temp/prepare").status_code == 409


def test_temp_cleanup_does_not_follow_junctions(ctx, tmp_path, monkeypatch):
    """Una unión NTFS dentro de TEMP hacia otra carpeta no se recorre ni se vacía."""
    c, _ = ctx
    temp = tmp_path / "temp"
    temp.mkdir()
    outside = tmp_path / "externo"
    outside.mkdir()
    victim = outside / "documento_antiguo.txt"
    victim.write_text("NO BORRAR", encoding="utf-8")
    stale = temp / "residuo.tmp"
    stale.write_text("x", encoding="utf-8")
    old = time.time() - 30 * 86400
    os.utime(victim, (old, old))
    os.utime(stale, (old, old))
    link = temp / "union"
    subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], check=True, capture_output=True)
    assert link.is_junction()
    monkeypatch.setenv("TEMP", str(temp))

    preview = c.get("/api/actions/temp/preview").json()["categorias"][0]
    assert preview["archivos"] == 1 and "documento_antiguo.txt" not in preview["muestra"]
    prep = c.post("/api/actions/temp/prepare").json()
    res = c.post("/api/actions/execute", json={"token": prep["token"]}).json()
    assert res["eliminados"] == 1
    assert not stale.exists()
    assert victim.read_text(encoding="utf-8") == "NO BORRAR"


def test_temp_cleanup_requires_confirmation_token(ctx):
    """Sin un token emitido por la vista de confirmación no se borra nada."""
    c, _ = ctx
    assert c.post("/api/actions/execute", json={"token": "token-inventado-0000"}).status_code in (400, 403, 404, 409, 410)
