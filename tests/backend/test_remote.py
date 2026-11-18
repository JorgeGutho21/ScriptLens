"""Acceso remoto: vinculación, solo lectura, origen de red, revocación y TLS real."""

from __future__ import annotations

import http.client
import socket
import ssl
import time

import pytest
from fastapi.testclient import TestClient

from backend.core.api import Engine, create_app
from backend.core.config import Settings
from backend.remote import tls
from backend.remote.app import ALLOWED_ROUTES, COOKIE, create_remote_app
from backend.remote.auth import MAX_FAILS_PER_IP, PairingError, RemoteAuth
from backend.remote.netinfo import is_allowed_client
from backend.storage.db import Database

LAN = ("192.168.1.50", 50123)


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    settings = Settings(token="token-local", sample_interval=0.2, process_interval=0.4, data_dir=tmp_path_factory.mktemp("remote"))
    e = Engine(settings)
    e.start()
    time.sleep(1.2)
    yield e
    e.stop()


@pytest.fixture()
def svc(engine):
    s = engine.remote
    s.state = "activo"  # el servidor real se prueba aparte; aquí basta el estado lógico
    s.fingerprint = "AA:BB"
    s.auth.new_code()
    yield s
    s.disable()


def lan_client(svc, addr=LAN) -> TestClient:
    return TestClient(create_remote_app(svc), base_url="https://testserver", client=addr)


def pair(svc, c: TestClient, tipo="navegador") -> dict:
    code = svc.auth.code_info()["codigo"] or svc.auth.new_code()["codigo"]
    r = c.post("/remote/api/pair/request", json={"codigo": code, "nombre": "Celular de prueba", "tipo": tipo})
    assert r.status_code == 200, r.text
    body = r.json()
    short = body["solicitud"][:8]
    svc.auth.decide(short, True)
    st = c.get("/remote/api/pair/status", params={"solicitud": body["solicitud"]})
    assert st.json()["estado"] == "autorizada"
    return st.json()


def iter_routes(routes):
    """Rutas finales, incluidas las de routers anidados (FastAPI los envuelve en _IncludedRouter)."""
    for r in routes:
        inner = getattr(r, "original_router", None)
        if inner is not None:
            yield from iter_routes(inner.routes)
        else:
            yield r


# --- Unidades ----------------------------------------------------------------
def test_private_network_filter():
    for ok in ("192.168.0.10", "10.1.2.3", "172.20.10.2", "169.254.3.4", "::ffff:192.168.1.9"):
        assert is_allowed_client(ok)
    for bad in ("8.8.8.8", "100.64.0.1", "127.0.0.1", "testclient", "", None, "224.0.0.1"):
        assert not is_allowed_client(bad)
    assert is_allowed_client("127.0.0.1", allow_loopback=True)


def test_code_rate_limit_and_single_delivery(tmp_path):
    db = Database(tmp_path / "a.db")
    now = [1000.0]
    a = RemoteAuth(db, clock=lambda: now[0])
    code = a.new_code()["codigo"]
    for _ in range(MAX_FAILS_PER_IP):
        with pytest.raises(PairingError) as e:
            a.request("000000" if code != "000000" else "111111", "x", "navegador", "192.168.1.2")
        assert e.value.status == 401
    with pytest.raises(PairingError) as e:  # bloqueado aunque ahora el código sea correcto
        a.request(code, "x", "navegador", "192.168.1.2")
    assert e.value.status == 429
    req = a.request(code, "Laptop", "consola", "192.168.1.3")  # otra IP sigue pudiendo
    assert a.poll(req.id)[0] == "pendiente"
    a.decide(req.id[:8], True)
    estado, token, tipo = a.poll(req.id)
    assert estado == "autorizada" and token and tipo == "consola"
    assert a.poll(req.id) == ("entregada", None, None)  # la credencial no se entrega dos veces
    assert a.validate(token, "192.168.1.3") is not None
    assert a.code_info()["codigo"] is None  # el código no sirve para otra vinculación
    now[0] += 31 * 86400
    assert a.validate(token, "192.168.1.3") is None  # caducada


def test_code_expires(tmp_path):
    now = [0.0]
    a = RemoteAuth(Database(tmp_path / "b.db"), clock=lambda: now[0])
    code = a.new_code()["codigo"]
    now[0] += 301
    with pytest.raises(PairingError):
        a.request(code, "x", "navegador", "10.0.0.2")


def test_tokens_stored_only_as_hash(svc):
    c = lan_client(svc)
    pair(svc, c)
    token = c.cookies.get(COOKIE)
    rows = svc.db.query("SELECT * FROM remote_sessions")
    assert rows and all(token not in str(v) for r in rows for v in r.values())


# --- Aplicación remota ----------------------------------------------------------
def test_rejects_public_ip_even_with_session(svc):
    c = lan_client(svc)
    pair(svc, c)
    public = lan_client(svc, ("8.8.8.8", 4000))
    public.cookies.set(COOKIE, c.cookies.get(COOKIE))
    assert public.get("/remote/api/overview").status_code == 403


def test_unauthenticated_requests_are_rejected(svc):
    c = lan_client(svc)
    for path in ("/remote/api/whoami", "/remote/api/overview", "/remote/api/history", "/remote/api/processes", "/remote/api/findings"):
        assert c.get(path).status_code == 401, path
    assert c.get("/remote/api/overview", headers={"X-ScriptLens-Token": "token-local"}).status_code == 401  # el token de Tauri no sirve
    assert c.get("/remote/api/overview", headers={"Authorization": "Bearer inventado"}).status_code == 401


def test_browser_pairing_and_live_data(svc, engine):
    c = lan_client(svc)
    assert c.get("/").status_code == 200
    assert "solo lectura" in c.get("/").text
    pair(svc, c)
    o = c.get("/remote/api/overview").json()
    assert o["solo_lectura"] is True and o["device_id"] == svc.device_id
    assert o["actual"]["cpu_percent"] is not None and abs(o["medido_en"] - time.time()) < 5
    p = c.get("/remote/api/processes", params={"by": "memory"}).json()
    assert p["programas"] and set(p["programas"][0]) == {"nombre", "instancias", "ram_mb", "cpu_ahora_pct", "cpu_prom_1min_pct", "tipo"}
    h = c.get("/remote/api/history", params={"seconds": 60}).json()["muestras"]
    assert len(h) >= 2
    r = c.get("/remote/api/overview")
    assert "default-src 'self'" in r.headers["content-security-policy"] and r.headers["cache-control"] == "no-store"


def test_sharing_preferences_are_enforced(svc):
    c = lan_client(svc)
    pair(svc, c)
    svc.set_sharing(False, True, True)
    assert c.get("/remote/api/processes").status_code == 403
    svc.set_sharing(True, True, True)
    assert c.get("/remote/api/processes").status_code == 200


def test_no_write_or_local_route_reachable_remotely(svc, engine):
    """Con una sesión válida, ninguna ruta de la API local (acciones, ajustes, asistente…) existe en remoto."""
    c = lan_client(svc)
    pair(svc, c)
    local = create_app(engine.settings, engine)
    checked = 0
    for route in iter_routes(local.routes):
        for method in getattr(route, "methods", None) or []:
            if method in ("HEAD", "OPTIONS"):
                continue
            path = route.path.replace("{", "").replace("}", "")
            assert (method, path) not in ALLOWED_ROUTES
            r = c.request(method, path, json={})
            assert r.status_code in (404, 405), (method, path, r.status_code)
            checked += 1
    assert checked > 40
    for method in ("PUT", "PATCH", "DELETE"):
        assert c.request(method, "/remote/api/overview").status_code == 405
    # La aplicación remota no registra nada fuera de la lista permitida.
    remote = create_remote_app(svc)
    for route in iter_routes(remote.routes):
        for method in getattr(route, "methods", None) or []:
            if method != "HEAD":
                assert (method, route.path) in ALLOWED_ROUTES


def test_revocation_and_disable_cut_existing_sessions(svc):
    a, b = lan_client(svc), lan_client(svc, ("192.168.1.51", 5000))
    pair(svc, a)
    pair(svc, b)
    assert a.get("/remote/api/overview").status_code == 200
    sid = next(s["id"] for s in svc.auth.sessions() if s["ip"] == "192.168.1.50")
    svc.auth.revoke(sid)
    assert a.get("/remote/api/overview").status_code == 401
    assert b.get("/remote/api/overview").status_code == 200
    svc.pause()  # en pausa no se sirven datos aunque la sesión exista
    assert b.get("/remote/api/overview").status_code == 401
    svc.state = "activo"
    assert b.get("/remote/api/overview").status_code == 200
    st = svc.disable()
    assert st["estado"] == "apagado" and st["sesiones"] == []
    svc.state = "activo"
    assert b.get("/remote/api/overview").status_code == 401


def test_rejected_request_gets_no_session(svc):
    c = lan_client(svc)
    body = c.post("/remote/api/pair/request", json={"codigo": svc.auth.code_info()["codigo"], "nombre": "Intruso"}).json()
    svc.auth.decide(body["solicitud"][:8], False)
    assert c.get("/remote/api/pair/status", params={"solicitud": body["solicitud"]}).json()["estado"] == "rechazada"
    assert c.get("/remote/api/overview").status_code == 401


# --- Servidor real con TLS -------------------------------------------------------
def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_real_https_server_lifecycle(engine):
    svc = engine.remote
    svc.allow_loopback = True
    port = _free_port()
    st = svc.enable(port=port, addresses=["127.0.0.1"])
    try:
        assert st["estado"] == "activo" and st["urls"] == [f"https://127.0.0.1:{port}/"]
        assert st["codigo"]["codigo"] and len(st["codigo"]["codigo"]) == 6
        ctx = ssl.create_default_context()
        ctx.check_hostname, ctx.verify_mode = False, ssl.CERT_NONE
        conn = http.client.HTTPSConnection("127.0.0.1", port, context=ctx, timeout=5)
        conn.request("GET", "/remote/api/overview")
        resp = conn.getresponse()
        assert resp.status == 401
        der = conn.sock.getpeercert(binary_form=True)
        assert tls.fingerprint_der(der) == svc.fingerprint  # la huella mostrada coincide con la servida
        conn.close()
        plain = http.client.HTTPConnection("127.0.0.1", port, timeout=5)  # sin cifrar: no se atiende
        with pytest.raises((http.client.HTTPException, ConnectionError, OSError)):
            plain.request("GET", "/remote/api/overview")
            plain.getresponse().read()
    finally:
        st = svc.disable()
        svc.allow_loopback = False
    assert st["estado"] == "apagado"
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", port), timeout=1).close()


def test_local_control_api(engine):
    app = create_app(engine.settings, engine)
    with TestClient(app) as c:
        c.headers["X-ScriptLens-Token"] = "token-local"
        st = c.get("/api/remote/status").json()
        assert st["estado"] == "apagado" and st["urls"] == []  # arranca apagado
        assert c.post("/api/remote/code").status_code == 409
        assert c.get("/api/remote/status", headers={"X-ScriptLens-Token": "x"}).status_code == 401
