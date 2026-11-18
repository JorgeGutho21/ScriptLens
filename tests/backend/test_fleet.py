"""Consola de varias computadoras: dos agentes reales (TLS en 127.0.0.1) y una consola.

Simula el escenario C (dos PC Windows + consola) y D (revocación) en un solo equipo. Cada
agente tiene su propia carpeta de datos, por lo que su ``device_id`` y su certificado son
distintos, igual que en dos computadoras reales.
"""

from __future__ import annotations

import socket
import time

import pytest
from fastapi.testclient import TestClient

from backend.core.api import Engine, create_app
from backend.core.config import Settings
from backend.fleet import secret
from backend.fleet.service import FleetError


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _engine(tmp, name):
    e = Engine(Settings(token=f"tok-{name}", sample_interval=0.25, process_interval=0.5, data_dir=tmp.mktemp(name)))
    e.start()
    return e


@pytest.fixture(scope="module")
def lab(tmp_path_factory):
    a, b, console = (_engine(tmp_path_factory, n) for n in ("agente-a", "agente-b", "consola"))
    time.sleep(1.2)
    ports = {}
    for e in (a, b):
        e.remote.allow_loopback = True
        port = _free_port()
        e.remote.enable(port=port, addresses=["127.0.0.1"])
        ports[e] = port
    console.fleet.allow_loopback = True
    yield {"a": a, "b": b, "console": console, "ports": ports}
    for e in (a, b, console):
        e.remote.disable()
        e.stop()


def _pair(lab, agent) -> str:
    fleet = lab["console"].fleet
    code = agent.remote.auth.code_info()["codigo"] or agent.remote.new_code()["codigo"]
    start = fleet.start_pair("127.0.0.1", lab["ports"][agent], code, "Consola de pruebas")
    assert start["huella"] == agent.remote.fingerprint  # la huella vista es la del agente
    assert fleet.poll_pair(start["id"])["estado"] == "pendiente"
    pending = agent.remote.auth.pending()
    assert pending[0]["frase"] == start["frase"] and pending[0]["tipo"] == "consola"
    agent.remote.auth.decide(pending[0]["id"], True)
    done = fleet.poll_pair(start["id"])
    assert done["estado"] == "autorizada"
    return done["device_id"]


def test_two_agents_are_independent(lab):
    a, b, fleet = lab["a"], lab["b"], lab["console"].fleet
    id_a, id_b = _pair(lab, a), _pair(lab, b)
    assert id_a == a.remote.device_id and id_b == b.remote.device_id and id_a != id_b
    time.sleep(10.5)
    fleet.poll_once()
    devs = {d["id"]: d for d in fleet.devices()}
    assert set(devs) == {id_a, id_b}
    for d in devs.values():
        assert d["conectado"] and d["cpu"] is not None and d["ram"] is not None and d["disco"]
        assert abs(d["medido_en"] - time.time()) < 10
    hist_a = fleet.history(id_a, 1)["muestras"]
    assert hist_a and all(r["ts"] > 0 for r in hist_a)
    assert {r["device_id"] for r in fleet.db.query("SELECT DISTINCT device_id FROM fleet_samples")} == {id_a, id_b}
    procs = fleet.live(id_a, "procesos", "?by=memory&limit=3")
    assert procs["programas"]
    # La credencial no se guarda en claro.
    row = fleet.db.query("SELECT token_enc FROM fleet_devices WHERE id = ?", (id_a,))[0]
    assert secret.unprotect(row["token_enc"]) and b"plain:" not in row["token_enc"]


def test_revocation_marks_device_disconnected(lab):
    a, b, fleet = lab["a"], lab["b"], lab["console"].fleet
    if len(fleet.devices()) < 2:
        _pair(lab, a)
        _pair(lab, b)
    a.remote.disable()  # escenario D: la PC A desactiva el acceso remoto
    fleet.poll_once()
    devs = {d["id"]: d for d in fleet.devices()}
    da, db_ = devs[a.remote.device_id], devs[b.remote.device_id]
    assert not da["conectado"] and da["error"] and da["ultima_lectura"]  # se muestra la hora de la última lectura
    assert db_["conectado"]
    with pytest.raises(FleetError):
        fleet.live(a.remote.device_id, "procesos")
    # La reactivación sin nueva vinculación no devuelve el acceso (las sesiones se revocaron).
    a.remote.enable(port=lab["ports"][a], addresses=["127.0.0.1"])
    fleet.poll_once()
    assert not {d["id"]: d for d in fleet.devices()}[a.remote.device_id]["conectado"]


def test_pinned_fingerprint_is_enforced(lab):
    b, fleet = lab["b"], lab["console"].fleet
    did = b.remote.device_id
    if not fleet.db.query("SELECT 1 FROM fleet_devices WHERE id = ?", (did,)):
        _pair(lab, b)
    fleet.db.execute("UPDATE fleet_devices SET huella = ? WHERE id = ?", ("00:" * 31 + "00", did))
    fleet.poll_once()
    d = fleet.device(did)
    assert not d["conectado"] and "huella" in d["error"]


def test_unlink_also_revokes_on_agent(lab):
    b, fleet = lab["b"], lab["console"].fleet
    before = {s["id"] for s in b.remote.auth.sessions()}
    did = _pair(lab, b)
    mine = {s["id"] for s in b.remote.auth.sessions()} - before
    assert len(mine) == 1
    res = fleet.unlink(did)
    assert res["otra_pc_notificada"]
    assert not mine & {s["id"] for s in b.remote.auth.sessions()}  # la otra PC olvidó esta consola
    assert all(d["id"] != did for d in fleet.devices())


def test_rejects_public_addresses_and_wrong_codes(lab):
    fleet = lab["console"].fleet
    with pytest.raises(FleetError) as e:
        fleet.start_pair("8.8.8.8", 8765, "123456")
    assert e.value.status == 422
    with pytest.raises(FleetError):
        fleet.start_pair("no-es-una-ip", 8765, "123456")
    with pytest.raises(FleetError) as e:
        fleet.start_pair("127.0.0.1", lab["ports"][lab["b"]], "000000" if lab["b"].remote.auth.code_info()["codigo"] != "000000" else "111111")
    assert e.value.status == 401


def test_fleet_routes_require_local_token(lab):
    console = lab["console"]
    with TestClient(create_app(console.settings, console)) as c:
        assert c.get("/api/fleet/devices").status_code == 401
        c.headers["X-ScriptLens-Token"] = "tok-consola"
        body = c.get("/api/fleet/devices").json()
        assert body["esta_pc"]["device_id"] == console.remote.device_id
