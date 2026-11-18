"""Invitaciones por correo: enlace de un solo uso + correo del destinatario como llave.

Flujo
1. El propietario escribe un correo y elige qué secciones podrá ver esa persona y durante cuánto
   tiempo. Se genera un token aleatorio de 256 bits; en la base de datos solo se guarda su hash.
2. El correo lleva el enlace ``https://<IP local>:<puerto>/#invitacion=<token>``. El token va en el
   **fragmento** (después de ``#``): el navegador no lo envía al servidor ni queda en registros.
3. Al abrir el enlace, la página pide al destinatario que escriba su correo. El servidor comprueba
   token (hash), correo, caducidad, revocación y que no se haya usado, en una sola operación atómica.
4. Si todo coincide, se crea una sesión de solo lectura con los permisos de la invitación y se
   entrega como cookie HttpOnly. El enlace queda gastado.

Defensas: un solo uso, caducidad, 3 correos erróneos bloquean la invitación, límite de intentos por
IP, mensajes de error que no revelan si falló el token o el correo, y revocación en cualquier momento.
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import threading
import time

from .auth import PairingError, _hash

PERMISOS = ("procesos", "seguridad", "estadisticas")
VALIDEZ_MIN = (5, 1440)  # minutos que el enlace puede esperar a ser abierto
HORAS_ACCESO = (1, 12)  # duración de la sesión creada al abrirlo
MAX_FAILS_INVITE = 3
MAX_FAILS_PER_IP = 5
FAIL_WINDOW = 60
LOCKOUT = 300
MAX_PENDING = 20
_EMAIL = re.compile(r"^[^@\s<>\"',;]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")
GENERIC = "El enlace no es válido, ya se usó, caducó o el correo no coincide con la invitación."


def normalize_email(correo: str) -> str:
    return (correo or "").strip().lower()


def valid_email(correo: str) -> bool:
    c = normalize_email(correo)
    return len(c) <= 254 and bool(_EMAIL.match(c))


def _email_hash(correo: str) -> str:
    return hashlib.sha256(normalize_email(correo).encode("utf-8")).hexdigest()


class Invites:
    def __init__(self, db, auth, clock=time.time):
        self.db = db
        self.auth = auth
        self.clock = clock
        self._lock = threading.Lock()
        self._fails: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}

    # --- Propietario (API local) -----------------------------------------
    def create(self, correo: str, permisos: dict, validez_min: int, horas: int) -> tuple[dict, str]:
        correo = normalize_email(correo)
        if not valid_email(correo):
            raise PairingError(422, "Escriba un correo electrónico válido.")
        if not VALIDEZ_MIN[0] <= validez_min <= VALIDEZ_MIN[1]:
            raise PairingError(422, "La validez del enlace debe estar entre 5 minutos y 24 horas.")
        if not HORAS_ACCESO[0] <= horas <= HORAS_ACCESO[1]:
            raise PairingError(422, "El acceso debe durar entre 1 y 12 horas.")
        now = self.clock()
        pending = self.db.query("SELECT COUNT(*) AS n FROM remote_invites WHERE used_at IS NULL AND revoked_at IS NULL AND expires_at > ?", (now,))[0]["n"]
        if pending >= MAX_PENDING:
            raise PairingError(429, "Hay demasiadas invitaciones pendientes. Revoque alguna antes de crear otra.")
        perms = {k: bool(permisos.get(k)) for k in PERMISOS}
        token = secrets.token_urlsafe(32)
        iid = secrets.token_hex(8)
        self.db.execute(
            "INSERT INTO remote_invites(id, correo, token_hash, permisos, horas, created_at, expires_at) VALUES (?,?,?,?,?,?,?)",
            (iid, correo, _hash(token), json.dumps(perms), horas, now, now + validez_min * 60),
        )
        return self.get(iid), token

    def get(self, iid: str) -> dict | None:
        rows = self.db.query("SELECT * FROM remote_invites WHERE id = ?", (iid,))
        return self._public(rows[0]) if rows else None

    def _public(self, r: dict) -> dict:
        now = self.clock()
        if r["revoked_at"] is not None:
            estado = "bloqueada" if r["fails"] >= MAX_FAILS_INVITE and r["used_at"] is None else "revocada"
        elif r["used_at"] is not None:
            estado = "usada"
        elif r["expires_at"] <= now:
            estado = "caducada"
        else:
            estado = "pendiente"
        return {
            "id": r["id"],
            "correo": r["correo"],
            "permisos": json.loads(r["permisos"]),
            "horas": r["horas"],
            "creada": r["created_at"],
            "caduca": r["expires_at"],
            "usada": r["used_at"],
            "estado": estado,
            "sesion_activa": bool(r["session_id"]) and bool(self.db.query("SELECT 1 FROM remote_sessions WHERE id = ?", (r["session_id"],))),
        }

    def list(self) -> list[dict]:
        # Se conservan 7 días para que el propietario vea qué se envió y si se usó.
        self.db.execute("DELETE FROM remote_invites WHERE created_at < ?", (self.clock() - 7 * 86400,))
        return [self._public(r) for r in self.db.query("SELECT * FROM remote_invites ORDER BY created_at DESC LIMIT 50")]

    def revoke(self, iid: str) -> bool:
        rows = self.db.query("SELECT session_id FROM remote_invites WHERE id = ?", (iid,))
        if not rows:
            return False
        self.db.execute("UPDATE remote_invites SET revoked_at = COALESCE(revoked_at, ?) WHERE id = ?", (self.clock(), iid))
        if rows[0]["session_id"]:
            self.auth.revoke(rows[0]["session_id"])
        return True

    def revoke_all(self) -> int:
        return self.db.execute("UPDATE remote_invites SET revoked_at = ? WHERE revoked_at IS NULL AND used_at IS NULL", (self.clock(),)).rowcount

    # --- Destinatario (servidor remoto) ------------------------------------
    def _fail_ip(self, ip: str, now: float) -> None:
        hist = [t for t in self._fails.get(ip, []) if now - t < FAIL_WINDOW]
        hist.append(now)
        self._fails[ip] = hist
        if len(hist) >= MAX_FAILS_PER_IP:
            self._locked_until[ip] = now + LOCKOUT

    def accept(self, token: str, correo: str, ip: str) -> tuple[str, dict]:
        """Devuelve (credencial de sesión, sesión). Lanza ``PairingError`` sin detallar la causa."""
        now = self.clock()
        with self._lock:
            if self._locked_until.get(ip, 0) > now:
                raise PairingError(429, "Demasiados intentos fallidos desde este dispositivo. Espere unos minutos.")
            rows = self.db.query("SELECT * FROM remote_invites WHERE token_hash = ?", (_hash(token or ""),)) if token and len(token) <= 100 else []
            if not rows:
                self._fail_ip(ip, now)
                raise PairingError(401, GENERIC)
            inv = rows[0]
            if not secrets.compare_digest(_email_hash(correo), _email_hash(inv["correo"])):
                self._fail_ip(ip, now)
                fails = inv["fails"] + 1
                self.db.execute("UPDATE remote_invites SET fails = ?, revoked_at = CASE WHEN ? >= ? THEN COALESCE(revoked_at, ?) ELSE revoked_at END WHERE id = ?",
                                (fails, fails, MAX_FAILS_INVITE, now, inv["id"]))
                raise PairingError(401, GENERIC)
            # Gastar el enlace de forma atómica: si dos dispositivos lo abren a la vez, solo uno entra.
            used = self.db.execute(
                "UPDATE remote_invites SET used_at = ?, used_ip = ? WHERE id = ? AND used_at IS NULL AND revoked_at IS NULL AND expires_at > ?",
                (now, ip, inv["id"], now),
            ).rowcount
            if used != 1:
                self._fail_ip(ip, now)
                raise PairingError(401, GENERIC)
            session_token = secrets.token_urlsafe(32)
            sid = self.auth._create_session(session_token, inv["correo"], "navegador", ip, ttl=inv["horas"] * 3600, permisos=inv["permisos"], correo=inv["correo"])
            self.db.execute("UPDATE remote_invites SET session_id = ? WHERE id = ?", (sid, inv["id"]))
            return session_token, {"id": sid, "correo": inv["correo"], "horas": inv["horas"], "permisos": json.loads(inv["permisos"])}


def effective_permissions(sharing: dict, session: dict) -> dict:
    """Lo que puede ver una sesión: lo que comparte la PC Y lo que permite su invitación."""
    raw = session.get("permisos")
    if not raw:
        return dict(sharing)
    own = json.loads(raw)
    return {k: bool(sharing.get(k)) and bool(own.get(k)) for k in PERMISOS}
