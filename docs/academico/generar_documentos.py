"""Genera los documentos académicos de ScriptLens IA en formato APA 7 (DOCX).

Uso (PowerShell, raíz del repositorio):
    .\\.venv\\Scripts\\python docs\\academico\\generar_documentos.py
    powershell -ExecutionPolicy Bypass -File docs\\academico\\exportar_pdf.ps1

Fuentes en docs/academico/fuentes/*.md con un Markdown reducido:
  # / ## / ### / ####       encabezados APA de nivel 1 a 4
  párrafos                  texto normal (sangría de primera línea)
  - elemento / 1. elemento  listas
  Tabla: Título             seguido de una tabla con barras | a | b |
  Figura: ruta | Título | Nota opcional
  ```                       bloque de código
  [[TOC]]                   índice de contenido
  [[SALTO]]                 salto de página
  [[REFERENCIAS]]           a partir de aquí, entradas con sangría francesa
  **negrita**, *cursiva*, `código`
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
FUENTES = Path(__file__).parent / "fuentes"
FONT = "Times New Roman"
BLACK = RGBColor(0, 0, 0)

DOCUMENTOS = [
    {
        "fuente": "tecnica.md",
        "salida": ROOT / "docs" / "desarrollo" / "Documentacion_Tecnica_ScriptLens_IA.docx",
        "titulo": "ScriptLens IA: Sistema Inteligente de Diagnóstico, Seguridad, Auditoría y Optimización del Sistema Operativo Windows",
        "subtitulo": "Documentación técnica completa",
        "interlineado": 2.0,
    },
    {
        "fuente": "expo.md",
        "salida": ROOT / "docs" / "expo_software" / "ExpoSoftware_2026_II_ScriptLens_IA.docx",
        "titulo": "ScriptLens IA: Diagnóstico Explicable de Windows con Análisis Estático de Scripts, Aprendizaje Supervisado e Inteligencia Artificial Local Verificada",
        "subtitulo": "Informe para ExpoSoftware 2026-II",
        "interlineado": 2.0,
    },
    {
        "fuente": "manual.md",
        "salida": ROOT / "docs" / "manual_usuario" / "Manual_Usuario_ScriptLens_IA.docx",
        "titulo": "Manual de Usuario de ScriptLens IA",
        "subtitulo": "Guía paso a paso para personas sin conocimientos técnicos",
        "interlineado": 1.5,
    },
]

PORTADA = [
    "Jorge Gutiérrez",
    "Programa de Ingeniería de Sistemas, Universidad Popular del Cesar",
    "Sistemas Operativos · ExpoSoftware 2026-II",
    "Docente: Oswaldo Rueda Carreño",
    "Valledupar, Cesar, 15 de noviembre de 2026",
]


def _font(run, size=12, bold=None, italic=None, mono=False):
    run.font.name = "Consolas" if mono else FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), run.font.name)
    run.font.size = Pt(size)
    run.font.color.rgb = BLACK
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def add_inline(p, text, size=12, base_bold=False, base_italic=False):
    """Añade texto con **negrita**, *cursiva* y `código`."""
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("**"):
            _font(p.add_run(part[2:-2]), size, True, base_italic)
        elif part.startswith("`"):
            _font(p.add_run(part[1:-1]), size - 1.5, base_bold, base_italic, mono=True)
        elif part.startswith("*"):
            _font(p.add_run(part[1:-1]), size, base_bold, True)
        else:
            _font(p.add_run(part), size, base_bold, base_italic)


def fmt(p, spacing=2.0, indent=True, align=None, before=0, after=0, hanging=False, keep=False):
    pf = p.paragraph_format
    pf.line_spacing = spacing
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.first_line_indent = Cm(1.27) if indent else Cm(0)
    if hanging:
        pf.left_indent = Cm(1.27)
        pf.first_line_indent = Cm(-1.27)
    if align is not None:
        p.alignment = align
    if keep:
        pf.keep_with_next = True


def field(paragraph, instr):
    run = paragraph.add_run()
    for tag, text in (("begin", None), (None, instr), ("separate", None), (None, "Actualice el índice (F9)"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
            run._r.append(el)
        elif text == instr:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = instr
            run._r.append(it)
        else:
            t = OxmlElement("w:t")
            t.text = text
            run._r.append(t)
    _font(run)


def page_number_header(section):
    hdr = section.header
    p = hdr.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run()
    for tag, instr in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
            run._r.append(el)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = instr
            run._r.append(it)
    _font(run)


def heading(doc, level, text, spacing):
    p = doc.add_paragraph(style=f"Heading {min(level, 4)}")
    # Niveles APA 7: 1 centrado negrita; 2 izquierda negrita; 3 izquierda negrita cursiva; 4 sangría negrita con punto.
    if level == 1:
        fmt(p, spacing, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, keep=True)
        add_inline(p, text, base_bold=True)
    elif level == 2:
        fmt(p, spacing, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, keep=True)
        add_inline(p, text, base_bold=True)
    elif level == 3:
        fmt(p, spacing, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, keep=True)
        add_inline(p, text, base_bold=True, base_italic=True)
    else:
        fmt(p, spacing, indent=True, keep=True)
        add_inline(p, text.rstrip(".") + ".", base_bold=True)
    return p


def set_cell_border(cell, **edges):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge, val in edges.items():
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), val)
        el.set(qn("w:sz"), "8")
        el.set(qn("w:color"), "000000")
        borders.append(el)


class Builder:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.sp = cfg["interlineado"]
        self.doc = Document()
        self.tables = 0
        self.figures = 0
        self._setup()

    def _setup(self):
        d = self.doc
        st = d.styles["Normal"]
        st.font.name = FONT
        st.font.size = Pt(12)
        st.font.color.rgb = BLACK
        st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        for i in range(1, 5):
            hs = d.styles[f"Heading {i}"]
            hs.font.name = FONT
            hs.font.size = Pt(12)
            hs.font.color.rgb = BLACK
            hs.font.bold = True
            hs.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        sec = d.sections[0]
        sec.page_height, sec.page_width = Cm(27.94), Cm(21.59)  # carta
        for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
            setattr(sec, m, Cm(2.54))
        page_number_header(sec)
        d.core_properties.author = "Jorge Gutiérrez (@JorgeGutho21)"
        d.core_properties.last_modified_by = "Jorge Gutiérrez (@JorgeGutho21)"
        d.core_properties.comments = ""
        d.core_properties.title = self.cfg["titulo"]
        d.core_properties.subject = self.cfg["subtitulo"]
        d.core_properties.language = "es-CO"

    def portada(self):
        d = self.doc
        for _ in range(3):
            fmt(d.add_paragraph(), self.sp, indent=False)
        p = d.add_paragraph()
        fmt(p, self.sp, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER)
        add_inline(p, self.cfg["titulo"], base_bold=True)
        p = d.add_paragraph()
        fmt(p, self.sp, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER)
        add_inline(p, self.cfg["subtitulo"])
        fmt(d.add_paragraph(), self.sp, indent=False)
        for line in PORTADA:
            p = d.add_paragraph()
            fmt(p, self.sp, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER)
            add_inline(p, line)
        p = d.add_paragraph()
        fmt(p, self.sp, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER)
        add_inline(p, "Repositorio: https://github.com/JorgeGutho21/ScriptLens")
        d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def table(self, title, rows):
        self.tables += 1
        d = self.doc
        p = d.add_paragraph()
        fmt(p, self.sp, indent=False, keep=True)
        add_inline(p, f"Tabla {self.tables}", base_bold=True)
        p = d.add_paragraph()
        fmt(p, self.sp, indent=False, keep=True)
        add_inline(p, title, base_italic=True)
        cols = max(len(r) for r in rows)
        t = d.add_table(rows=len(rows), cols=cols)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, r in enumerate(rows):
            for j in range(cols):
                c = t.cell(i, j)
                c.text = ""
                cp = c.paragraphs[0]
                fmt(cp, 1.0, indent=False, before=2, after=2)
                add_inline(cp, r[j] if j < len(r) else "", size=10.5, base_bold=(i == 0))
                edges = {}
                if i == 0:
                    edges.update(top="single", bottom="single")
                if i == len(rows) - 1:
                    edges.update(bottom="single")
                if edges:
                    set_cell_border(c, **edges)
        fmt(d.add_paragraph(), 1.0, indent=False)

    def figure(self, path, title, note):
        self.figures += 1
        d = self.doc
        p = d.add_paragraph()
        fmt(p, self.sp, indent=False, keep=True)
        add_inline(p, f"Figura {self.figures}", base_bold=True)
        p = d.add_paragraph()
        fmt(p, self.sp, indent=False, keep=True)
        add_inline(p, title, base_italic=True)
        p = d.add_paragraph()
        fmt(p, 1.0, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, keep=bool(note))
        img = ROOT / path
        p.add_run().add_picture(str(img), width=Cm(15.5))
        if note:
            p = d.add_paragraph()
            fmt(p, self.sp, indent=False)
            add_inline(p, "*Nota.* " + note)

    def code(self, lines):
        for line in lines:
            p = self.doc.add_paragraph()
            fmt(p, 1.0, indent=False)
            p.paragraph_format.left_indent = Cm(1.0)
            _font(p.add_run(line if line else " "), 9.5, mono=True)
        fmt(self.doc.add_paragraph(), 1.0, indent=False)

    def build(self, text: str):
        self.portada()
        lines = text.splitlines()
        i = 0
        refs = False
        pending_table = None
        while i < len(lines):
            line = lines[i].rstrip()
            s = line.strip()
            if not s:
                i += 1
                continue
            if s == "[[TOC]]":
                p = self.doc.add_paragraph()
                fmt(p, self.sp, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER)
                add_inline(p, "Contenido", base_bold=True)
                field(self.doc.add_paragraph(), 'TOC \\o "1-2" \\h \\z \\u')
                self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            elif s == "[[SALTO]]":
                self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            elif s == "[[REFERENCIAS]]":
                refs = True
            elif s.startswith("```"):
                block = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    block.append(lines[i].rstrip())
                    i += 1
                self.code(block)
            elif m := re.match(r"^(#{1,4})\s+(.*)", s):
                refs = False  # la lista de referencias termina en el siguiente encabezado
                heading(self.doc, len(m.group(1)), m.group(2), self.sp)
            elif s.startswith("Tabla:"):
                pending_table = s[6:].strip()
            elif s.startswith("|"):
                rows = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                    if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                        rows.append(cells)
                    i += 1
                self.table(pending_table or "", rows)
                pending_table = None
                continue
            elif s.startswith("Figura:"):
                parts = [x.strip() for x in s[7:].split("|")]
                self.figure(parts[0], parts[1], parts[2] if len(parts) > 2 else "")
            elif m := re.match(r"^-\s+(.*)", s):
                p = self.doc.add_paragraph(style="List Bullet")
                fmt(p, self.sp, indent=False)
                add_inline(p, m.group(1))
            elif m := re.match(r"^(\d+)\.\s+(.*)", s):
                # Numeración explícita: cada lista empieza en el número escrito en la fuente.
                p = self.doc.add_paragraph()
                fmt(p, self.sp, indent=False)
                p.paragraph_format.left_indent = Cm(1.27)
                p.paragraph_format.first_line_indent = Cm(-0.63)
                add_inline(p, f"{m.group(1)}. {m.group(2)}")
            else:
                p = self.doc.add_paragraph()
                if refs:
                    fmt(p, self.sp, indent=False, hanging=True)
                else:
                    fmt(p, self.sp, indent=True)
                add_inline(p, s)
            i += 1

    def save(self):
        self.cfg["salida"].parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(self.cfg["salida"])
        print(f"{self.cfg['salida'].relative_to(ROOT)}: {self.tables} tablas, {self.figures} figuras")


def main(only: list[str]):
    for cfg in DOCUMENTOS:
        if only and cfg["fuente"] not in only:
            continue
        b = Builder(cfg)
        b.build((FUENTES / cfg["fuente"]).read_text(encoding="utf-8"))
        b.save()


if __name__ == "__main__":
    main(sys.argv[1:])
