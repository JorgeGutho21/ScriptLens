"""Rutas del administrador de procesos (solo lectura)."""

from __future__ import annotations

import time

import psutil
from fastapi import APIRouter, HTTPException, Query

from . import analysis
from .winapi import visible_window_pids


def _row(engine, snap, window_pids, mem_total, stats_cache) -> dict:
    path = engine.paths.get(snap.pid, snap.create_time)
    sig = engine.signatures.get(path)
    stats = stats_cache.get((snap.pid, snap.create_time))
    sig_d = sig.to_dict() if sig else None
    sigs = analysis.signals(snap, path, sig_d, stats, mem_total, engine.detections_for(path))
    cat = analysis.category(snap, window_pids)
    row = snap.to_dict()
    row.update(
        {
            "path": path,
            "category": cat,
            "category_label": analysis.CATEGORY_ES[cat],
            "publisher": (sig_d or {}).get("firmante") or (sig_d or {}).get("editor"),
            "description": (sig_d or {}).get("descripcion"),
            "signature": (sig_d or {}).get("estado") if sig_d else ("pendiente" if path else None),
            "estado": analysis.overall(sigs),
            "signals": [s["code"] for s in sigs],
            "cpu_avg_60s": stats["cpu_avg"] if stats else None,
        }
    )
    return row


def router(engine) -> APIRouter:
    r = APIRouter(prefix="/api/processes")

    @r.get("")
    def list_processes():
        ts, snaps = engine.processes.latest()
        windows = visible_window_pids()
        mem_total = engine.sampler.latest().mem_total if engine.sampler.latest() else None
        stats_cache = {(s.pid, s.create_time): engine.processes.stats(s.pid, s.create_time, 60) for s in snaps}
        rows = [_row(engine, s, windows, mem_total, stats_cache) for s in snaps]
        engine.signatures.request(r_["path"] for r_ in rows if r_["path"])
        return {"measured_at": ts, "count": len(rows), "processes": rows}

    @r.get("/{pid}")
    def detail(pid: int, create_time: float | None = Query(None)):
        snap = engine.processes.find(pid)
        if snap is None or (create_time is not None and snap.create_time is not None and abs(snap.create_time - create_time) > 0.01):
            raise HTTPException(404, "El proceso ya no existe (pudo haberse cerrado durante la medición).")
        _, snaps = engine.processes.latest()
        by_pid = {s.pid: s for s in snaps}
        path = engine.paths.get(snap.pid, snap.create_time)
        sig = engine.signatures.verify_now(path) if path else None
        sig_d = sig.to_dict() if sig else None
        stats = engine.processes.stats(snap.pid, snap.create_time, 60)
        mem_total = engine.sampler.latest().mem_total if engine.sampler.latest() else None
        detections = engine.detections_for(path)
        sigs = analysis.signals(snap, path, sig_d, stats, mem_total, detections)

        # Padre válido solo si existía antes que el hijo (Windows reutiliza los PID).
        parent = by_pid.get(snap.ppid or -1)
        if parent and parent.create_time and snap.create_time and parent.create_time > snap.create_time:
            parent = None
        children = [
            {"pid": c.pid, "name": c.name, "create_time": c.create_time}
            for c in snaps
            if c.ppid == snap.pid and c.pid != snap.pid and (not c.create_time or not snap.create_time or c.create_time >= snap.create_time)
        ]

        extra = {"cmdline": None, "user": None, "connections": None, "status": None}
        try:
            p = psutil.Process(pid)
            with p.oneshot():
                try:
                    extra["cmdline"] = analysis.redact(" ".join(p.cmdline()))[:600]
                except psutil.AccessDenied:
                    pass
                try:
                    user = p.username()
                    me = psutil.Process().username()
                    if user == me:
                        extra["user"] = "Su cuenta de usuario"
                    elif user and user.upper().endswith(("SYSTEM", "SISTEMA")):
                        extra["user"] = "Sistema (SYSTEM)"
                    elif user and ("SERVICE" in user.upper() or "SERVICIO" in user.upper()):
                        extra["user"] = "Cuenta de servicio de Windows"
                    else:
                        extra["user"] = "Otra cuenta"  # no se muestra el nombre por privacidad
                except psutil.AccessDenied:
                    extra["user"] = None
                try:
                    extra["status"] = p.status()
                except psutil.Error:
                    pass
            try:
                conns = p.net_connections(kind="inet")
                extra["connections"] = {
                    "total": len(conns),
                    "establecidas": sum(1 for c in conns if c.status == psutil.CONN_ESTABLISHED),
                    "escuchando": sorted({c.laddr.port for c in conns if c.status == psutil.CONN_LISTEN}),
                    "remotas": sorted({f"{c.raddr.ip}:{c.raddr.port}" for c in conns if c.raddr})[:10],
                }
            except (psutil.AccessDenied, OSError):
                extra["connections"] = None
        except psutil.NoSuchProcess:
            raise HTTPException(404, "El proceso terminó mientras se consultaba.")
        except psutil.Error:
            pass

        cat = analysis.category(snap, visible_window_pids())
        allowed, reason = analysis.can_terminate(snap.name, snap.pid, engine.own_pids)
        detail = {
            **snap.to_dict(),
            "measured_at": time.time(),
            "path": path,
            "category": cat,
            "category_label": analysis.CATEGORY_ES[cat],
            "signature": sig_d,
            "stats": stats,
            "parent": {"pid": parent.pid, "name": parent.name, "create_time": parent.create_time} if parent else None,
            "children": children,
            "signals": sigs,
            "estado": analysis.overall(sigs),
            "can_terminate": allowed,
            "terminate_reason": reason,
            "autostart": engine.autostart_for(path),
            "defender_checked": detections is not None,
            **extra,
        }
        detail["explicacion"] = analysis.explain(detail)
        return detail

    return r
