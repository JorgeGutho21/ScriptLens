"""Registro y consulta de estadísticas.

Origen de los datos (sin muestreos adicionales):
- Rendimiento: el ``SystemSampler`` existente (1 muestra/s) se resume cada minuto en
  ``stats_minute`` y cada hora en ``stats_hour``.
- Procesos: el ``ProcessMonitor`` existente; se guardan los 15 de mayor CPU y RAM por minuto,
  acumulados por hora en ``stats_proc_hour``.
- Actividad: cada 10 s se consulta el contador de inactividad de Windows (sin contenido).
- Aplicaciones en primer plano: solo con consentimiento explícito (``app_tracking_enabled``).
- Arranques y apagados: registro de eventos de Windows (Kernel-General 12/13, Power-Troubleshooter 1).

Tres tiempos que NO se mezclan:
- **Desde el último arranque**: lo que informa Windows; con suspensión o Inicio rápido puede
  abarcar varios días.
- **Sesión registrada**: minutos con una sesión de usuario abierta mientras ScriptLens medía.
- **Uso activo**: segundos con teclado o ratón usados en los últimos 2 minutos.

Retención: el detalle por minuto se conserva 7 días; horas, procesos, aplicaciones y alertas,
los días configurados (90 por defecto).
"""

from __future__ import annotations

import csv
import io
import threading
import time
from collections import defaultdict

from . import activity

TICK = 10.0
ACTIVE_IDLE_LIMIT = 120.0
MINUTE_RETENTION_DAYS = 7
SUSTAINED_MINUTES = 5
ALERT_COOLDOWN = 1800
TOP_PROCS = 15
SESSION_GAP = 300

BOOT_EVENTS_PS = r"""
$since=(Get-Date).AddDays(-60)
$ev=@(Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Microsoft-Windows-Kernel-General';Id=12,13;StartTime=$since} -ErrorAction SilentlyContinue)
$ev+=@(Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Microsoft-Windows-Power-Troubleshooter';Id=1;StartTime=$since} -ErrorAction SilentlyContinue)
@($ev | ForEach-Object { [pscustomobject]@{id=$_.Id; p=$_.ProviderName; t=([DateTimeOffset]$_.TimeCreated).ToUnixTimeSeconds()} }) | ConvertTo-Json -Compress
"""


def _minute(ts: float) -> int:
    return int(ts // 60 * 60)


def _hour(ts: float) -> int:
    return int(ts // 3600 * 3600)


def _day_start(ts: float) -> int:
    lt = time.localtime(ts)
    return int(time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1)))


def _avg(values):
    v = [x for x in values if x is not None]
    return round(sum(v) / len(v), 2) if v else None


class StatsService:
    def __init__(self, engine, clock=time.time, idle=activity.idle_seconds, foreground=activity.foreground_app, session=activity.user_session_open):
        self.engine = engine
        self.db = engine.db
        self.clock, self.idle, self.foreground, self.session = clock, idle, foreground, session
        self._active: dict[int, float] = defaultdict(float)
        self._apps: dict[tuple[int, str], float] = defaultdict(float)
        self._last_minute: int | None = None
        self._last_cleanup = 0.0
        self._events_loaded = 0.0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    # --- Ajustes ------------------------------------------------------------
    def settings(self) -> dict:
        s = self.db.settings()
        return {"activadas": bool(s["stats_enabled"]), "retencion_dias": int(s["stats_retention_days"]), "aplicaciones": bool(s["app_tracking_enabled"])}

    def set_settings(self, activadas: bool, retencion_dias: int, aplicaciones: bool) -> dict:
        self.db.set_setting("stats_enabled", bool(activadas))
        self.db.set_setting("stats_retention_days", int(retencion_dias))
        self.db.set_setting("app_tracking_enabled", bool(aplicaciones))
        return self.settings()

    def delete(self, what: str) -> dict:
        tables = {"aplicaciones": ["app_usage"], "alertas": ["stats_alerts"], "todo": ["stats_minute", "stats_hour", "stats_proc_hour", "app_usage", "stats_alerts", "boots"]}[what]
        n = sum(self.db.execute(f"DELETE FROM {t}").rowcount for t in tables)
        with self._lock:
            if what in ("aplicaciones", "todo"):
                self._apps.clear()
            if what == "todo":
                self._active.clear()
        return {"borrados": n, "que": what}

    # --- Registro -------------------------------------------------------------
    def start(self) -> None:
        self.db.execute("INSERT OR IGNORE INTO boots(boot_time, source) VALUES (?, 'arranque_actual')", (int(self.engine.info()["boot_time"]),))
        self._thread = threading.Thread(target=self._loop, daemon=True, name="sl-stats")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.wait(TICK):
            try:
                self.tick()
            except Exception:  # noqa: BLE001 — las estadísticas nunca deben afectar al monitoreo
                pass

    def tick(self) -> None:
        now = self.clock()
        st = self.settings()
        minute = _minute(now)
        if st["activadas"]:
            idle = self.idle()
            active = idle is not None and idle < ACTIVE_IDLE_LIMIT
            with self._lock:
                if active:
                    self._active[minute] += TICK
                    if st["aplicaciones"]:
                        app = self.foreground()
                        if app:
                            self._apps[(_hour(now), app[:80])] += TICK
        if self._last_minute is None:
            self._last_minute = minute
        elif minute > self._last_minute:
            if st["activadas"]:
                for m in range(self._last_minute, minute, 60):
                    self.record_minute(m)
                self.flush_apps()
            self._last_minute = minute
        if now - self._last_cleanup > 3600:
            self.cleanup(now)

    def record_minute(self, m: int, samples=None, session_open: bool | None = None) -> bool:
        if samples is None:
            samples = [s for s in self.engine.sampler.history(240) if m <= s.ts < m + 60]
        with self._lock:
            active = min(60.0, self._active.pop(m, 0.0))
        if not samples:
            return False
        session_open = self.session() if session_open is None else session_open
        cpu = [s.cpu_percent for s in samples]
        ram = [s.mem_percent for s in samples]
        self.db.execute(
            "INSERT OR REPLACE INTO stats_minute(ts, samples, cpu_avg, cpu_max, ram_avg, ram_max, disk_read, disk_write, net_sent, net_recv, active_seconds, session_user) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                m,
                len(samples),
                _avg(cpu),
                max(cpu),
                _avg(ram),
                max(ram),
                _avg(s.disk_read_bps for s in samples),
                _avg(s.disk_write_bps for s in samples),
                _avg(s.net_sent_bps for s in samples),
                _avg(s.net_recv_bps for s in samples),
                active,
                1 if session_open else 0,
            ),
        )
        self._record_processes(_hour(m))
        self._rollup(_hour(m))
        self._alerts(m)
        return True

    def _record_processes(self, hour: int) -> None:
        procs = getattr(self.engine, "processes", None)
        if procs is None:
            return
        _, snaps = procs.latest()
        cpu: dict[str, float] = defaultdict(float)
        ram: dict[str, int] = defaultdict(int)
        for row in procs.sustained(60, 200):
            cpu[row["name"]] += row["cpu_avg"]
        for s in snaps:
            if s.pid and s.name:
                ram[s.name] += s.memory_rss or 0
        names = set(sorted(cpu, key=cpu.get, reverse=True)[:TOP_PROCS]) | set(sorted(ram, key=ram.get, reverse=True)[:TOP_PROCS])
        for n in names:
            self.db.execute(
                "INSERT INTO stats_proc_hour(ts, name, cpu_avg, ram_max, minutes) VALUES (?,?,?,?,1) "
                "ON CONFLICT(ts, name) DO UPDATE SET cpu_avg = (cpu_avg * minutes + excluded.cpu_avg) / (minutes + 1), ram_max = MAX(ram_max, excluded.ram_max), minutes = minutes + 1",
                (hour, n[:80], round(cpu.get(n, 0.0), 2), int(ram.get(n, 0))),
            )

    def _rollup(self, hour: int) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO stats_hour(ts, minutes, cpu_avg, cpu_max, ram_avg, ram_max, disk_read, disk_write, net_sent, net_recv, active_seconds) "
            "SELECT ?, COUNT(*), AVG(cpu_avg), MAX(cpu_max), AVG(ram_avg), MAX(ram_max), AVG(disk_read), AVG(disk_write), AVG(net_sent), AVG(net_recv), SUM(active_seconds) "
            "FROM stats_minute WHERE ts >= ? AND ts < ?",
            (hour, hour, hour + 3600),
        )

    def _alerts(self, m: int) -> None:
        rows = self.db.query("SELECT ts, cpu_avg, ram_avg FROM stats_minute WHERE ts > ? AND ts <= ? ORDER BY ts", (m - SUSTAINED_MINUTES * 60, m))
        if len(rows) < SUSTAINED_MINUTES or rows[0]["ts"] != m - (SUSTAINED_MINUTES - 1) * 60:
            return  # se exigen minutos consecutivos, sin huecos
        for kind, field, limit, text in (("cpu_sostenida", "cpu_avg", 85, "CPU por encima del {limit} % durante {n} minutos seguidos (promedio {v} %)"), ("ram_sostenida", "ram_avg", 90, "RAM por encima del {limit} % durante {n} minutos seguidos (promedio {v} %)")):
            vals = [r[field] for r in rows]
            if all(v is not None and v >= limit for v in vals):
                recent = self.db.query("SELECT 1 FROM stats_alerts WHERE kind = ? AND created_at > ?", (kind, m - ALERT_COOLDOWN))
                if not recent:
                    v = round(sum(vals) / len(vals), 1)
                    self.db.execute("INSERT INTO stats_alerts(created_at, kind, detail, value, minutes) VALUES (?,?,?,?,?)", (m + 60, kind, text.format(limit=limit, n=SUSTAINED_MINUTES, v=v), v, SUSTAINED_MINUTES))

    def flush_apps(self) -> None:
        with self._lock:
            items, self._apps = list(self._apps.items()), defaultdict(float)
        for (h, app), secs in items:
            self.db.execute("INSERT INTO app_usage(ts, app, seconds) VALUES (?,?,?) ON CONFLICT(ts, app) DO UPDATE SET seconds = seconds + excluded.seconds", (h, app, secs))

    def cleanup(self, now: float) -> None:
        self._last_cleanup = now
        days = self.settings()["retencion_dias"]
        self.db.execute("DELETE FROM stats_minute WHERE ts < ?", (now - MINUTE_RETENTION_DAYS * 86400,))
        for table, col in (("stats_hour", "ts"), ("stats_proc_hour", "ts"), ("app_usage", "ts"), ("stats_alerts", "created_at"), ("boots", "boot_time")):
            self.db.execute(f"DELETE FROM {table} WHERE {col} < ?", (now - days * 86400,))

    # --- Arranques desde el registro de eventos ------------------------------------
    def load_boot_events(self, force: bool = False) -> int:
        if not force and self.clock() - self._events_loaded < 3600:
            return 0
        self._events_loaded = self.clock()
        from backend.core.winps import PowerShellError, run_ps

        try:
            events = run_ps(BOOT_EVENTS_PS, timeout=30) or []
        except PowerShellError:
            return 0
        if isinstance(events, dict):
            events = [events]
        events.sort(key=lambda e: e["t"])
        added = 0
        start = None
        for e in events:
            if e["id"] == 12 and "Kernel-General" in e["p"]:
                start = e["t"]
                added += self.db.execute("INSERT OR IGNORE INTO boots(boot_time, source) VALUES (?, 'inicio')", (e["t"],)).rowcount
            elif e["id"] == 1:
                added += self.db.execute("INSERT OR IGNORE INTO boots(boot_time, source) VALUES (?, 'reanudacion')", (e["t"],)).rowcount
            elif e["id"] == 13 and start is not None:
                self.db.execute("UPDATE boots SET shutdown_time = ? WHERE boot_time = ?", (e["t"], start))
                start = None
        return added

    # --- Consultas --------------------------------------------------------------
    def _range(self, period: str, now: float) -> tuple[int, int, int]:
        """(inicio, fin, tamaño del intervalo de la serie)."""
        today = _day_start(now)
        if period == "dia":
            return today, today + 86400, 3600
        days = {"semana": 7, "mes": 30}[period]
        return today - (days - 1) * 86400, today + 86400, 86400

    def summary(self, period: str = "dia") -> dict:
        now = self.clock()
        start, end, step = self._range(period, now)
        hours = self.db.query("SELECT * FROM stats_hour WHERE ts >= ? AND ts < ? ORDER BY ts", (start, end))
        minutes = self.db.query("SELECT ts, cpu_avg, ram_avg, active_seconds, session_user FROM stats_minute WHERE ts >= ? AND ts < ? ORDER BY ts", (start, end))

        # Serie: por hora (día) o por día (semana/mes). Los días se agrupan en hora local.
        buckets: dict[int, list[dict]] = defaultdict(list)
        for h in hours:
            key = h["ts"] // 3600 * 3600 if step == 3600 else _day_start(h["ts"])
            buckets[key].append(h)
        serie = []
        for key in sorted(buckets):
            hs = buckets[key]
            mins = sum(x["minutes"] for x in hs)
            w = lambda f: round(sum((x[f] or 0) * x["minutes"] for x in hs) / mins, 2) if mins else None  # noqa: E731 — promedio ponderado por minutos
            serie.append(
                {
                    "ts": key,
                    "minutos_registrados": mins,
                    "cpu_prom": w("cpu_avg"),
                    "cpu_max": max((x["cpu_max"] or 0) for x in hs),
                    "ram_prom": w("ram_avg"),
                    "ram_max": max((x["ram_max"] or 0) for x in hs),
                    "red_enviados": round(sum((x["net_sent"] or 0) * 60 * x["minutes"] for x in hs)),
                    "red_recibidos": round(sum((x["net_recv"] or 0) * 60 * x["minutes"] for x in hs)),
                    "disco_leidos": round(sum((x["disk_read"] or 0) * 60 * x["minutes"] for x in hs)),
                    "disco_escritos": round(sum((x["disk_write"] or 0) * 60 * x["minutes"] for x in hs)),
                    "activo_s": round(sum(x["active_seconds"] or 0 for x in hs)),
                }
            )

        registrado = sum(x["minutos_registrados"] for x in serie) * 60
        activo = sum(x["activo_s"] for x in serie)
        # El detalle por minuto dura 7 días: en «mes» la sesión solo cubre la última semana.
        sesion = sum(60 for m in minutes if m["session_user"])

        # Sesiones de uso: tramos de minutos activos separados por menos de 5 minutos.
        sessions, cur = [], None
        for m in minutes:
            if (m["active_seconds"] or 0) <= 0:
                continue
            if cur and m["ts"] - cur["fin"] <= SESSION_GAP:
                cur["fin"] = m["ts"] + 60
                cur["activo_s"] += m["active_seconds"]
            else:
                cur = {"inicio": m["ts"], "fin": m["ts"] + 60, "activo_s": m["active_seconds"]}
                sessions.append(cur)

        # Horario de actividad: segundos activos por hora del día (y por día de la semana).
        horario = [[0] * 24 for _ in range(7)]
        for h in hours:
            lt = time.localtime(h["ts"])
            horario[lt.tm_wday][lt.tm_hour] += round(h["active_seconds"] or 0)

        procs = self.db.query(
            "SELECT name, SUM(cpu_avg * minutes) / SUM(minutes) AS cpu_prom, MAX(ram_max) AS ram_max, SUM(minutes) AS minutos FROM stats_proc_hour WHERE ts >= ? AND ts < ? GROUP BY name",
            (start, end),
        )
        apps = self.db.query("SELECT app, SUM(seconds) AS segundos FROM app_usage WHERE ts >= ? AND ts < ? GROUP BY app ORDER BY segundos DESC LIMIT 12", (start, end))
        alerts = self.db.query("SELECT created_at, kind, detail, value, minutes FROM stats_alerts WHERE created_at >= ? ORDER BY created_at DESC LIMIT 30", (start,))
        boots = self.db.query("SELECT boot_time, source, shutdown_time FROM boots WHERE boot_time >= ? ORDER BY boot_time DESC LIMIT 60", (start - 86400 * 2,))
        info = self.engine.info()
        return {
            "periodo": period,
            "desde": start,
            "hasta": min(end, now),
            "ajustes": self.settings(),
            "tiempos": {
                "desde_ultimo_arranque_s": round(now - info["boot_time"]),
                "ultimo_arranque": info["boot_time"],
                "registrado_s": registrado,
                "sesion_s": sesion,
                "activo_s": activo,
                "inactivo_s": max(0, (sesion or 0) - activo),
            },
            "promedios": {"cpu": _avg(x["cpu_prom"] for x in serie), "ram": _avg(x["ram_prom"] for x in serie)},
            "serie": serie,
            "sesiones": sessions[-20:],
            "horario": horario,
            "procesos_cpu": sorted(procs, key=lambda p: p["cpu_prom"] or 0, reverse=True)[:10],
            "procesos_ram": sorted(procs, key=lambda p: p["ram_max"] or 0, reverse=True)[:10],
            "aplicaciones": apps,
            "alertas": alerts,
            "arranques": boots,
            "comparacion_dias": self.compare_days(now),
        }

    def compare_days(self, now: float, days: int = 7) -> list[dict]:
        today = _day_start(now)
        out = []
        for i in range(days):
            d0 = today - i * 86400
            r = self.db.query(
                "SELECT SUM(minutes) AS mins, SUM(cpu_avg * minutes) AS cpu_w, SUM(ram_avg * minutes) AS ram_w, SUM(active_seconds) AS activo, SUM(net_recv * 60 * minutes) AS rx, SUM(net_sent * 60 * minutes) AS tx FROM stats_hour WHERE ts >= ? AND ts < ?",
                (d0, d0 + 86400),
            )[0]
            mins = r["mins"] or 0
            out.append(
                {
                    "dia": d0,
                    "minutos_registrados": mins,
                    "cpu_prom": round(r["cpu_w"] / mins, 1) if mins else None,
                    "ram_prom": round(r["ram_w"] / mins, 1) if mins else None,
                    "activo_s": round(r["activo"] or 0),
                    "red_bytes": round((r["rx"] or 0) + (r["tx"] or 0)),
                }
            )
        return out

    def remote_summary(self, period: str = "dia") -> dict:
        s = self.summary(period)
        first = min((b["boot_time"] for b in s["arranques"] if b["boot_time"] >= s["desde"] and b["source"] == "inicio"), default=None)
        return {
            "disponible": True,
            "encendido_s": s["tiempos"]["desde_ultimo_arranque_s"],
            "activo_s": s["tiempos"]["activo_s"],
            "registrado_s": s["tiempos"]["registrado_s"],
            "cpu_prom": s["promedios"]["cpu"],
            "ram_prom": s["promedios"]["ram"],
            "primer_arranque": first,
        }

    def export_csv(self, period: str) -> str:
        s = self.summary(period)
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=";")
        w.writerow(["inicio_intervalo", "minutos_registrados", "cpu_prom_%", "cpu_max_%", "ram_prom_%", "ram_max_%", "red_enviados_bytes", "red_recibidos_bytes", "disco_leidos_bytes", "disco_escritos_bytes", "uso_activo_s"])
        for x in s["serie"]:
            w.writerow([time.strftime("%Y-%m-%d %H:%M", time.localtime(x["ts"])), x["minutos_registrados"], x["cpu_prom"], x["cpu_max"], x["ram_prom"], x["ram_max"], x["red_enviados"], x["red_recibidos"], x["disco_leidos"], x["disco_escritos"], x["activo_s"]])
        return buf.getvalue()
