"""Informe HTML autocontenido con la identidad visual de ScriptLens IA."""

from __future__ import annotations

import html
import time

ESTADO_ES = {
    "normal": "Normal",
    "informativo": "Informativo",
    "consumo_elevado": "Consumo elevado",
    "requiere_revision": "Requiere revisión",
    "actividad_sospechosa": "Actividad sospechosa",
    "amenaza_detectada": "Amenaza detectada",
    "info_insuficiente": "Información insuficiente",
}

LOGO_SVG = """<svg width="44" height="44" viewBox="0 0 64 64" fill="none" aria-hidden="true"><rect width="64" height="64" rx="15" fill="#0B1220"/><circle cx="28" cy="28" r="15" stroke="#3B8CFF" stroke-width="5"/><path d="M39.5 39.5 L51 51" stroke="#3B8CFF" stroke-width="6.5" stroke-linecap="round"/><path d="M24 22 L19 28 L24 34 M32 22 L37 28 L32 34" stroke="#E8EEF7" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>"""


def e(v) -> str:
    return html.escape("—" if v is None else str(v))


def table(headers: list[str], rows: list[list]) -> str:
    th = "".join(f"<th>{e(h)}</th>" for h in headers)
    tr = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>"


def render(d: dict) -> str:
    m, p = d["meta"], d["rendimiento"]
    wm = e(m["marca_agua"])
    sec = d.get("seguridad")
    parts = [
        f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="author" content="{e(m['autor'])} ({e(m['github'])})"><title>{e(m['titulo'])} · {e(m['app'])}</title>
<style>
:root{{--accent:#1f6feb;--text:#0e1621;--muted:#4b5a70;--line:#dde3ec;--bg:#f3f5f9}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 'Segoe UI',system-ui,sans-serif}}
.page{{max-width:980px;margin:0 auto;padding:32px 24px;position:relative;z-index:1}}
.wm{{position:fixed;inset:0;pointer-events:none;z-index:0;display:flex;flex-wrap:wrap;align-content:space-around;justify-content:space-around;transform:rotate(-24deg) scale(1.4);opacity:.045;font-size:22px;font-weight:600;color:#0b1220;user-select:none}}
header{{display:flex;gap:16px;align-items:center;padding:20px 24px;background:#0b1220;color:#e8eef7;border-radius:16px}}
header h1{{margin:0;font-size:22px}} header .sub{{color:#93a1b5;font-size:13px}}
section{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-top:18px}}
h2{{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0 0 12px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}} .kpi{{border:1px solid var(--line);border-radius:12px;padding:12px}}
.kpi b{{display:block;font-size:24px}} .kpi span{{color:var(--muted);font-size:12px}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}} th,td{{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}} th{{color:var(--muted);font-weight:600;font-size:12px}}
.pill{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;background:#eef3fb;color:var(--accent)}}
.pill.rev{{background:#fff4e0;color:#9a6700}} .pill.amz{{background:#ffe7e9;color:#cf222e}}
ul{{margin:0;padding-left:20px}} li{{margin:4px 0}}
footer{{margin:24px 0 8px;color:var(--muted);font-size:12px;text-align:center}}
@media print{{body{{background:#fff}} section{{break-inside:avoid}}}}
@media (max-width:700px){{.kpis{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body>
<div class="wm" aria-hidden="true">{''.join(f'<span>{wm}</span>' for _ in range(24))}</div>
<div class="page">
<header>{LOGO_SVG}<div><h1>{e(m['titulo'])}</h1><div class="sub">{e(m['app'])} v{e(m['version'])} · Generado el {e(m['generado'])} · Equipo {e(d['sistema']['equipo'])}</div>
<div class="sub">Desarrollado por {e(m['autor'])} · GitHub: {e(m['github'])} · {e(m['repositorio'])}</div></div></header>""",
        "<section><h2>Resumen del sistema</h2>"
        + table(["Elemento", "Valor"], [["Sistema operativo", d["sistema"]["so"]], ["Procesador", d["sistema"]["procesador"]], ["Núcleos", d["sistema"]["nucleos"]], ["Memoria RAM total", f"{d['sistema']['ram_total_gb']} GB"], ["Tiempo encendido", f"{p['tiempo_encendido_h']} h"]])
        + "</section>",
        f"""<section><h2>Métricas medidas (último minuto: {e(p['segundos_medidos'])} s)</h2><div class="kpis">
<div class="kpi"><b>{e(p['cpu_prom_1min_pct'])} %</b><span>CPU promedio</span></div>
<div class="kpi"><b>{e(p['ram_prom_1min_pct'])} %</b><span>RAM promedio</span></div>
<div class="kpi"><b>{e(p['ram_usada_gb'])} / {e(p['ram_total_gb'])} GB</b><span>RAM en uso</span></div>
<div class="kpi"><b>{e(p['procesos'])}</b><span>Procesos activos</span></div></div>
<h2 style="margin-top:16px">Diagnóstico</h2><ul>{''.join(f'<li><span class="pill">{e(ESTADO_ES.get(f["estado"], f["estado"]))}</span> {e(f["titulo"])}. <small>{e(f["evidencia"])}</small></li>' for f in p['hallazgos'])}</ul>
<h2 style="margin-top:16px">Almacenamiento</h2>{table(['Unidad', 'Usado', 'Libre', 'Total'], [[x['unidad'], f"{x['usado_pct']} %", f"{x['libre_gb']} GB", f"{x['total_gb']} GB"] for x in d['discos']])}</section>""",
        "<section><h2>Procesos destacados</h2>"
        + table(["Programa (por memoria)", "Instancias", "RAM (MB)", "CPU 1 min (%)", "Tipo"], [[x["nombre"], x["instancias"], x["ram_mb"], x["cpu_prom_1min_pct"], x["tipo"]] for x in d["top_memoria"]])
        + "<br>"
        + table(["Programa (por CPU)", "Instancias", "CPU 1 min (%)", "RAM (MB)"], [[x["nombre"], x["instancias"], x["cpu_prom_1min_pct"], x["ram_mb"]] for x in d["top_cpu"][:6]])
        + "</section>",
    ]
    if sec and sec.get("disponible"):
        fw = ", ".join(f"{k}: {'activo' if v else 'desactivado'}" for k, v in sec["firewall"].items())
        rows = [[ESTADO_ES.get(h["estado"], h["estado"]), h["que"], h["donde"], h["que_hacer"]] for h in sec["hallazgos"]]
        parts.append(
            "<section><h2>Hallazgos de seguridad</h2>"
            + table(["Elemento", "Estado"], [["Antivirus (Defender)", "Activo" if sec["antivirus_activo"] else "No confirmado"], ["Protección en tiempo real", "Activa" if sec["proteccion_tiempo_real"] else "No confirmada"], ["Antigüedad de definiciones", f"{sec['antiguedad_definiciones_dias']} día(s)"], ["Firewall", fw], ["Amenazas activas registradas por Defender", sec["amenazas_activas_defender"]], ["Auditoría realizada", sec["medido"]]])
            + ("<br>" + table(["Estado", "Qué se encontró", "Dónde", "Qué puede hacer"], rows) if rows else "<p>No se encontraron aspectos que requieran revisión.</p>")
            + "</section>"
        )
    rv = d["procesos_revision"]["procesos"]
    parts.append("<section><h2>Evidencias: procesos con señales</h2>" + (table(["Proceso", "PID", "Estado", "Señales", "Ruta"], [[x["nombre"], x["pid"], ESTADO_ES.get(x["estado"], x["estado"]), "; ".join(x["senales"]), x["ruta"]] for x in rv]) if rv else "<p>Ningún proceso en ejecución mostró señales que requieran revisión.</p>") + "</section>")
    parts.append("<section><h2>Recomendaciones</h2><ul>" + "".join(f"<li>{e(r)}</li>" for r in d["recomendaciones"]) + "</ul></section>")
    acts = d["acciones"]
    parts.append(
        "<section><h2>Acciones realizadas (últimas 20)</h2>"
        + (table(["Fecha", "Acción", "Objetivo", "Resultado", "Detalle"], [[time.strftime("%Y-%m-%d %H:%M", time.localtime(a["created_at"])), a["action"], a["target"], a["result"], a["detail"]] for a in acts]) if acts else "<p>No se han realizado acciones desde ScriptLens.</p>")
        + "</section>"
    )
    c = d.get("comparacion")
    if c:
        parts.append(
            f"<section><h2>Comparación: {e(c['a']['label'])} → {e(c['b']['label'])}</h2><ul>"
            + "".join(f"<li>{e(s)}</li>" for s in c["summary"])
            + "</ul></section>"
        )
    parts.append("<section><h2>Limitaciones del diagnóstico</h2><ul>" + "".join(f"<li>{e(x)}</li>" for x in d["limitaciones"]) + "</ul></section>")
    parts.append(f"<footer>{wm} · Informe generado localmente; no contiene datos enviados a Internet.</footer></div></body></html>")
    return "\n".join(parts)
