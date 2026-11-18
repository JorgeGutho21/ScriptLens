"""Vinculación y sesiones del acceso remoto.

Flujo (el propietario de la PC decide siempre):

1. La PC muestra un **código temporal** de 6 cifras (caduca en 5 minutos).
2. El otro dispositivo lo escribe y envía una solicitud con un nombre descriptivo.
3. Ambos ven la misma **frase de verificación** (p. ej. «K7-3M»).
4. El propietario pulsa *Autorizar* en la PC. Solo entonces se crea una sesión.
5. El dispositivo recoge una única vez su credencial de sesión (cookie HttpOnly en navegadores,
   token en el cuerpo para la consola). Nunca viaja en la URL ni en un código QR.

Las credenciales se guardan solo como hash SHA-256, caducan y se pueden revocar una a una o todas
juntas al desactivar el acceso remoto. Los intentos fallidos se limitan por dirección IP y en total.
"""

from __future__ import annotations

import hashlib
import secrets
import threading
import time
from dataclasses import dataclass, field

CODE_TTL = 300  # segundos de validez del código temporal
REQUEST_TTL = 300  # una solicitud pendiente caduca si nadie la autoriza
SESSION_TTL = {"navegador": 12 * 3600, "consola": 30 * 86400}
MAX_FAILS_PER_IP = 5  # por ventana
FAIL_WINDOW = 60
LOCKOUT = 300
MAX_FAILS_GLOBAL = 20  # tras esto el código se invalida y hay que generar otro
MAX_PENDING = 10
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin 0/O ni 1/I para evitar confusiones


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _phrase() -> str:
    s = "".join(secrets.choice(_ALPHABET) for _ in range(4))
    return f"{s[:2]}-{s[2:]}"


class PairingError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


@dataclass
class PendingRequest:
    id: str
    nombre: str
    tipo: str
    ip: str
    frase: str
    creado: float
    estado: str = "pendiente"  # pendiente | autorizada | rechazada | entregada
    token: str | None = field(default=None, repr=False)
    session_id: str | None = None

    def public(self) -> dict:
        return {"id": self.id[:8], "nombre": self.nombre, "tipo": self.tipo, "ip": self.ip, "frase": self.frase, "creado": self.creado, "estado": self.estado}


class RemoteAuth:
    def __init__(self, db, clock=time.time):
        self.db = db
        self.clock = clock
        self._lock = threading.Lock()
        self._code: str | None = None
        self._code_expires = 0.0
        self._global_fails = 0
        self._fails: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}
        self._pending: dict[str, PendingRequest] = {}

    # --- Código temporal --------------------------------------------------
    def new_code(self) -> dict:
        with self._lock:
            self._code = f"{secrets.randbelow(1_000_000):06d}"
            self._code_expires = self.clock() + CODE_TTL
            self._global_fails = 0
            return self._code_info()

    def code_info(self) -> dict:
        with self._lock:
            return self._code_info()

    def _code_info(self) -> dict:
        if self._code is None or self.clock() >= self._code_expires:
            return {"codigo": None, "caduca_en": 0}
        return {"codigo": self._code, "caduca_en": round(self._code_expires - self.clock())}

    def clear_code(self) -> None:
        with self._lock:
            self._code = None

    # --- Solicitudes ------------------------------------------------------
    def _register_fail(self, ip: str, now: float) -> None:
        hist = [t for t in self._fails.get(ip, []) if now - t < FAIL_WINDOW]
        hist.append(now)
        self._fails[ip] = hist
        self._global_fails += 1
        if len(hist) >= MAX_FAILS_PER_IP:
            self._locked_until[ip] = now + LOCKOUT
        if self._global_fails >= MAX_FAILS_GLOBAL:
            self._code = None  # demasiados intentos: el propietario debe generar otro código

    def request(self, code: str, nombre: str, tipo: str, ip: str) -> PendingRequest:
        if tipo not in SESSION_TTL:
            raise PairingError(422, "Tipo de dispositivo no válido.")
        now = self.clock()
        with self._lock:
            if self._locked_until.get(ip, 0) > now:
                raise PairingError(429, "Demasiados intentos fallidos desde este dispositivo. Espere unos minutos.")
            self._purge(now)
            valid = self._code is not None and now < self._code_expires and secrets.compare_digest(str(code), self._code)
            if not valid:
                self._register_fail(ip, now)
                raise PairingError(401, "El código no es correcto o ya caducó. Pida en la PC un código nuevo.")
            if sum(1 for p in self._pending.values() if p.estado == "pendiente") >= MAX_PENDING:
                raise PairingError(429, "Hay demasiadas solicitudes pendientes en la PC.")
            req = PendingRequest(id=secrets.token_urlsafe(24), nombre=nombre.strip()[:60] or "Dispositivo", tipo=tipo, ip=ip, frase=_phrase(), creado=now)
            self._pending[req.id] = req
            return req

    def pending(self) -> list[dict]:
        with self._lock:
            self._purge(self.clock())
            return [p.public() for p in self._pending.values() if p.estado == "pendiente"]

    def _find_short(self, short_id: str) -> PendingRequest | None:
        for p in self._pending.values():
            if p.id[:8] == short_id and p.estado == "pendiente":
                return p
        return None

    def decide(self, short_id: str, approve: bool) -> dict:
        with self._lock:
            self._purge(self.clock())
            p = self._find_short(short_id)
            if p is None:
                raise PairingError(404, "La solicitud ya no existe o caducó.")
            if not approve:
                p.estado = "rechazada"
                return p.public()
            token = secrets.token_urlsafe(32)
            p.session_id = self._create_session(token, p.nombre, p.tipo, p.ip)
            p.token, p.estado = token, "autorizada"
            # Un código sirve para una sola vinculación aprobada.
            self._code = None
            return p.public()

    def poll(self, request_id: str) -> tuple[str, str | None, str | None]:
        """Estado de una solicitud. La credencial se entrega UNA sola vez."""
        with self._lock:
            self._purge(self.clock())
            p = self._pending.get(request_id)
            if p is None:
                return "caducada", None, None
            if p.estado == "autorizada":
                token, p.token, p.estado = p.token, None, "entregada"
                return "autorizada", token, p.tipo
            if p.estado == "entregada":
                return "entregada", None, None
            return p.estado, None, None

    def _purge(self, now: float) -> None:
        for k in [k for k, p in self._pending.items() if now - p.creado > REQUEST_TTL]:
            del self._pending[k]

    # --- Sesiones (persistentes en SQLite, solo el hash) -------------------
    def _create_session(self, token: str, nombre: str, tipo: str, ip: str) -> str:
        sid = secrets.token_hex(8)
        now = self.clock()
        self.db.execute(
            "INSERT INTO remote_sessions(id, token_hash, nombre, tipo, ip, created_at, expires_at, last_seen, last_ip) VALUES (?,?,?,?,?,?,?,?,?)",
            (sid, _hash(token), nombre, tipo, ip, now, now + SESSION_TTL[tipo], None, ip),
        )
        return sid

    def validate(self, token: str | None, ip: str) -> dict | None:
        if not token or len(token) > 200:
            return None
        rows = self.db.query("SELECT * FROM remote_sessions WHERE token_hash = ?", (_hash(token),))
        if not rows:
            return None
        s = rows[0]
        now = self.clock()
        if s["expires_at"] <= now:
            self.db.execute("DELETE FROM remote_sessions WHERE id = ?", (s["id"],))
            return None
        # Actualizar «última consulta» como mucho cada 5 s para no escribir en cada petición.
        if s["last_seen"] is None or now - s["last_seen"] > 5 or s["last_ip"] != ip:
            self.db.execute("UPDATE remote_sessions SET last_seen = ?, last_ip = ? WHERE id = ?", (now, ip, s["id"]))
            s["last_seen"], s["last_ip"] = now, ip
        return s

    def sessions(self) -> list[dict]:
        now = self.clock()
        self.db.execute("DELETE FROM remote_sessions WHERE expires_at <= ?", (now,))
        rows = self.db.query("SELECT id, nombre, tipo, ip, created_at, expires_at, last_seen, last_ip FROM remote_sessions ORDER BY created_at DESC")
        for r in rows:
            r["activa_ahora"] = r["last_seen"] is not None and now - r["last_seen"] < 30
        return rows

    def revoke(self, sid: str) -> bool:
        return self.db.execute("DELETE FROM remote_sessions WHERE id = ?", (sid,)).rowcount > 0

    def revoke_all(self) -> int:
        with self._lock:
            self._pending.clear()
            self._code = None
        return self.db.execute("DELETE FROM remote_sessions").rowcount
