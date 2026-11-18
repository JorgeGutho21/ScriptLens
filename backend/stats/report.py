"""Informe HTML de estadísticas (autocontenido, sin recursos externos)."""

from __future__ import annotations

import html
import time

from backend.core.config import APP_NAME, APP_VERSION, AUTHOR, AUTHOR_GITHUB, REPOSITORY_URL

PERIODO = {"dia": "Hoy", "semana": "Últimos 7 días", "mes": "Últimos 30 días"}


def _dur(s) -> str:
    if s is None:
        return "—"
    s = int(s)
    d, h, m = s // 86400, s % 86400 // 3600, s % 3600 // 60
    return f"{d} d {h} h" if d else f"{h} h {m} min" if h else f"{m} min"


def _mb(b) -> str:
    return "—" if b is None else f"{b / 1024**2:,.1f} MB".replace(",", " ")


def _t(ts, fmt="%Y-%m-%d %H:%M") -> str:
    return time.strftime(fmt, time.localtime(ts)) if ts else "—"


def render(s: dict, equipo: str) -> str:
    e = html.escape
    t = s["tiempos"]
    step_fmt = "%H:%M" if s["periodo"] == "dia" else "%a %d/%m"
    serie = "".join(
        f"<tr><td>{_t(x['ts'], step_fmt)}</td><td>{x['minutos_registrados']}</td><td>{x['cpu_prom']}</td><td>{x['ram_prom']}</td><td>{_mb(x['red_enviados'] + x['red_recibidos'])}</td><td>{_dur(x['activo_s'])}</td></tr>"
        for x in s["serie"]
    )
    procs = "".join(f"<tr><td>{e(p['name'])}</td><td>{round(p['cpu_prom'] or 0, 1)} %</td><td>{_mb(p['ram_max'])}</td></tr>" for p in s["procesos_cpu"])
    apps = "".join(f"<tr><td>{e(a['app'])}</td><td>{_dur(a['segundos'])}</td></tr>" for a in s["aplicaciones"]) or "<tr><td colspan=2>Seguimiento de aplicaciones desactivado o sin datos.</td></tr>"
    alerts = "".join(f"<li>{_t(a['created_at'])}: {e(a['detail'])}</li>" for a in s["alertas"]) or "<li>Sin alertas de consumo sostenido.</li>"
    days = "".join(f"<tr><td>{_t(d['dia'], '%a %d/%m')}</td><td>{d['cpu_prom'] if d['cpu_prom'] is not None else '—'}</td><td>{d['ram_prom'] if d['ram_prom'] is not None else '—'}</td><td>{_dur(d['activo_s'])}</td><td>{_dur(d['minutos_registrados'] * 60)}</td></tr>" for d in s["comparacion_dias"])
    boots = "".join(f"<li>{_t(b['boot_time'])} ({'inicio' if b['source'] == 'inicio' else 'reanudación' if b['source'] == 'reanudacion' else 'arranque actual'}){' → apagado ' + _t(b['shutdown_time']) if b['shutdown_time'] else ''}</li>" for b in s["arranques"][:20])
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Estadísticas de {e(equipo)}</title>
<style>body{{font:14px/1.5 'Segoe UI',sans-serif;color:#0e1621;max-width:960px;margin:24px auto;padding:0 16px}}header{{background:#0b1220;color:#fff;padding:16px 20px;border-radius:12px}}header small{{color:#b9c4d4}}h2{{color:#1f6feb;font-size:15px;margin-top:24px}}table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #dde3ec;padding:5px 6px;text-align:left}}th{{color:#4b5a70;font-weight:600}}.k{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}}.k div{{border:1px solid #dde3ec;border-radius:10px;padding:10px}}.k b{{display:block;font-size:20px}}footer{{color:#75839a;font-size:12px;margin-top:28px}}</style></head><body>
<header><strong>Estadísticas de mi PC — {e(equipo)}</strong><br><small>{PERIODO[s['periodo']]} · {_t(s['desde'])} a {_t(s['hasta'])} · {APP_NAME} v{APP_VERSION} · Desarrollado por {AUTHOR} ({AUTHOR_GITHUB})</small></header>
<h2>Tiempos (no se mezclan)</h2><div class="k">
<div>Desde el último arranque<b>{_dur(t['desde_ultimo_arranque_s'])}</b><small>Según Windows; puede incluir suspensión.</small></div>
<div>Sesión registrada<b>{_dur(t['sesion_s'])}</b><small>Minutos con sesión abierta mientras ScriptLens medía.</small></div>
<div>Uso activo<b>{_dur(t['activo_s'])}</b><small>Teclado o ratón usados en los últimos 2 min.</small></div>
<div>Tiempo medido<b>{_dur(t['registrado_s'])}</b><small>Cobertura real de las estadísticas.</small></div></div>
<h2>Rendimiento</h2><p>CPU promedio: {s['promedios']['cpu'] if s['promedios']['cpu'] is not None else '—'} % · RAM promedio: {s['promedios']['ram'] if s['promedios']['ram'] is not None else '—'} %</p>
<table><tr><th>Intervalo</th><th>Minutos</th><th>CPU %</th><th>RAM %</th><th>Red</th><th>Uso activo</th></tr>{serie}</table>
<h2>Comparación entre días</h2><table><tr><th>Día</th><th>CPU %</th><th>RAM %</th><th>Uso activo</th><th>Medido</th></tr>{days}</table>
<h2>Procesos con mayor consumo de CPU</h2><table><tr><th>Proceso</th><th>CPU promedio</th><th>RAM máxima</th></tr>{procs}</table>
<h2>Aplicaciones más utilizadas (opcional)</h2><table><tr><th>Aplicación</th><th>Tiempo en primer plano</th></tr>{apps}</table>
<h2>Alertas por consumo sostenido</h2><ul>{alerts}</ul>
<h2>Arranques registrados</h2><ul>{boots or '<li>Sin datos del registro de eventos.</li>'}</ul>
<footer>Datos medidos en este equipo por ScriptLens IA. Las estadísticas solo cubren el tiempo en que ScriptLens estuvo abierto. {REPOSITORY_URL}</footer></body></html>"""
