"""Informe PDF con reportlab: encabezado de marca, pie con autor y marca de agua discreta."""

from __future__ import annotations

import os
import time
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .html_report import ESTADO_ES

ACCENT = colors.HexColor("#1F6FEB")
DARK = colors.HexColor("#0B1220")
MUTED = colors.HexColor("#4B5A70")
LINE = colors.HexColor("#DDE3EC")


def _fonts() -> tuple[str, str]:
    """Segoe UI (incluida en Windows) para tildes y eñes; Helvetica como respaldo."""
    fonts_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    try:
        if "SL-Regular" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("SL-Regular", str(fonts_dir / "segoeui.ttf")))
            pdfmetrics.registerFont(TTFont("SL-Bold", str(fonts_dir / "segoeuib.ttf")))
        return "SL-Regular", "SL-Bold"
    except Exception:  # noqa: BLE001
        return "Helvetica", "Helvetica-Bold"


def render(d: dict, path: Path) -> Path:
    regular, bold = _fonts()
    styles = {
        "h1": ParagraphStyle("h1", fontName=bold, fontSize=17, leading=21, textColor=colors.white),
        "sub": ParagraphStyle("sub", fontName=regular, fontSize=8.5, leading=11, textColor=colors.HexColor("#B9C4D4")),
        "h2": ParagraphStyle("h2", fontName=bold, fontSize=10, leading=13, textColor=ACCENT, spaceBefore=12, spaceAfter=6),
        "p": ParagraphStyle("p", fontName=regular, fontSize=9.5, leading=13.5, textColor=DARK, alignment=TA_LEFT),
        "cell": ParagraphStyle("cell", fontName=regular, fontSize=8.3, leading=10.5, textColor=DARK),
        "head": ParagraphStyle("head", fontName=bold, fontSize=8.3, leading=10.5, textColor=MUTED),
    }
    m, p = d["meta"], d["rendimiento"]

    def P(text, st="p"):
        return Paragraph(str("—" if text is None else text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), styles[st])

    def T(headers, rows, widths):
        data = [[P(h, "head") for h in headers]] + [[P(c, "cell") for c in r] for r in rows]
        t = Table(data, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        return t

    W = A4[0] - 3.6 * cm
    header = Table(
        [[Paragraph(m["titulo"], styles["h1"])], [Paragraph(f"{m['app']} v{m['version']} · Generado el {m['generado']} · Equipo {d['sistema']['equipo']}", styles["sub"])], [Paragraph(f"Desarrollado por {m['autor']} · GitHub: {m['github']} · {m['repositorio']}", styles["sub"])]],
        colWidths=[W],
    )
    header.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), DARK), ("LEFTPADDING", (0, 0), (-1, -1), 14), ("TOPPADDING", (0, 0), (0, 0), 12), ("BOTTOMPADDING", (0, -1), (-1, -1), 12)]))

    story = [header, Spacer(1, 10)]
    story += [P("Resumen del sistema", "h2"), T(["Elemento", "Valor"], [["Sistema operativo", d["sistema"]["so"]], ["Procesador", d["sistema"]["procesador"]], ["Núcleos", d["sistema"]["nucleos"]], ["RAM total", f"{d['sistema']['ram_total_gb']} GB"], ["Tiempo encendido", f"{p['tiempo_encendido_h']} h"]], [5 * cm, W - 5 * cm])]
    story += [
        P(f"Métricas medidas (último minuto: {p['segundos_medidos']} s)", "h2"),
        T(["CPU promedio", "RAM promedio", "RAM en uso", "Procesos"], [[f"{p['cpu_prom_1min_pct']} %", f"{p['ram_prom_1min_pct']} %", f"{p['ram_usada_gb']} / {p['ram_total_gb']} GB", p["procesos"]]], [W / 4] * 4),
        Spacer(1, 6),
    ]
    story += [P(f"• {ESTADO_ES.get(f['estado'], f['estado'])}: {f['titulo']}. {f['evidencia']}") for f in p["hallazgos"]]
    story += [P("Almacenamiento", "h2"), T(["Unidad", "Usado", "Libre", "Total"], [[x["unidad"], f"{x['usado_pct']} %", f"{x['libre_gb']} GB", f"{x['total_gb']} GB"] for x in d["discos"]], [W / 4] * 4)]
    story += [P("Procesos destacados (por memoria)", "h2"), T(["Programa", "Inst.", "RAM (MB)", "CPU 1 min", "Tipo"], [[x["nombre"], x["instancias"], x["ram_mb"], f"{x['cpu_prom_1min_pct']} %", x["tipo"]] for x in d["top_memoria"]], [5.2 * cm, 1.2 * cm, 2 * cm, 2 * cm, W - 10.4 * cm])]
    sec = d.get("seguridad")
    if sec and sec.get("disponible"):
        fw = ", ".join(f"{k}: {'activo' if v else 'desactivado'}" for k, v in sec["firewall"].items())
        story += [
            P("Seguridad", "h2"),
            T(["Elemento", "Estado"], [["Antivirus (Defender)", "Activo" if sec["antivirus_activo"] else "No confirmado"], ["Protección en tiempo real", "Activa" if sec["proteccion_tiempo_real"] else "No confirmada"], ["Definiciones", f"{sec['antiguedad_definiciones_dias']} día(s)"], ["Firewall", fw], ["Amenazas activas (Defender)", sec["amenazas_activas_defender"]]], [6 * cm, W - 6 * cm]),
        ]
        if sec["hallazgos"]:
            story += [Spacer(1, 6), T(["Estado", "Hallazgo", "Qué puede hacer"], [[ESTADO_ES.get(h["estado"], h["estado"]), f"{h['que']} — {h['donde']}", h["que_hacer"]] for h in sec["hallazgos"]], [2.6 * cm, 7.4 * cm, W - 10 * cm])]
    rv = d["procesos_revision"]["procesos"]
    story += [P("Evidencias: procesos con señales", "h2")]
    story += [T(["Proceso", "Estado", "Señales"], [[f"{x['nombre']} (PID {x['pid']})", ESTADO_ES.get(x["estado"], x["estado"]), "; ".join(x["senales"])] for x in rv], [4.5 * cm, 3 * cm, W - 7.5 * cm])] if rv else [P("Ningún proceso en ejecución mostró señales que requieran revisión.")]
    story += [P("Recomendaciones", "h2")] + [P(f"• {r}") for r in d["recomendaciones"]]
    story += [P("Acciones realizadas (últimas 20)", "h2")]
    story += [T(["Fecha", "Acción", "Objetivo", "Resultado"], [[time.strftime("%Y-%m-%d %H:%M", time.localtime(a["created_at"])), a["action"], a["target"], f"{a['result']}: {a['detail']}"] for a in d["acciones"]], [2.8 * cm, 3.2 * cm, 4.5 * cm, W - 10.5 * cm])] if d["acciones"] else [P("No se han realizado acciones desde ScriptLens.")]
    c = d.get("comparacion")
    if c:
        story += [P(f"Comparación: {c['a']['label']} → {c['b']['label']}", "h2")] + [P(f"• {s}") for s in c["summary"]]
    story += [P("Limitaciones del diagnóstico", "h2")] + [P(f"• {x}") for x in d["limitaciones"]]

    def decorate(canvas, doc):
        canvas.saveState()
        # Marca de agua: texto gris muy claro y rotado, detrás del contenido.
        canvas.setFillColor(colors.Color(0.05, 0.08, 0.13, alpha=0.05))
        canvas.setFont(bold, 26)
        canvas.translate(A4[0] / 2, A4[1] / 2)
        canvas.rotate(32)
        for dy in (-260, 0, 260):
            canvas.drawCentredString(0, dy, m["marca_agua"])
        canvas.restoreState()
        canvas.saveState()
        canvas.setFont(regular, 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(1.8 * cm, 1.1 * cm, f"{m['marca_agua']} · {m['repositorio']}")
        canvas.drawRightString(A4[0] - 1.8 * cm, 1.1 * cm, f"Página {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.8 * cm, title=m["titulo"], author=f"{m['autor']} ({m['github']})", subject=m["app"], creator=m["app"])
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    return path
