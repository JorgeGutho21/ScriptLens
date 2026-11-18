"""Consola central: vincula otras PC con ScriptLens y las consulta periódicamente.

Patrón tomado de Beszel (*hub* que consulta *agentes*) adaptado a ScriptLens:
- El «agente» es cualquier PC con el acceso remoto activado; no se instala nada oculto ni
  persistente. La participación la decide esa PC (activar, pausar, revocar).
- La consola guarda por equipo: huella TLS fijada, credencial cifrada con DPAPI, última
  lectura y un historial reducido (una muestra cada ~10 s) con ``device_id`` y hora.
- Si un equipo no responde se marca **Desconectado** con la hora de su última lectura; sus
  cifras nunca se presentan como actuales.
"""

from __future__ import annotations

import ipaddress
import json
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from backend.remote.netinfo import device_name, is_allowed_client
from backend.remote.tls import short_fingerprint

from . import secret
from .client import AgentClient, AgentError

POLL_INTERVAL = 5.0
ONLINE_WINDOW = 20.0  # sin lectura en este tiempo → desconectado
HISTORY_EVERY = 10.0
HISTORY_DAYS = 7
PAIR_TTL = 300


class FleetError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message


class FleetService:
    def __init__(self, engine, allow_loopback: bool = False):
        self.engine = engine
        self.db = engine.db
        self.allow_loopback = allow_loopback  # solo pruebas
        self._pending: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._errors: dict[str, dict] = {}
        self._last_hist: dict[str, float] = {}
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="sl-fleet")

    # --- Vinculación ------------------------------------------------------
    def _validate_host(self, host: str) -> str:
        host = host.strip()
        try:
            ipaddress.ip_address(host)
        except ValueError as e:
            raise FleetError(422, "Escriba la dirección IP que muestra la otra PC (por ejemplo 192.168.1.25).") from e
        if not is_allowed_client(host, self.allow_loopback):
            raise FleetError(422, "Solo se pueden vincular equipos de la red local (direcciones privadas).")
        return host

    def start_pair(self, host: str, port: int, code: str, nombre: str | None = None) -> dict:
        host = self._validate_host(host)
        client = AgentClient(host, port)
        try:
            r = client.call("POST", "/remote/api/pair/request", {"codigo": code, "nombre": (nombre or f"Consola en {device_name()}")[:60], "tipo": "consola"})
        except AgentError as e:
            raise FleetError(e.status or 502, str(e)) from e
        if r.get("huella") and r["huella"] != client.seen_fingerprint:
            raise FleetError(502, "La huella anunciada no coincide con el certificado recibido.")
        pid = secrets.token_hex(6)
        with self._lock:
            self._pending[pid] = {
                "host": host,
                "port": port,
                "solicitud": r["solicitud"],
                "frase": r["frase"],
                "equipo": r["equipo"],
                "device_id": r["device_id"],
                "huella": client.seen_fingerprint,
                "creado": time.time(),
            }
        return {"id": pid, "frase": r["frase"], "equipo": r["equipo"], "huella": client.seen_fingerprint, "huella_corta": short_fingerprint(client.seen_fingerprint)}

    def poll_pair(self, pid: str) -> dict:
        with self._lock:
            p = self._pending.get(pid)
        if p is None or time.time() - p["creado"] > PAIR_TTL:
            raise FleetError(404, "La vinculación caducó. Pida en la otra PC un código nuevo.")
        client = AgentClient(p["host"], p["port"], p["huella"])
        try:
            r = client.call("GET", f"/remote/api/pair/status?solicitud={p['solicitud']}")
        except AgentError as e:
            raise FleetError(e.status or 502, str(e)) from e
        estado = r.get("estado")
        if estado != "autorizada":
            if estado in ("rechazada", "caducada", "entregada"):
                with self._lock:
                    self._pending.pop(pid, None)
            return {"estado": estado}
        if r.get("device_id") != p["device_id"] or r.get("huella") != p["huella"]:
            raise FleetError(502, "La identidad del equipo cambió durante la vinculación; se canceló por seguridad.")
        with self._lock:
            self._pending.pop(pid, None)
        if r["device_id"] == self.engine.remote.device_id:
            raise FleetError(409, "Esa es esta misma PC: ya aparece como «Esta PC».")
        old = self._row(r["device_id"])
        if old is not None:
            # Volver a vincular reemplaza: se cierra antes la sesión anterior en la otra PC.
            try:
                oc, ot = self._client(old)
                oc.timeout = 2
                oc.call("POST", "/remote/api/logout", token=ot)
            except (AgentError, OSError):
                pass
            self.db.execute("DELETE FROM fleet_devices WHERE id = ?", (r["device_id"],))
        self.db.execute(
            "INSERT INTO fleet_devices(id, nombre, direccion, puerto, huella, token_enc, created_at) VALUES (?,?,?,?,?,?,?)",
            (r["device_id"], p["equipo"], p["host"], p["port"], p["huella"], secret.protect(r["token"]), time.time()),
        )
        self._poll_device(self._row(r["device_id"]))
        return {"estado": "autorizada", "device_id": r["device_id"], "equipo": p["equipo"]}

    # --- Consulta periódica ------------------------------------------------
    def start(self) -> None:
        if self._thread is None:
            self._thread = threading.Thread(target=self._loop, daemon=True, name="sl-fleet-poll")
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._pool.shutdown(wait=False, cancel_futures=True)

    def _loop(self) -> None:
        while not self._stop.wait(POLL_INTERVAL):
            try:
                self.poll_once()
            except Exception:  # noqa: BLE001 — un equipo con problemas no debe detener la consola
                pass

    def _row(self, did: str) -> dict | None:
        rows = self.db.query("SELECT * FROM fleet_devices WHERE id = ?", (did,))
        return rows[0] if rows else None

    def poll_once(self) -> None:
        rows = self.db.query("SELECT * FROM fleet_devices")
        list(self._pool.map(self._poll_device, rows))
        cutoff = time.time() - HISTORY_DAYS * 86400
        self.db.execute("DELETE FROM fleet_samples WHERE ts < ?", (cutoff,))

    def _client(self, row: dict) -> tuple[AgentClient, str]:
        return AgentClient(row["direccion"], row["puerto"], row["huella"]), secret.unprotect(row["token_enc"])

    def _poll_device(self, row: dict | None) -> None:
        if row is None:
            return
        try:
            client, token = self._client(row)
            o = client.call("GET", "/remote/api/overview", token=token)
        except AgentError as e:
            msg = {"revocado": "La otra PC revocó el acceso o desactivó el acceso remoto.", "huella": str(e)}.get(e.kind, str(e))
            self._errors[row["id"]] = {"tipo": e.kind, "mensaje": msg, "hora": time.time()}
            self.db.execute("UPDATE fleet_devices SET last_error = ? WHERE id = ?", (msg, row["id"]))
            return
        if o.get("device_id") != row["id"]:
            self.db.execute("UPDATE fleet_devices SET last_error = ? WHERE id = ?", ("El equipo que responde en esa dirección no es el vinculado.", row["id"]))
            return
        now = time.time()
        self._errors.pop(row["id"], None)
        self.db.execute("UPDATE fleet_devices SET last_ok = ?, last_error = NULL, last_overview_json = ?, nombre = ? WHERE id = ?", (now, json.dumps(o), o["equipo"], row["id"]))
        s = o.get("actual")
        if s and now - self._last_hist.get(row["id"], 0) >= HISTORY_EVERY:
            self._last_hist[row["id"]] = now
            main = max(o["discos"], key=lambda d: d["total"], default=None)
            self.db.execute(
                "INSERT OR REPLACE INTO fleet_samples(device_id, ts, cpu, ram, disk_pct, net_sent, net_recv, uptime) VALUES (?,?,?,?,?,?,?,?)",
                (row["id"], s["ts"], s["cpu_percent"], s["mem_percent"], main["porcentaje"] if main else None, s["net_sent_bps"], s["net_recv_bps"], o["tiempo_encendido_s"]),
            )

    # --- Consultas para la interfaz ------------------------------------------
    def _summary(self, row: dict) -> dict:
        o = json.loads(row["last_overview_json"]) if row["last_overview_json"] else None
        now = time.time()
        online = row["last_ok"] is not None and now - row["last_ok"] < ONLINE_WINDOW and not row["last_error"]
        cur = (o or {}).get("actual") or {}
        main = max((o or {}).get("discos", []), key=lambda d: d["total"], default=None)
        err = self._errors.get(row["id"])
        alerts = []
        if online and cur.get("cpu_percent", 0) >= 90:
            alerts.append("CPU muy alta")
        if online and cur.get("mem_percent", 0) >= 90:
            alerts.append("RAM casi llena")
        if main and main["porcentaje"] >= 90:
            alerts.append(f"Disco {main['unidad']} casi lleno")
        if err and err["tipo"] in ("revocado", "huella"):
            alerts.append(err["mensaje"])
        return {
            "id": row["id"],
            "nombre": row["nombre"],
            "direccion": f"{row['direccion']}:{row['puerto']}",
            "huella_corta": short_fingerprint(row["huella"]),
            "conectado": online,
            "ultima_lectura": row["last_ok"],
            "medido_en": (o or {}).get("medido_en"),
            "error": row["last_error"],
            "so": (o or {}).get("so"),
            # Las cifras se entregan siempre con su hora; la interfaz las marca como antiguas si no hay conexión.
            "cpu": cur.get("cpu_percent"),
            "ram": cur.get("mem_percent"),
            "ram_usada": cur.get("mem_used"),
            "ram_total": cur.get("mem_total"),
            "disco": {"unidad": main["unidad"], "porcentaje": main["porcentaje"], "libre": main["libre"]} if main else None,
            "tiempo_encendido_s": (o or {}).get("tiempo_encendido_s"),
            "alertas": alerts,
            "vinculado": row["created_at"],
        }

    def devices(self) -> list[dict]:
        return [self._summary(r) for r in self.db.query("SELECT * FROM fleet_devices ORDER BY nombre")]

    def device(self, did: str) -> dict:
        row = self._row(did)
        if row is None:
            raise FleetError(404, "Equipo no vinculado")
        out = self._summary(row)
        out["overview"] = json.loads(row["last_overview_json"]) if row["last_overview_json"] else None
        return out

    def live(self, did: str, what: str, params: str = "") -> dict:
        """Consulta directa (procesos, hallazgos, estadísticas) a un equipo conectado."""
        paths = {"procesos": "/remote/api/processes", "hallazgos": "/remote/api/findings", "estadisticas": "/remote/api/stats"}
        row = self._row(did)
        if row is None:
            raise FleetError(404, "Equipo no vinculado")
        client, token = self._client(row)
        try:
            return client.call("GET", paths[what] + params, token=token)
        except AgentError as e:
            raise FleetError(e.status if e.status in (401, 403) else 502, str(e)) from e

    def history(self, did: str, hours: int) -> dict:
        since = time.time() - hours * 3600
        rows = self.db.query("SELECT ts, cpu, ram, disk_pct, net_sent, net_recv FROM fleet_samples WHERE device_id = ? AND ts >= ? ORDER BY ts", (did, since))
        return {"device_id": did, "muestras": rows}

    def unlink(self, did: str) -> dict:
        row = self._row(did)
        if row is None:
            raise FleetError(404, "Equipo no vinculado")
        notified = False
        try:
            client, token = self._client(row)
            client.timeout = 2
            client.call("POST", "/remote/api/logout", token=token)  # la otra PC también olvida esta consola
            notified = True
        except AgentError:
            pass
        self.db.execute("DELETE FROM fleet_devices WHERE id = ?", (did,))
        self._errors.pop(did, None)
        return {"desvinculado": did, "otra_pc_notificada": notified}
