"""Rutas del Centro de seguridad (consultas de solo lectura bajo demanda)."""

from __future__ import annotations

import threading

from fastapi import APIRouter

from . import audit, collect


class SecurityState:
    """Último resultado de auditoría; se ejecuta solo cuando el usuario lo pide."""

    def __init__(self) -> None:
        self.result: dict | None = None
        self.running = False
        self.error: str | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self.running:
                return
            self.running = True
        threading.Thread(target=self.run, daemon=True, name="sl-audit").start()

    def run(self) -> None:
        self.running = True
        try:
            self.result = audit.evaluate(collect.collect())
            self.error = None
        except Exception as e:  # noqa: BLE001
            self.error = str(e)
        finally:
            self.running = False

    def detections_for(self, path: str | None) -> list | None:
        if self.result is None:
            return None
        if not path:
            return []
        low = path.lower()
        return [
            {"amenaza": f["que"], "fecha": f["evidencia"]}
            for f in self.result["findings"]
            if f["categoria"] == "Amenazas" and low in (f.get("donde") or "").lower()
        ]

    def autostart_for(self, path: str | None) -> list | None:
        if self.result is None:
            return None
        if not path:
            return []
        low = path.lower()
        out = [{"origen": e["origen"], "nombre": e["nombre"]} for e in self.result["startup"] if (e.get("ejecutable") or "").lower() == low and e.get("habilitado")]
        out += [
            {"origen": f"Tarea programada {t['ruta']}{t['nombre']}", "nombre": t["nombre"]}
            for t in self.result["tasks"]["otras"]
            if any(low == (a.get("exe") or "").strip('"').lower() for a in t["acciones"])
        ]
        return out


def router(engine) -> APIRouter:
    r = APIRouter(prefix="/api/security")
    state: SecurityState = engine.security

    @r.post("/audit")
    def start_audit():
        state.start()
        return {"running": True}

    @r.get("/audit")
    def get_audit():
        return {"running": state.running, "error": state.error, "result": state.result}

    return r
