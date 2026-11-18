"""Informes HTML y PDF de la auditoría de 30 controles."""

from __future__ import annotations

import html
import time
from pathlib import Path

from backend.core.config import APP_NAME, APP_VERSION, AUTHOR, AUTHOR_GITHUB, REPOSITORY_URL

COLORS = {"CUMPLE": "#1a7f37", "NO CUMPLE": "#cf222e", "REQUIERE REVISIÓN": "#9a6700", "NO APLICA": "#4b5a70"}


def render_html(res: dict, equipo: str) -> str:
    e = html.escape
    rows = "".join(
        f"<tr><td>{c['numero']:02d}</td><td>{e(c['area'])}</td><td><b>{e(c['nombre'])}</b><br><small>{e(c['proposito'])}</small></td>"
        f"<td style='color:{COLORS[c['estado']]};font-weight:600'>{c['estado']}</td><td><code>{e(c['evidencia'])}</code></td>"
        f"<td>{e(c['explicacion'])}<br><small><b>Recomendación:</b> {e(c['recomendacion'])}</small></td></tr>"
        for c in res["controles"]
    )
    s = res["resumen"]
    pct = res["cumplimiento_concluyente_pct"]
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Auditoría de 30 controles — {e(equipo)}</title>
<style>body{{font:13.5px/1.45 'Segoe UI',sans-serif;color:#0e1621;max-width:1200px;margin:24px auto;padding:0 16px}}header{{background:#0b1220;color:#fff;padding:16px 20px;border-radius:12px}}header small{{color:#b9c4d4}}table{{border-collapse:collapse;width:100%;margin-top:14px}}td,th{{border-bottom:1px solid #dde3ec;padding:6px;vertical-align:top;text-align:left}}th{{color:#4b5a70}}code{{font-size:12px;word-break:break-word;white-space:pre-wrap}}small{{color:#4b5a70}}.k{{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}}.k div{{border:1px solid #dde3ec;border-radius:10px;padding:8px 14px}}footer{{color:#75839a;font-size:12px;margin-top:24px}}</style></head><body>
<header><strong>Auditoría de Windows — 30 controles</strong><br><small>Equipo {e(equipo)} · {e(res['sistema'])} · {time.strftime('%Y-%m-%d %H:%M', time.localtime(res['medido_en']))} · {'con' if res['administrador'] else 'sin'} permisos de administrador · {APP_NAME} v{APP_VERSION} · Desarrollado por {AUTHOR} ({AUTHOR_GITHUB})</small></header>
<div class="k"><div>Cumple: <b>{s['CUMPLE']}</b></div><div>No cumple: <b>{s['NO CUMPLE']}</b></div><div>Requiere revisión: <b>{s['REQUIERE REVISIÓN']}</b></div><div>No aplica: <b>{s['NO APLICA']}</b></div><div>Cumplimiento entre controles concluyentes: <b>{pct if pct is not None else '—'} %</b></div></div>
<p><small>{e(res['nota'])} La auditoría es de solo lectura: no modificó ninguna configuración.</small></p>
<table><tr><th>N.º</th><th>Área</th><th>Control y propósito</th><th>Resultado</th><th>Evidencia técnica</th><th>Explicación</th></tr>{rows}</table>
<footer>Basado en el material del taller «Auditoría de Windows 10 — 30 controles». {REPOSITORY_URL}</footer></body></html>"""


def render_pdf(res: dict, equipo: str, path: Path) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    from backend.reports.pdf_report import _fonts

    regular, bold = _fonts()
    st = {
        "h1": ParagraphStyle("h1", fontName=bold, fontSize=15, leading=19, textColor=colors.white),
        "sub": ParagraphStyle("sub", fontName=regular, fontSize=8, leading=10.5, textColor=colors.HexColor("#B9C4D4")),
        "p": ParagraphStyle("p", fontName=regular, fontSize=8.5, leading=11),
        "c": ParagraphStyle("c", fontName=regular, fontSize=7.4, leading=9.4),
        "h": ParagraphStyle("h", fontName=bold, fontSize=7.6, leading=9.4, textColor=colors.HexColor("#4B5A70")),
    }

    def P(t, s="c", color=None):
        txt = html.escape(str(t))
        return Paragraph(f"<font color='{color}'>{txt}</font>" if color else txt, st[s])

    W = landscape(A4)[0] - 3 * cm
    head = Table([[Paragraph("Auditoría de Windows — 30 controles", st["h1"])], [Paragraph(html.escape(f"Equipo {equipo} · {res['sistema']} · {time.strftime('%Y-%m-%d %H:%M', time.localtime(res['medido_en']))} · {'con' if res['administrador'] else 'sin'} permisos de administrador"), st["sub"])], [Paragraph(f"{APP_NAME} v{APP_VERSION} · Desarrollado por {AUTHOR} · GitHub: {AUTHOR_GITHUB}", st["sub"])]], colWidths=[W])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0B1220")), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (0, 0), 10), ("BOTTOMPADDING", (0, -1), (-1, -1), 10)]))
    s = res["resumen"]
    pct = res["cumplimiento_concluyente_pct"]
    summary = P(f"Cumple: {s['CUMPLE']} · No cumple: {s['NO CUMPLE']} · Requiere revisión: {s['REQUIERE REVISIÓN']} · No aplica: {s['NO APLICA']} · Cumplimiento entre controles concluyentes: {pct if pct is not None else '—'} %. {res['nota']} Auditoría de solo lectura.", "p")
    data = [[P(h, "h") for h in ("N.º", "Área", "Control", "Resultado", "Evidencia técnica", "Explicación y recomendación")]]
    for c in res["controles"]:
        data.append([P(f"{c['numero']:02d}"), P(c["area"]), P(c["nombre"]), P(c["estado"], color=COLORS[c["estado"]]), P(c["evidencia"]), P(f"{c['explicacion']} Recomendación: {c['recomendacion']}")])
    t = Table(data, colWidths=[1 * cm, 2.1 * cm, 5 * cm, 2.6 * cm, 7.6 * cm, W - 18.3 * cm], repeatRows=1)
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDE3EC")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))

    def foot(canvas, doc):
        canvas.saveState()
        canvas.setFont(regular, 7)
        canvas.drawString(1.5 * cm, 0.9 * cm, f"ScriptLens IA · {REPOSITORY_URL}")
        canvas.drawRightString(landscape(A4)[0] - 1.5 * cm, 0.9 * cm, f"Página {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4), leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.3 * cm, bottomMargin=1.5 * cm, title="Auditoría de 30 controles", author=f"{AUTHOR} ({AUTHOR_GITHUB})", creator=APP_NAME)
    doc.build([head, Spacer(1, 8), summary, Spacer(1, 8), t], onFirstPage=foot, onLaterPages=foot)
    return path
