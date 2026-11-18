"""Persistencia local en SQLite (scriptlens.db dentro de la carpeta de datos de la aplicación).

Todo permanece en el equipo. El usuario puede desactivar el historial y borrar
diagnósticos, conversaciones o el registro de acciones desde Ajustes.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path

SCHEMA_VERSION = 3

_MIGRATIONS = {
    1: """
    CREATE TABLE IF NOT EXISTS diagnostics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at REAL NOT NULL,
        label TEXT NOT NULL,
        window_seconds INTEGER NOT NULL,
        cpu_avg REAL, ram_avg REAL, ram_used INTEGER, ram_total INTEGER,
        swap_avg REAL, process_count INTEGER,
        disks_json TEXT NOT NULL DEFAULT '[]',
        findings_json TEXT NOT NULL DEFAULT '[]'
    );
    CREATE TABLE IF NOT EXISTS diagnostic_processes (
        diagnostic_id INTEGER NOT NULL REFERENCES diagnostics(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        instances INTEGER NOT NULL,
        cpu_avg REAL,
        memory INTEGER,
        PRIMARY KEY (diagnostic_id, name)
    );
    CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at REAL NOT NULL,
        action TEXT NOT NULL,
        target TEXT NOT NULL,
        result TEXT NOT NULL,
        detail TEXT,
        before_json TEXT,
        after_json TEXT
    );
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at REAL NOT NULL,
        title TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        created_at REAL NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        evidence_json TEXT
    );
    CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """,
    # v0.2: acceso remoto, consola de varias computadoras y estadísticas persistentes.
    2: """
    CREATE TABLE IF NOT EXISTS remote_sessions (
        id TEXT PRIMARY KEY,
        token_hash TEXT NOT NULL UNIQUE,
        nombre TEXT NOT NULL,
        tipo TEXT NOT NULL,
        ip TEXT NOT NULL,
        created_at REAL NOT NULL,
        expires_at REAL NOT NULL,
        last_seen REAL,
        last_ip TEXT
    );
    CREATE TABLE IF NOT EXISTS fleet_devices (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        direccion TEXT NOT NULL,
        puerto INTEGER NOT NULL,
        huella TEXT NOT NULL,
        token_enc BLOB NOT NULL,
        created_at REAL NOT NULL,
        last_ok REAL,
        last_error TEXT,
        last_overview_json TEXT
    );
    CREATE TABLE IF NOT EXISTS fleet_samples (
        device_id TEXT NOT NULL REFERENCES fleet_devices(id) ON DELETE CASCADE,
        ts REAL NOT NULL,
        cpu REAL, ram REAL, disk_pct REAL, net_sent REAL, net_recv REAL, uptime REAL,
        PRIMARY KEY (device_id, ts)
    );
    CREATE TABLE IF NOT EXISTS stats_minute (
        ts INTEGER PRIMARY KEY,
        samples INTEGER NOT NULL,
        cpu_avg REAL, cpu_max REAL, ram_avg REAL, ram_max REAL,
        disk_read REAL, disk_write REAL, net_sent REAL, net_recv REAL,
        active_seconds REAL, session_user INTEGER
    );
    CREATE TABLE IF NOT EXISTS stats_hour (
        ts INTEGER PRIMARY KEY,
        minutes INTEGER NOT NULL,
        cpu_avg REAL, cpu_max REAL, ram_avg REAL, ram_max REAL,
        disk_read REAL, disk_write REAL, net_sent REAL, net_recv REAL,
        active_seconds REAL
    );
    CREATE TABLE IF NOT EXISTS stats_proc_hour (
        ts INTEGER NOT NULL,
        name TEXT NOT NULL,
        cpu_avg REAL NOT NULL,
        ram_max INTEGER NOT NULL,
        minutes INTEGER NOT NULL,
        PRIMARY KEY (ts, name)
    );
    CREATE TABLE IF NOT EXISTS app_usage (
        ts INTEGER NOT NULL,
        app TEXT NOT NULL,
        seconds REAL NOT NULL,
        PRIMARY KEY (ts, app)
    );
    CREATE TABLE IF NOT EXISTS boots (
        boot_time INTEGER PRIMARY KEY,
        source TEXT NOT NULL,
        shutdown_time INTEGER
    );
    CREATE TABLE IF NOT EXISTS stats_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at REAL NOT NULL,
        kind TEXT NOT NULL,
        detail TEXT NOT NULL,
        value REAL,
        minutes INTEGER
    );
    CREATE INDEX IF NOT EXISTS idx_fleet_samples_ts ON fleet_samples(ts);
    CREATE INDEX IF NOT EXISTS idx_app_usage_ts ON app_usage(ts);
    """,
    # v0.3: invitaciones por correo con enlace de un solo uso y permisos por sesión.
    3: """
    ALTER TABLE remote_sessions ADD COLUMN permisos TEXT;
    ALTER TABLE remote_sessions ADD COLUMN correo TEXT;
    CREATE TABLE IF NOT EXISTS remote_invites (
        id TEXT PRIMARY KEY,
        correo TEXT NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        permisos TEXT NOT NULL,
        horas INTEGER NOT NULL,
        created_at REAL NOT NULL,
        expires_at REAL NOT NULL,
        used_at REAL,
        used_ip TEXT,
        session_id TEXT,
        revoked_at REAL,
        fails INTEGER NOT NULL DEFAULT 0
    );
    """,
}

DEFAULT_SETTINGS = {
    "history_enabled": True,
    "conversations_enabled": True,
    # Acceso remoto (siempre arranca apagado; estas son preferencias de lo que se comparte).
    "remote_port": 8765,
    "remote_share_processes": True,
    "remote_share_security": True,
    "remote_share_stats": True,
    # Estadísticas
    "stats_enabled": True,
    "stats_retention_days": 90,  # detalle por minuto se conserva 7 días; esto aplica a horas y alertas
    "app_tracking_enabled": False,  # aplicaciones en primer plano: solo con consentimiento explícito
}


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._migrate()

    def _migrate(self) -> None:
        with self._lock:
            current = self._conn.execute("PRAGMA user_version").fetchone()[0]
            for version in range(current + 1, SCHEMA_VERSION + 1):
                self._conn.executescript(_MIGRATIONS[version])
                self._conn.execute(f"PRAGMA user_version = {version}")
            self._conn.commit()

    def execute(self, sql: str, params=()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return cur

    def query(self, sql: str, params=()) -> list[dict]:
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # --- Ajustes -----------------------------------------------------------
    def settings(self) -> dict:
        stored = {r["key"]: json.loads(r["value"]) for r in self.query("SELECT key, value FROM settings")}
        return {**DEFAULT_SETTINGS, **stored}

    def set_setting(self, key: str, value) -> None:
        if key not in DEFAULT_SETTINGS:
            raise KeyError(key)
        self.execute("INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, json.dumps(value)))

    # --- Registro de acciones (auditoría) ---------------------------------
    def log_action(self, action: str, target: str, result: str, detail: str = "", before=None, after=None) -> int:
        cur = self.execute(
            "INSERT INTO actions(created_at, action, target, result, detail, before_json, after_json) VALUES (?,?,?,?,?,?,?)",
            (time.time(), action, target, result, detail, json.dumps(before) if before is not None else None, json.dumps(after) if after is not None else None),
        )
        return cur.lastrowid

    def actions(self, limit: int = 200) -> list[dict]:
        rows = self.query("SELECT * FROM actions ORDER BY id DESC LIMIT ?", (limit,))
        for r in rows:
            r["before"] = json.loads(r.pop("before_json") or "null")
            r["after"] = json.loads(r.pop("after_json") or "null")
        return rows

    def clear(self, what: str) -> int:
        tables = {"diagnostics": "diagnostics", "conversations": "conversations", "actions": "actions"}
        if what not in tables:
            raise KeyError(what)
        return self.execute(f"DELETE FROM {tables[what]}").rowcount
