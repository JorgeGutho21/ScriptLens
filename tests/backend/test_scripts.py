"""Pruebas del analizador de scripts (fase 5).

Incluye los casos funcionales CP1–CP6 de la guía original 03B (§12.2).
"""

import ast
import base64
import time
from pathlib import Path

from fastapi.testclient import TestClient

from backend.core.api import Engine, create_app
from backend.core.config import Settings
from backend.scripts.analyzer import analyze
from backend.scripts.catalog import ORIGINAL, hallazgos
from backend.scripts.deobfuscate import decoded_payloads, normalize_line
from backend.scripts.flow import flujo_bat
from backend.scripts.reading import decode

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "backend" / "scripts"


def reglas(texto):
    return {h["regla"] for h in hallazgos(texto)}


def test_original_catalog_is_preserved():
    assert len(ORIGINAL) == 24
    assert {r.id for r in ORIGINAL} >= {"C01", "E03", "P01", "B01", "O03", "N01", "K01", "A03"}


def test_cp1_consulta():
    r = analyze(b"@echo off\nsysteminfo\ntasklist\n", "cp1.bat")
    assert {"C01", "C02"} <= {h["regla"] for h in r["hallazgos"]}
    assert r["clasificacion"]["reglas"] == "consulta"
    assert r["clasificacion"]["hibrida"] == "consulta"


def test_cp2_run_key_is_persistence():
    texto = 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v Demo /d C:\\Lab\\demo.bat /f'
    assert {"R01", "P01"} <= reglas(texto)
    r = analyze(texto.encode(), "cp2.bat")
    assert r["clasificacion"]["hibrida"] == "sensible"
    assert any(t["id"] == "T1547.001" and t["nombre"] for t in r["tecnicas"])


def test_reading_run_key_is_not_persistence():
    """Corrección por contexto encontrada en el análisis de errores."""
    assert "P01" not in reglas('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"')
    assert "C06" in reglas('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"')


def test_cp3_infinite_loop_and_loop_with_exit():
    f = flujo_bat(":INICIO\ntasklist\ntimeout /t 5 >nul\ngoto INICIO\n")
    assert f["posible_ciclo_infinito"]
    g = flujo_bat(":INICIO\nset /a n+=1\nif %n% GEQ 3 goto FIN\ngoto INICIO\n:FIN\n")
    assert g["ciclos"] and not g["posible_ciclo_infinito"]


def test_cp4_comments_are_ignored():
    assert reglas('rem reg add "HKCU\\...\\Run"\n:: del /f x\n# Remove-Item x -Recurse') == set()
    assert reglas("<#\nInvoke-Expression $x\n#>\nGet-Date") == set()


def test_cp5_utf16_is_read():
    texto, enc = decode("systeminfo\r\nwhoami".encode("utf-16"))
    assert "systeminfo" in texto and enc.startswith("utf-16")
    texto2, _ = decode("tasklist".encode("utf-16-le"))  # sin BOM
    assert texto2 == "tasklist"


def test_cp6_large_file_is_truncated_quickly():
    data = (b"echo linea de relleno\n" * 260000)[:5_000_000]
    t = time.perf_counter()
    r = analyze(data, "grande.bat")
    assert r["truncado"] and time.perf_counter() - t < 10
    assert any("1 MB" in l for l in r["limitaciones"])


def test_nul_redirection_is_not_a_write():
    assert "E03" not in reglas("timeout /t 5 >nul")
    assert "E03" in reglas("systeminfo > C:\\Lab\\r.txt")


def test_deobfuscation_caret_backtick_concat_and_base64():
    assert "taskkill" in normalize_line("t^a^s^k^k^i^l^l /f /im x.exe", "bat")
    # `n, `t, `r… son secuencias especiales en PowerShell; la ofuscación real evita usarlas.
    assert "Invoke-Expression" in normalize_line("Inv`ok`e-Ex`pr`ess`ion $c", "powershell")
    assert normalize_line('Write-Host "a`nb"', "powershell") == 'Write-Host "a`nb"'
    assert "Invoke-Expression" in normalize_line("& ('Invoke-' + 'Expression') $c", "powershell")
    enc = base64.b64encode("Remove-Item C:\\Lab -Recurse".encode("utf-16-le")).decode()
    payloads = decoded_payloads(f"powershell -enc {enc}")
    assert payloads and "Remove-Item" in payloads[0]["texto"]
    r = analyze(f"powershell -NoP -enc {enc}".encode(), "x.ps1")
    assert any(h.get("decodificado") and h["regla"] == "B01" for h in r["hallazgos"])
    assert r["ofuscacion"]


def test_results_are_independent_and_honest():
    r = analyze(b"Set-MpPreference -DisableRealtimeMonitoring $true\n", "d.ps1")
    c = r["clasificacion"]
    assert set(c) >= {"estadistica", "reglas", "hibrida"}
    assert r["severidad"]["nivel"] in ("alta", "critica")
    assert any("no es la probabilidad" in l for l in r["limitaciones"])
    assert r["ejecutado"] is False
    assert any(t["id"] == "T1685" for t in r["tecnicas"])  # identificador vigente en ATT&CK 20.1


def test_line_explanations_cover_every_line():
    texto = "@echo off\nrem comentario\necho Hola\nsysteminfo\nfoo-bar-desconocido\n"
    r = analyze(texto.encode(), "x.bat")
    tipos = {l["linea"]: l["tipo"] for l in r["explicacion_lineas"]}
    assert tipos == {1: "comun", 2: "comentario", 3: "comun", 4: "regla", 5: "no_catalogado"}


def test_analyzer_never_executes_code():
    """Regla de oro del proyecto original: ningún módulo del analizador ejecuta procesos."""
    forbidden = {"subprocess", "os.system", "os.popen", "os.startfile", "Popen", "run_ps", "ShellExecute"}
    for py in SCRIPTS_DIR.glob("*.py"):
        if py.name == "train.py":
            continue
        tree = ast.parse(py.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names |= {a.name for a in node.names} | ({node.module} if isinstance(node, ast.ImportFrom) and node.module else set())
            elif isinstance(node, ast.Attribute):
                names.add(f"{getattr(node.value, 'id', '')}.{node.attr}")
                names.add(node.attr)
        assert not (names & forbidden), f"{py.name} usa {names & forbidden}"


def test_api_analyze_roundtrip(tmp_path):
    settings = Settings(token="t", data_dir=tmp_path)
    engine = Engine(settings)
    with TestClient(create_app(settings, engine)) as c:
        c.headers["X-ScriptLens-Token"] = "t"
        body = {"nombre": "a.bat", "contenido_b64": base64.b64encode(b"attrib +h +s x.bat").decode()}
        r = c.post("/api/scripts/analyze", json=body).json()
        assert r["clasificacion"]["hibrida"] == "sensible"
        assert engine.last_script_analysis["archivo"] == "a.bat"
        assert c.post("/api/scripts/analyze", json={"contenido_b64": "@@no-base64@@"}).status_code == 422
        m = c.get("/api/scripts/model").json()
        assert m["corpus"]["total"] == 180
