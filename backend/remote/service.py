"""Ciclo de vida del acceso remoto: apagado → activo ⇄ pausado → apagado.

- **Apagado** (siempre al abrir ScriptLens): no se escucha en ninguna interfaz de red.
- **Activo**: servidor HTTPS en las IPv4 privadas del equipo, puerto fijo (8765 por defecto).
- **Pausado**: el servidor se detiene pero se conservan los dispositivos vinculados.
- **Desactivar**: detiene el servidor y revoca TODAS las sesiones y solicitudes.

El servidor remoto comparte el mismo ``Engine`` que la interfaz local (no duplica muestreos).
"""

from __future__ import annotations

import socket
import threading
import time
import uuid

from . import tls
from .auth import RemoteAuth
from .invites import Invites, effective_permissions
from .mailer import build_message, create_mailer
from .netinfo import device_name, local_addresses


class RemoteError(RuntimeError):
    pass


class RemoteService:
    def __init__(self, engine, allow_loopback: bool = False):
        self.engine = engine
        self.db = engine.db
        self.auth = RemoteAuth(engine.db)
        self.invites = Invites(engine.db, self.auth)
        self.allow_loopback = allow_loopback  # solo pruebas automáticas
        self.folder = engine.settings.data_dir / "remote"
        try:
            self.mailer = create_mailer(self.folder / "correo_salida")
        except ValueError as e:  # SMTP mal configurado: se cae al modo local y se informa
            self.mailer = create_mailer(self.folder / "correo_salida", env={})
            self.mail_error = str(e)
        else:
            self.mail_error = None
        self.device_id = self._device_id()
        self.fingerprint: str | None = None
        self.state = "apagado"
        self.error: str | None = None
        self.port: int | None = None
        self.addresses: list[str] = []
        self.started_at: float | None = None
        self._server = None
        self._thread: threading.Thread | None = None
        self._sockets: list[socket.socket] = []
        self._lock = threading.Lock()

    def _device_id(self) -> str:
        self.folder.mkdir(parents=True, exist_ok=True)
        f = self.folder / "device_id"
        try:
            value = f.read_text(encoding="ascii").strip()
            uuid.UUID(value)
            return value
        except (OSError, ValueError):
            value = str(uuid.uuid4())
            f.write_text(value, encoding="ascii")
            return value

    @property
    def serving(self) -> bool:
        return self.state == "activo"

    # --- Preferencias de lo que se comparte --------------------------------
    def sharing(self) -> dict:
        s = self.db.settings()
        return {"procesos": bool(s["remote_share_processes"]), "seguridad": bool(s["remote_share_security"]), "estadisticas": bool(s["remote_share_stats"])}

    def set_sharing(self, procesos: bool, seguridad: bool, estadisticas: bool) -> dict:
        self.db.set_setting("remote_share_processes", bool(procesos))
        self.db.set_setting("remote_share_security", bool(seguridad))
        self.db.set_setting("remote_share_stats", bool(estadisticas))
        return self.sharing()

    # --- Estado -------------------------------------------------------------
    def status(self) -> dict:
        addrs = local_addresses()
        port = self.port or int(self.db.settings()["remote_port"])
        urls = [f"https://{a}:{port}/" for a in self.addresses] if self.serving else []
        return {
            "estado": self.state,
            "error": self.error,
            "equipo": device_name(),
            "device_id": self.device_id,
            "puerto": port,
            "direcciones": self.addresses,
            "urls": urls,
            "interfaces": addrs,
            "hay_red_local": any(not a["virtual"] and not a["enlace_local"] for a in addrs),
            "huella": self.fingerprint,
            "huella_corta": tls.short_fingerprint(self.fingerprint) if self.fingerprint else None,
            "codigo": self.auth.code_info() if self.serving else {"codigo": None, "caduca_en": 0},
            "solicitudes": self.auth.pending() if self.serving else [],
            "sesiones": self.auth.sessions(),
            "comparte": self.sharing(),
            "activo_desde": self.started_at,
            "invitaciones": self.invites.list(),
            "correo": {"modo": self.mailer.mode, "error": self.mail_error, "salida": str(self.mailer.folder) if self.mailer.mode == "local" else None},
        }

    def permissions(self, session: dict) -> dict:
        return effective_permissions(self.sharing(), session)

    # --- Invitaciones por correo -----------------------------------------------
    def invite(self, correo: str, permisos: dict, validez_min: int, horas: int) -> dict:
        if not self.serving or not self.addresses:
            raise RemoteError("Active el acceso remoto antes de invitar: el enlace apunta a la dirección local de esta PC.")
        inv, token = self.invites.create(correo, permisos, validez_min, horas)
        enlace = f"https://{self.addresses[0]}:{self.port}/#invitacion={token}"
        msg = build_message(to=inv["correo"], sender=self.mailer.sender, equipo=device_name(), enlace=enlace,
                            huella=self.fingerprint or "", caduca=inv["caduca"], horas=inv["horas"], permisos=inv["permisos"])
        try:
            envio = self.mailer.send(msg, inv["id"])
        except Exception as e:  # noqa: BLE001 — el envío falló: la invitación no debe quedar utilizable
            self.invites.revoke(inv["id"])
            raise RemoteError(f"No se pudo enviar el correo ({type(e).__name__}). La invitación se anuló.") from e
        out = {"invitacion": self.invites.get(inv["id"]), "envio": envio}
        if envio["modo"] == "local":
            # Solo en modo de prueba: el propietario necesita el enlace para entregarlo él mismo.
            out["enlace"] = enlace
        return out

    # --- Transiciones ---------------------------------------------------------
    def enable(self, port: int | None = None, addresses: list[str] | None = None) -> dict:
        with self._lock:
            if self.serving:
                return self.status()
            port = int(port or self.db.settings()["remote_port"])
            if not 1024 <= port <= 65535:
                raise RemoteError("El puerto debe estar entre 1024 y 65535.")
            if addresses is None:
                addresses = [a["ip"] for a in local_addresses() if not a["virtual"] and not a["enlace_local"]] or [a["ip"] for a in local_addresses()]
            if not addresses:
                self.error = "No se encontró ninguna red local activa (WiFi, cable o hotspot)."
                raise RemoteError(self.error)
            cert, key, self.fingerprint = tls.ensure_certificate(self.folder)
            self._start(cert, key, port, addresses)
            self.db.set_setting("remote_port", port)
            if self.state == "apagado":
                self.auth.new_code()
            self.state, self.error, self.started_at = "activo", None, time.time()
        return self.status()

    def pause(self) -> dict:
        with self._lock:
            self._stop()
            if self.state == "activo":
                self.state = "pausado"
            self.auth.clear_code()
        return self.status()

    def disable(self) -> dict:
        with self._lock:
            self._stop()
            revoked = self.auth.revoke_all()
            self.invites.revoke_all()
            self.state, self.started_at = "apagado", None
        st = self.status()
        st["sesiones_revocadas"] = revoked
        return st

    def new_code(self) -> dict:
        if not self.serving:
            raise RemoteError("Active el acceso remoto para generar un código.")
        return self.auth.new_code()

    # --- Servidor ----------------------------------------------------------------
    def _start(self, cert, key, port: int, addresses: list[str]) -> None:
        import uvicorn

        from .app import create_remote_app

        socks: list[socket.socket] = []
        try:
            for ip in addresses:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                s.bind((ip, port))
                s.listen(64)
                socks.append(s)
        except OSError as e:
            for s in socks:
                s.close()
            self.error = f"No se pudo usar el puerto {port} ({e.strerror or e}). Puede que otro programa lo esté usando."
            raise RemoteError(self.error) from e

        config = uvicorn.Config(
            create_remote_app(self),
            ssl_certfile=str(cert),
            ssl_keyfile=str(key),
            log_level="warning",
            access_log=False,
            lifespan="off",
            timeout_graceful_shutdown=2,
            server_header=False,
        )
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, kwargs={"sockets": socks}, daemon=True, name="sl-remote")
        thread.start()
        deadline = time.monotonic() + 10
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.05)
        if not server.started:
            server.should_exit = True
            for s in socks:
                s.close()
            self.error = "El servidor remoto no pudo iniciar."
            raise RemoteError(self.error)
        self._server, self._thread, self._sockets = server, thread, socks
        self.port, self.addresses = port, addresses

    def _stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
            if self._thread is not None:
                self._thread.join(timeout=6)
        for s in self._sockets:
            try:
                s.close()
            except OSError:
                pass
        self._server, self._thread, self._sockets = None, None, []
        self.addresses = []

    def shutdown(self) -> None:
        with self._lock:
            self._stop()
