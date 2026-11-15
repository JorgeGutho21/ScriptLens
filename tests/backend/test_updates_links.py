"""Comprobación de actualizaciones y apertura de enlaces (lista permitida)."""

import io
import json
import urllib.error

from fastapi.testclient import TestClient

from backend.core import updates
from backend.core.api import Engine, create_app
from backend.core.config import APP_VERSION, Settings


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_update_newer_version(monkeypatch):
    monkeypatch.setattr(updates.urllib.request, "urlopen", lambda req, timeout: _Resp(json.dumps({"tag_name": "v9.0.0", "html_url": "https://github.com/JorgeGutho21/ScriptLens/releases/tag/v9.0.0"}).encode()))
    r = updates.check()
    assert r["hay_nueva"] and r["actual"] == APP_VERSION and "SHA-256" in r["mensaje"]


def test_update_without_releases_or_network(monkeypatch):
    def not_found(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(updates.urllib.request, "urlopen", not_found)
    assert updates.check()["hay_nueva"] is False

    def offline(req, timeout):
        raise urllib.error.URLError("sin red")

    monkeypatch.setattr(updates.urllib.request, "urlopen", offline)
    assert "Sin conexión" in updates.check()["mensaje"]


def test_open_link_allowlist(tmp_path, monkeypatch):
    opened = []
    import webbrowser

    monkeypatch.setattr(webbrowser, "open", lambda url: opened.append(url))
    settings = Settings(token="t", data_dir=tmp_path)
    with TestClient(create_app(settings, Engine(settings))) as c:
        c.headers["X-ScriptLens-Token"] = "t"
        assert c.post("/api/open-link", json={"url": "https://github.com/JorgeGutho21/ScriptLens"}).status_code == 200
        assert c.post("/api/open-link", json={"url": "https://ollama.com/download"}).status_code == 200
        for bad in ("https://evil.example/x", "file:///C:/Windows/System32/calc.exe", "https://ollama.com/download\" & calc", "C:\\Windows\\notepad.exe"):
            assert c.post("/api/open-link", json={"url": bad}).status_code == 400
    assert opened == ["https://github.com/JorgeGutho21/ScriptLens", "https://ollama.com/download"]
