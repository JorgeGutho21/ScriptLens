"""Invitaciones por correo: enlace de un solo uso, correo como llave, permisos por sesión y revocación."""

from __future__ import annotations

import email
import json
import time
from email import policy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.core.api import Engine, create_app
from backend.core.config import Settings
from backend.remote.app import COOKIE, create_remote_app
from backend.remote.auth import PairingError, RemoteAuth
from backend.remote.invites import GENERIC, MAX_FAILS_INVITE, Invites, effective_permissions, valid_email
from backend.remote.mailer import SmtpMailer, build_message, create_mailer
from backend.storage.db import Database

LAN = ("192.168.1.50", 50123)
OTHER = ("192.168.1.77", 50124)


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    settings = Settings(token="token-local", sample_interval=0.2, process_interval=0.4, data_dir=tmp_path_factory.mktemp("invites"))
    e = Engine(settings)
    e.start()
    time.sleep(1.0)
    yield e
    e.stop()


@pytest.fixture()
def svc(engine):
    s = engine.remote
    s.state, s.fingerprint, s.addresses, s.port = "activo", "AA:BB:CC", ["192.168.1.20"], 8765
    s.set_sharing(True, True, True)
    yield s
    s.disable()


def local(engine) -> TestClient:
    return TestClient(create_app(engine.settings, engine), headers={"X-ScriptLens-Token": "token-local"})


def remote(svc, addr=LAN) -> TestClient:
    return TestClient(create_remote_app(svc), base_url="https://testserver", client=addr)


def invite(engine, correo="ana@ejemplo.com", **kw) -> dict:
    body = {"correo": correo, "procesos": True, "seguridad": False, "estadisticas": False, **kw}
    r = local(engine).post("/api/remote/invites", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def token_of(result: dict) -> str:
    return result["enlace"].split("#invitacion=", 1)[1]


# --- Unidades --------------------------------------------------------------------
def test_email_validation():
    for ok in ("ana@ejemplo.com", "Ana.Perez+lab@unicesar.edu.co", "  x@y.co "):
        assert valid_email(ok)
    for bad in ("", "ana", "ana@", "@ejemplo.com", "ana@ejemplo", "a b@ejemplo.com", "ana@ejemplo.com>", "x" * 70 + "@a.co"):
        assert not valid_email(bad)


def test_effective_permissions_are_the_intersection():
    sharing = {"procesos": True, "seguridad": False, "estadisticas": True}
    assert effective_permissions(sharing, {"permisos": None}) == sharing  # vinculación por código: lo que comparta la PC
    own = json.dumps({"procesos": False, "seguridad": True, "estadisticas": True})
    assert effective_permissions(sharing, {"permisos": own}) == {"procesos": False, "seguridad": False, "estadisticas": True}


def test_token_stored_only_as_hash_and_single_use(tmp_path):
    db = Database(tmp_path / "i.db")
    inv = Invites(db, RemoteAuth(db))
    row, token = inv.create("Ana@Ejemplo.com", {"procesos": True}, 60, 2)
    raw = db.query("SELECT * FROM remote_invites")[0]
    assert token not in json.dumps(raw) and raw["correo"] == "ana@ejemplo.com"
    session_token, s = inv.accept(token, " ANA@ejemplo.com ", "192.168.1.5")  # mayúsculas y espacios no importan
    assert s["permisos"] == {"procesos": True, "seguridad": False, "estadisticas": False}
    assert db.query("SELECT correo, permisos FROM remote_sessions")[0]["correo"] == "ana@ejemplo.com"
    with pytest.raises(PairingError) as e:
        inv.accept(token, "ana@ejemplo.com", "192.168.1.6")
    assert e.value.status == 401 and e.value.message == GENERIC
    assert inv.get(row["id"])["estado"] == "usada"


def test_expired_and_wrong_email_block(tmp_path):
    now = [1000.0]
    db = Database(tmp_path / "i.db")
    auth = RemoteAuth(db, clock=lambda: now[0])
    inv = Invites(db, auth, clock=lambda: now[0])
    _, t1 = inv.create("ana@ejemplo.com", {}, 5, 1)
    now[0] += 5 * 60 + 1
    with pytest.raises(PairingError):
        inv.accept(t1, "ana@ejemplo.com", "192.168.1.5")
    row, t2 = inv.create("ana@ejemplo.com", {}, 60, 1)
    for i in range(MAX_FAILS_INVITE):
        with pytest.raises(PairingError) as e:
            inv.accept(t2, f"otra{i}@ejemplo.com", f"192.168.1.{10 + i}")
        assert e.value.message == GENERIC  # no revela si falló el correo o el enlace
    assert inv.get(row["id"])["estado"] == "bloqueada"
    with pytest.raises(PairingError):
        inv.accept(t2, "ana@ejemplo.com", "192.168.1.30")  # ni con el correo correcto
    assert db.query("SELECT COUNT(*) AS n FROM remote_sessions")[0]["n"] == 0


def test_ip_lockout_after_repeated_failures(tmp_path):
    db = Database(tmp_path / "i.db")
    inv = Invites(db, RemoteAuth(db))
    for _ in range(5):
        with pytest.raises(PairingError):
            inv.accept("x" * 43, "ana@ejemplo.com", "192.168.1.5")
    _, token = inv.create("ana@ejemplo.com", {}, 60, 1)
    with pytest.raises(PairingError) as e:
        inv.accept(token, "ana@ejemplo.com", "192.168.1.5")
    assert e.value.status == 429
    assert inv.accept(token, "ana@ejemplo.com", "192.168.1.6")[1]["correo"] == "ana@ejemplo.com"  # otra IP sí puede


def test_message_contents(tmp_path):
    msg = build_message(to="ana@ejemplo.com", sender="ScriptLens IA <no-responder@scriptlens.local>", equipo="PC-LAB", enlace="https://192.168.1.20:8765/#invitacion=abc",
                        huella="AA:BB", caduca=time.time() + 3600, horas=2, permisos={"procesos": True, "seguridad": False, "estadisticas": True})
    text = msg.get_body(("plain",)).get_content()
    assert "#invitacion=abc" in text and "UNA sola vez" in text and "SOLO LECTURA" in text and "AA:BB" in text
    assert "seguridad" not in text.split("Podrá ver:")[1].split("\n")[0]
    assert msg["To"] == "ana@ejemplo.com" and "PC-LAB" in msg["Subject"]


def test_smtp_mailer_needs_configuration_and_never_exposes_password(monkeypatch, tmp_path):
    with pytest.raises(ValueError):
        create_mailer(tmp_path, env={"SCRIPTLENS_MAIL_MODE": "smtp"})
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            sent["dest"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self, context):
            sent["tls"] = True

        def login(self, user, password):
            sent["login"] = (user, password)

        def send_message(self, m):
            sent["to"] = m["To"]

    monkeypatch.setattr("backend.remote.mailer.smtplib.SMTP", FakeSMTP)
    env = {"SCRIPTLENS_MAIL_MODE": "smtp", "SCRIPTLENS_SMTP_HOST": "smtp.ejemplo.com", "SCRIPTLENS_SMTP_USER": "u", "SCRIPTLENS_SMTP_PASSWORD": "secreta", "SCRIPTLENS_SMTP_FROM": "u@ejemplo.com"}
    m = create_mailer(tmp_path, env=env)
    assert isinstance(m, SmtpMailer) and "secreta" not in repr(vars(m).get("host")) and m.list() == []
    msg = build_message(to="ana@ejemplo.com", sender=m.sender, equipo="PC", enlace="https://x/#invitacion=t", huella="", caduca=time.time(), horas=1, permisos={})
    out = m.send(msg, "id")
    assert sent == {"dest": ("smtp.ejemplo.com", 587), "tls": True, "login": ("u", "secreta"), "to": "ana@ejemplo.com"}
    assert "secreta" not in json.dumps(out)


# --- Flujo completo por HTTP -----------------------------------------------------------
def test_invite_requires_active_remote_access(engine):
    engine.remote.state = "apagado"
    r = local(engine).post("/api/remote/invites", json={"correo": "ana@ejemplo.com"})
    assert r.status_code == 409


def test_full_flow_local_mailbox_and_scoped_session(engine, svc):
    res = invite(engine)
    assert res["envio"]["modo"] == "local" and res["enlace"].startswith("https://192.168.1.20:8765/#invitacion=")
    eml = Path(res["envio"]["archivo"])
    parsed = email.message_from_bytes(eml.read_bytes(), policy=policy.default)
    assert parsed["To"] == "ana@ejemplo.com" and token_of(res) in parsed.get_body(("plain",)).get_content()

    c = remote(svc)
    assert c.get("/remote/api/overview").status_code == 401  # sin aceptar no hay datos
    bad = c.post("/remote/api/invite/accept", json={"token": token_of(res), "correo": "otro@ejemplo.com"})
    assert bad.status_code == 401
    ok = c.post("/remote/api/invite/accept", json={"token": token_of(res), "correo": "ana@ejemplo.com"})
    assert ok.status_code == 200, ok.text
    cookie = ok.headers["set-cookie"]
    assert COOKIE in cookie and "HttpOnly" in cookie and "Secure" in cookie and "samesite=strict" in cookie.lower()
    assert token_of(res) not in cookie

    who = c.get("/remote/api/whoami").json()
    assert who["comparte"] == {"procesos": True, "seguridad": False, "estadisticas": False} and who["sesion"]["invitacion"]
    assert c.get("/remote/api/overview").status_code == 200
    assert c.get("/remote/api/processes").status_code == 200
    assert c.get("/remote/api/stats").status_code == 403  # no incluido en la invitación
    assert c.get("/remote/api/findings").json()["seguridad"] is None

    # Un segundo dispositivo con el mismo enlace no entra.
    again = remote(svc, OTHER).post("/remote/api/invite/accept", json={"token": token_of(res), "correo": "ana@ejemplo.com"})
    assert again.status_code == 401

    # Si la PC deja de compartir procesos, la invitación tampoco los ve (intersección).
    svc.set_sharing(False, True, True)
    assert c.get("/remote/api/processes").status_code == 403
    svc.set_sharing(True, True, True)

    st = local(engine).get("/api/remote/status").json()
    item = next(i for i in st["invitaciones"] if i["id"] == res["invitacion"]["id"])
    assert item["estado"] == "usada" and item["sesion_activa"]
    assert any(s["correo"] == "ana@ejemplo.com" for s in st["sesiones"])
    assert "token_hash" not in json.dumps(st)

    # Quitar el acceso desde la PC corta la sesión al instante.
    assert local(engine).delete(f"/api/remote/invites/{item['id']}").status_code == 200
    assert c.get("/remote/api/overview").status_code == 401


def test_revoked_pending_invite_and_disable(engine, svc):
    res = invite(engine, correo="luis@ejemplo.com")
    local(engine).delete(f"/api/remote/invites/{res['invitacion']['id']}")
    r = remote(svc).post("/remote/api/invite/accept", json={"token": token_of(res), "correo": "luis@ejemplo.com"})
    assert r.status_code == 401
    res2 = invite(engine, correo="eva@ejemplo.com")
    svc.disable()  # desactivar anula también las invitaciones pendientes
    svc.state, svc.addresses, svc.port = "activo", ["192.168.1.20"], 8765
    r = remote(svc, OTHER).post("/remote/api/invite/accept", json={"token": token_of(res2), "correo": "eva@ejemplo.com"})
    assert r.status_code == 401


def test_accept_route_is_the_only_new_remote_route_and_rejects_bad_input(svc):
    c = remote(svc)
    assert c.post("/remote/api/invite/accept", json={"token": "corto", "correo": "a@b.co"}).status_code == 422
    assert c.get("/remote/api/invite/accept").status_code == 405
    assert c.post("/remote/api/invites", json={"correo": "a@b.co"}).status_code == 404  # crear invitaciones solo desde la PC
    svc.state = "pausado"
    assert c.post("/remote/api/invite/accept", json={"token": "x" * 43, "correo": "a@b.co"}).status_code == 503


def test_upgrade_from_v2_database_keeps_sessions(tmp_path):
    """Una instalación v0.2.0 (esquema 2) se actualiza sin perder los dispositivos vinculados."""
    import sqlite3

    from backend.storage import db as dbmod

    path = tmp_path / "v2.db"
    con = sqlite3.connect(path)
    for v in (1, 2):
        con.executescript(dbmod._MIGRATIONS[v])
    con.execute("PRAGMA user_version = 2")
    con.execute("INSERT INTO remote_sessions(id, token_hash, nombre, tipo, ip, created_at, expires_at) VALUES ('s1','h','Celular','navegador','192.168.1.5',1,9e12)")
    con.commit()
    con.close()
    db = Database(path)
    assert db.query("PRAGMA user_version")[0]["user_version"] == 3
    row = db.query("SELECT * FROM remote_sessions")[0]
    assert row["nombre"] == "Celular" and row["permisos"] is None and row["correo"] is None
    assert db.query("SELECT COUNT(*) AS n FROM remote_invites")[0]["n"] == 0
