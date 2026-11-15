"""Genera la presentación de ExpoSoftware (PPTX) con la identidad visual de ScriptLens IA.

Uso (PowerShell, raíz del repositorio):
    .\\.venv\\Scripts\\python docs\\expo_software\\generar_presentacion.py
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
CAP = ROOT / "docs" / "capturas"
OUT = Path(__file__).parent / "ScriptLens_IA_ExpoSoftware.pptx"

BG = RGBColor(0x08, 0x0B, 0x10)
SURFACE = RGBColor(0x12, 0x18, 0x22)
ACCENT = RGBColor(0x3B, 0x8C, 0xFF)
TEXT = RGBColor(0xE8, 0xEE, 0xF7)
MUTED = RGBColor(0x93, 0xA1, 0xB5)
FONT = "Segoe UI"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
W, H = prs.slide_width, prs.slide_height


def base(title: str | None = None, kicker: str | None = None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.12), H)
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()
    if kicker:
        text(s, kicker.upper(), Inches(0.7), Inches(0.45), Inches(10), Inches(0.4), 13, ACCENT, bold=True)
    if title:
        text(s, title, Inches(0.7), Inches(0.8), Inches(12), Inches(0.9), 32, TEXT, bold=True)
    text(s, "ScriptLens IA · Jorge Gutiérrez · @JorgeGutho21", Inches(0.7), H - Inches(0.5), Inches(8), Inches(0.3), 10, MUTED)
    text(s, str(len(prs.slides)), W - Inches(1.0), H - Inches(0.5), Inches(0.5), Inches(0.3), 10, MUTED, align=PP_ALIGN.RIGHT)
    return s


def text(s, t, x, y, w, h, size=18, color=TEXT, bold=False, align=PP_ALIGN.LEFT):
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(t.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.name, r.font.size, r.font.bold = FONT, Pt(size), bold
        r.font.color.rgb = color
    return tb


def bullets(s, items, x, y, w, h, size=19):
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(10)
        r = p.add_run()
        r.text = "▸  " + it
        r.font.name, r.font.size = FONT, Pt(size)
        r.font.color.rgb = TEXT


def card(s, x, y, w, h, title, body, num=None):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = SURFACE
    sh.line.color.rgb = RGBColor(0x22, 0x2C, 0x3B)
    sh.adjustments[0] = 0.08
    if num:
        text(s, num, x + Inches(0.25), y + Inches(0.15), w - Inches(0.5), Inches(0.7), 30, ACCENT, bold=True)
    text(s, title, x + Inches(0.25), y + Inches(0.85 if num else 0.2), w - Inches(0.5), Inches(0.5), 17, TEXT, bold=True)
    text(s, body, x + Inches(0.25), y + Inches(1.35 if num else 0.7), w - Inches(0.5), h - Inches(1.4), 13, MUTED)


def image(s, name, x, y, w):
    s.shapes.add_picture(str(CAP / name), x, y, width=w)


# 1. Portada
s = base()
s.shapes.add_picture(str(ROOT / "src-tauri" / "icons" / "icon.png"), Inches(0.9), Inches(1.6), height=Inches(1.6))
text(s, "ScriptLens IA", Inches(0.9), Inches(3.4), Inches(8), Inches(1.0), 54, TEXT, bold=True)
text(s, "Diagnóstico explicable de Windows con análisis de scripts\ne inteligencia artificial local verificada", Inches(0.9), Inches(4.5), Inches(7.5), Inches(1.0), 20, MUTED)
text(s, "Jorge Gutiérrez · Ingeniería de Sistemas · Universidad Popular del Cesar\nExpoSoftware 2026-II · Docente: Oswaldo Rueda Carreño", Inches(0.9), Inches(5.8), Inches(8), Inches(0.8), 14, MUTED)
image(s, "02_panel_general.png", Inches(8.3), Inches(1.4), Inches(4.6))

# 2. Problema
s = base("¿Por qué está lento mi computador?", "El problema")
bullets(s, [
    "La información existe, pero está dispersa y es técnica: Administrador de tareas, Registro, Visor de eventos, Programador de tareas.",
    "Los consejos de Internet suelen ser riesgosos: «cierre ese proceso», «desactive el antivirus».",
    "En clase circulan scripts que escriben en el Registro, crean tareas u ocultan archivos.",
    "Quien ejecuta un script sin leerlo asume efectos que desconoce.",
], Inches(0.7), Inches(2.0), Inches(7.2), Inches(4.5))
card(s, Inches(8.4), Inches(2.0), Inches(4.3), Inches(3.6), "Pregunta de investigación", "¿Pueden mediciones verificadas, reglas ATT&CK, aprendizaje supervisado y un modelo de lenguaje local explicar el estado del equipo y el riesgo de un script, sin enviar datos ni actuar sin permiso?")

# 3. Solución
s = base("Medir · Explicar · Actuar con supervisión", "La solución")
for i, (t, b) in enumerate([
    ("Medir", "CPU, RAM, disco, red y procesos en tiempo real. Consumo sostenido, no picos."),
    ("Explicar", "Qué hace cada proceso, qué es comprobado y qué es estimado. Scripts sin ejecutarlos."),
    ("Preguntar", "Asistente con IA local que solo lee datos y verifica cada cifra."),
    ("Actuar", "Cierre, inicio automático y limpieza con confirmación, revalidación y auditoría."),
]):
    card(s, Inches(0.7 + i * 3.1), Inches(2.1), Inches(2.9), Inches(3.6), t, b, num=f"0{i + 1}")
text(s, "Todo ocurre en el equipo: ningún dato sale a Internet.", Inches(0.7), Inches(6.1), Inches(12), Inches(0.5), 17, ACCENT, bold=True)

# 4. Arquitectura
s = base("Arquitectura", "Diseño del sistema")
card(s, Inches(0.7), Inches(2.0), Inches(3.6), Inches(3.9), "Interfaz", "Tauri 2 (Rust) + React 19 + TypeScript + Tailwind. Modo sencillo/avanzado, claro/oscuro, accesibilidad, glosario.")
card(s, Inches(4.6), Inches(2.0), Inches(4.1), Inches(3.9), "Motor de análisis (Python)", "API solo en 127.0.0.1 con token aleatorio. psutil · NtQuerySystemInformation · Authenticode · SQLite · scikit-learn · reportlab.")
card(s, Inches(9.0), Inches(2.0), Inches(3.6), Inches(3.9), "IA local", "Ollama + Qwen3 4B Instruct. Herramientas de solo lectura, verificación de cifras, sin acceso a acciones.")
text(s, "Instalador NSIS de 49,26 MB · sin administrador · sin instalar Python, Node.js ni Rust", Inches(0.7), Inches(6.2), Inches(12), Inches(0.5), 16, MUTED)

# 5. Procesos y seguridad
s = base("Procesos y seguridad, explicados", "Funcionalidades")
image(s, "05_detalle_proceso.png", Inches(0.7), Inches(1.9), Inches(6.0))
image(s, "09_seguridad.png", Inches(6.9), Inches(1.9), Inches(6.0))
text(s, "331 procesos con firma válida verificada en el equipo de prueba. Ningún proceso se califica como malicioso solo por no tener firma o consumir mucho.", Inches(0.7), Inches(6.0), Inches(12), Inches(0.8), 15, MUTED)

# 6. Analizador de scripts
s = base("Analizar scripts sin ejecutarlos", "Motor analítico")
image(s, "11_script_lineas_attack.png", Inches(0.7), Inches(1.9), Inches(7.0))
bullets(s, [
    "43 reglas (24 del proyecto original) y MITRE ATT&CK 20.1",
    "Desofuscación: ^, `, concatenación, Base64",
    "Flujo y ciclos sin salida",
    "Explicación de cada línea",
    "TF-IDF de n-gramas + regresión logística balanceada",
], Inches(8.0), Inches(2.0), Inches(4.8), Inches(4.5), 16)

# 7. Resultados del clasificador
s = base("Resultados medidos del clasificador", "Evaluación")
rows = [("Conjunto", "Método", "F1 macro", "Recall sensible"),
        ("Sintético (180, VC 5 pliegues)", "Regresión logística", "0,955", "0,917"),
        ("Sintético (180, VC 5 pliegues)", "Híbrida", "0,966", "1,000"),
        ("Realista independiente (18)", "Reglas", "1,000", "1,000"),
        ("Realista independiente (18)", "Regresión logística", "0,886", "0,667"),
        ("Realista independiente (18)", "Híbrida", "1,000", "1,000")]
tbl = s.shapes.add_table(len(rows), 4, Inches(0.7), Inches(2.0), Inches(8.2), Inches(3.2)).table
for i, r in enumerate(rows):
    for j, v in enumerate(r):
        c = tbl.cell(i, j)
        c.text = v
        c.fill.solid()
        c.fill.fore_color.rgb = ACCENT if i == 0 else SURFACE
        para = c.text_frame.paragraphs[0]
        para.runs[0].font.size, para.runs[0].font.name = Pt(14), FONT
        para.runs[0].font.color.rgb = TEXT
        para.runs[0].font.bold = i == 0
card(s, Inches(9.2), Inches(2.0), Inches(3.5), Inches(4.2), "Lectura honesta", "El modelo solo dejó pasar 2 de 6 scripts sensibles reales; la política híbrida los recuperó. El análisis de errores corrigió la regla P01: falsos positivos 43,3 % → 0 %. Corpus pequeño: kappa pendiente.")

# 8. Asistente
s = base("Asistente local con cifras verificadas", "Inteligencia artificial")
image(s, "12_asistente_ia.png", Inches(0.7), Inches(1.9), Inches(7.0))
bullets(s, [
    "Solo herramientas de lectura",
    "Datos del equipo tratados como no confiables",
    "Cada cifra se compara con los datos medidos",
    "Caso real: detectó «70 % de la RAM» inventado",
    "Sin Ollama, responde con plantillas",
    "qwen3:4b razonaba 256 s → qwen3:4b-instruct 10–58 s",
], Inches(8.0), Inches(2.0), Inches(4.9), Inches(4.7), 15)

# 9. Acciones supervisadas
s = base("Nada sin su permiso", "Seguridad")
image(s, "08_confirmacion_accion.png", Inches(0.7), Inches(1.9), Inches(6.6))
bullets(s, [
    "Preparar → confirmar → ejecutar (token de un solo uso, 60 s)",
    "Se revalida PID + hora de creación + nombre",
    "Procesos críticos, de seguridad y servicios protegidos",
    "Inicio automático reversible",
    "Registro con mediciones antes y después",
    "Nunca desactiva antivirus, firewall ni actualizaciones",
], Inches(7.6), Inches(2.0), Inches(5.3), Inches(4.7), 15)

# 10. Pruebas y distribución
s = base("Pruebas y distribución", "Calidad")
for i, (n, t) in enumerate([("110", "pruebas automatizadas aprobadas"), ("< 0,05 s", "lectura de ≈ 345 procesos (antes 3,4 s)"), ("49 MB", "instalador probado: instalar, desinstalar, reinstalar"), ("5", "defectos hallados en la app instalada y corregidos")]):
    card(s, Inches(0.7 + i * 3.1), Inches(2.1), Inches(2.9), Inches(3.0), t, "", num=n)
text(s, "GitHub Actions: pruebas del motor, compilación de la interfaz y del contenedor; flujo que genera el instalador con SHA-256.", Inches(0.7), Inches(5.6), Inches(12), Inches(0.8), 15, MUTED)

# 11. Limitaciones y futuro
s = base("Limitaciones y trabajo futuro", "Discusión")
bullets(s, [
    "Corpus sintético y conjunto realista pequeño con un solo etiquetador",
    "El análisis estático no ve código descargado en ejecución",
    "La IA local tarda 10–60 s sin tarjeta gráfica",
    "Instalador sin firma comercial (aviso de SmartScreen)",
], Inches(0.7), Inches(2.0), Inches(6.0), Inches(4.5), 17)
bullets(s, [
    "Más scripts reales y kappa de Cohen",
    "Firma de código y publicación en Releases / WinGet",
    "Detección de anomalías (RecuperaSO IA)",
    "Pruebas de usabilidad con principiantes",
], Inches(7.0), Inches(2.0), Inches(5.8), Inches(4.5), 17)

# 12. Cierre
s = base()
text(s, "«Antes de ejecutar un script, léalo.\nScriptLens le ayuda a leerlo.»", Inches(0.9), Inches(2.3), Inches(11.5), Inches(2.0), 38, TEXT, bold=True)
text(s, "github.com/JorgeGutho21/ScriptLens", Inches(0.9), Inches(4.7), Inches(10), Inches(0.6), 22, ACCENT, bold=True)
text(s, "Jorge Gutiérrez · @JorgeGutho21 · ¡Gracias!", Inches(0.9), Inches(5.4), Inches(10), Inches(0.6), 18, MUTED)

prs.core_properties.author = "Jorge Gutiérrez (@JorgeGutho21)"
prs.core_properties.last_modified_by = "Jorge Gutiérrez (@JorgeGutho21)"
prs.core_properties.title = "ScriptLens IA — ExpoSoftware 2026-II"
prs.save(OUT)
print(f"{OUT.relative_to(ROOT)}: {len(prs.slides)} diapositivas")
