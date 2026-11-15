"""Pruebas de los informes (fase 8)."""

import time

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from backend.core.api import Engine, create_app
from backend.core.config import Settings
from backend.reports import html_report


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    import os

    os.environ["SCRIPTLENS_REPORTS_DIR"] = str(tmp_path_factory.mktemp("informes"))
    settings = Settings(token="t", sample_interval=0.2, process_interval=0.4, data_dir=tmp_path_factory.mktemp("rep"))
    engine = Engine(settings)
    app = create_app(settings, engine)
    engine.start()
    time.sleep(2.0)
    with TestClient(app) as c:
        c.headers["X-ScriptLens-Token"] = "t"
        yield c
    engine.stop()
    os.environ.pop("SCRIPTLENS_REPORTS_DIR", None)


def test_html_report_has_identity_sections_and_watermark(client):
    r = client.post("/api/reports", json={"formato": "html", "incluir_seguridad": False}).json()
    from pathlib import Path

    html = Path(r["ruta"]).read_text(encoding="utf-8")
    for text in ("ScriptLens IA", "Jorge Gutiérrez", "@JorgeGutho21", "github.com/JorgeGutho21/ScriptLens", "Métricas medidas", "Procesos destacados", "Recomendaciones", "Acciones realizadas", "Limitaciones del diagnóstico"):
        assert text in html, text
    assert 'class="wm"' in html and "opacity:.045" in html  # marca de agua discreta


def test_untrusted_names_are_escaped():
    assert html_report.e("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"


def test_pdf_report_is_valid_and_contains_author(client):
    r = client.post("/api/reports", json={"formato": "pdf", "incluir_seguridad": True}).json()
    reader = PdfReader(r["ruta"])
    text = "\n".join(p.extract_text() for p in reader.pages)
    assert len(reader.pages) >= 2
    assert "Jorge Gutiérrez" in text and "Seguridad" in text and "Limitaciones" in text
    assert reader.metadata.author.startswith("Jorge Gutiérrez")
    listing = client.get("/api/reports").json()["informes"]
    assert any(i["archivo"] == r["archivo"] for i in listing)


def test_open_rejects_paths_outside_reports(client):
    assert client.post("/api/reports/open/..%5C..%5Cwindows%5Cwin.ini").status_code == 404
    assert client.post("/api/reports/open/otro.pdf").status_code == 404
