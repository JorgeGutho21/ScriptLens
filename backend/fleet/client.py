"""Cliente HTTPS hacia el acceso remoto de otra PC, con la huella del certificado fijada.

La primera conexión (al vincular) registra la huella que presenta la otra PC; la persona la
compara con la que se ve en esa pantalla. Desde entonces cualquier otro certificado se rechaza,
lo que impide que un tercero en la red se haga pasar por el equipo.
"""

from __future__ import annotations

import http.client
import json
import ssl

from backend.remote.tls import fingerprint_der


class AgentError(Exception):
    def __init__(self, message: str, status: int | None = None, kind: str = "red"):
        super().__init__(message)
        self.status = status
        self.kind = kind  # red | huella | revocado | rechazo


class AgentClient:
    def __init__(self, host: str, port: int, fingerprint: str | None = None, timeout: float = 4.0):
        self.host, self.port, self.fingerprint, self.timeout = host, port, fingerprint, timeout
        ctx = ssl.create_default_context()
        # La autenticidad se garantiza con la huella fijada, no con una autoridad de certificación.
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        self._ctx = ctx
        self.seen_fingerprint: str | None = None

    def call(self, method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
        conn = http.client.HTTPSConnection(self.host, self.port, context=self._ctx, timeout=self.timeout)
        try:
            try:
                conn.connect()
            except (OSError, ssl.SSLError) as e:
                raise AgentError(f"Sin respuesta de {self.host}:{self.port}") from e
            fp = fingerprint_der(conn.sock.getpeercert(binary_form=True))
            self.seen_fingerprint = fp
            if self.fingerprint and fp != self.fingerprint:
                raise AgentError("El certificado del equipo cambió: la huella no coincide con la registrada al vincular.", kind="huella")
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            try:
                conn.request(method, path, json.dumps(body) if body is not None else None, headers)
                resp = conn.getresponse()
                raw = resp.read(2_000_000)
            except (OSError, http.client.HTTPException) as e:
                raise AgentError(f"Conexión interrumpida con {self.host}") from e
        finally:
            conn.close()
        try:
            data = json.loads(raw) if raw else {}
        except ValueError as e:
            raise AgentError("Respuesta no válida del equipo", resp.status) from e
        if resp.status == 401:
            raise AgentError(data.get("detail") or "Acceso revocado", 401, "revocado")
        if resp.status >= 400:
            raise AgentError(data.get("detail") or f"Error {resp.status}", resp.status, "rechazo")
        return data
