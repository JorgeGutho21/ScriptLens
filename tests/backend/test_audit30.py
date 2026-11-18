"""Auditoría de 30 controles: evaluación con evidencias reales, casos límite y solo lectura."""

from __future__ import annotations

import copy
import datetime as dt
import json
import re
from pathlib import Path

import pytest

from backend.audit30 import collect, evaluate, report

FIX = json.loads((Path(__file__).parents[1] / "fixtures" / "audit30" / "win11_sin_admin.json").read_text(encoding="utf-8"))
TODAY = dt.date(2026, 11, 18)


def by_num(res):
    return {c["numero"]: c for c in res["controles"]}


def test_real_windows11_capture():
    """Evidencias reales de Windows 11 Pro 25H2 sin administrador (2026-11-18)."""
    res = evaluate.evaluate(FIX, TODAY)
    c = by_num(res)
    assert len(res["controles"]) == 30 and [x["numero"] for x in res["controles"]] == list(range(1, 31))
    assert c[1]["estado"] == "NO APLICA"  # control específico de Windows 10
    assert c[2]["estado"] == "CUMPLE" and "2027-10-12" in c[2]["evidencia"]
    assert c[12]["estado"] == "NO APLICA"  # RDP desactivado
    assert c[14]["estado"] == c[15]["estado"] == "NO CUMPLE"
    assert c[22]["estado"] == "NO CUMPLE" and "Longitud mínima: 0" in c[22]["evidencia"]
    assert c[23]["estado"] == "NO CUMPLE" and c[24]["estado"] == "NO CUMPLE"
    assert c[25]["estado"] == c[26]["estado"] == "REQUIERE REVISIÓN"  # exigen administrador
    assert res["resumen"] == {"CUMPLE": 19, "NO CUMPLE": 5, "REQUIERE REVISIÓN": 4, "NO APLICA": 2}
    for x in res["controles"]:
        assert x["evidencia"] and x["explicacion"] and x["proposito"] and x["recomendacion"]


def test_missing_evidence_never_passes():
    res = evaluate.evaluate({}, TODAY)
    assert res["resumen"]["CUMPLE"] == 0
    assert all(x["estado"] in ("REQUIERE REVISIÓN", "NO APLICA", "NO CUMPLE") for x in res["controles"])


def test_windows10_after_end_of_support_requires_review():
    r = copy.deepcopy(FIX)
    r["os"].update(caption="Microsoft Windows 10 Pro", build=19045, display="22H2")
    c = by_num(evaluate.evaluate(r, TODAY))
    assert c[1]["estado"] == "CUMPLE"
    assert c[2]["estado"] == "REQUIERE REVISIÓN" and "ESU" in c[2]["evidencia"]
    r["os"]["build"] = 19044
    assert by_num(evaluate.evaluate(r, TODAY))[1]["estado"] == "NO CUMPLE"


def test_third_party_antivirus():
    r = copy.deepcopy(FIX)
    r["defender"] = {"av": False, "rtp": False, "behavior": False, "mode": "Passive Mode"}
    r["av_products"] = ["Windows Defender", "Antivirus Ejemplo"]
    c = by_num(evaluate.evaluate(r, TODAY))
    assert c[7]["estado"] == "CUMPLE" and "Antivirus Ejemplo" in c[7]["evidencia"]
    assert c[8]["estado"] == c[9]["estado"] == c[10]["estado"] == "NO APLICA"


def test_rdp_enabled_requires_nla_and_admin_sources():
    r = copy.deepcopy(FIX)
    r.update(rdp_deny=0, rdp_nla=0, admin=True, audit=[{"sub": "Logon", "valor": "Success and Failure"}, {"sub": "User Account Management", "valor": "Success"}])
    r["tpm"] = {"present": True, "ready": True, "origen": "Get-Tpm"}
    c = by_num(evaluate.evaluate(r, TODAY))
    assert c[11]["estado"] == "REQUIERE REVISIÓN" and c[12]["estado"] == "NO CUMPLE"
    assert c[25]["estado"] == "CUMPLE" and c[26]["estado"] == "CUMPLE"
    r["audit"][0]["valor"] = "No Auditing"
    assert by_num(evaluate.evaluate(r, TODAY))[26]["estado"] == "NO CUMPLE"


def test_password_policy_parsing_is_positional():
    r = copy.deepcopy(FIX)
    r["net_accounts"] = ["Never", "0", "42", "12", "None", "5", "10", "10", "WORKSTATION"]  # salida en inglés
    assert by_num(evaluate.evaluate(r, TODAY))[22]["estado"] == "CUMPLE"
    r["net_accounts"] = ["Never", "0", "42", "12", "None", "Never", "10", "10", "WORKSTATION"]
    assert by_num(evaluate.evaluate(r, TODAY))[22]["estado"] == "NO CUMPLE"  # sin bloqueo


def test_collection_script_is_read_only():
    s = collect.SCRIPT  # New-Object solo crea en memoria el objeto COM para leer la propiedad de BitLocker
    forbidden = r"\b(Set|New|Remove|Enable|Disable|Add|Clear|Stop|Start|Restart|Install|Uninstall)-(?!Object\b)\w+|Invoke-WebRequest|Invoke-RestMethod|reg(\.exe)?\s+(add|delete)|auditpol(\.exe)?\s+/set|net\s+(user|share|accounts)\s+\S+\s*/|Out-File|Set-Content|Export-Csv"
    assert not re.search(forbidden, s, re.I)
    for secret_source in ("Get-ChildItem Env:", "SerialNumber", "whoami", "netstat"):
        assert secret_source not in s  # anexos del original que podían contener secretos


def test_reports(tmp_path):
    res = evaluate.evaluate(FIX, TODAY)
    res["medido_en"] = 1_800_000_000
    html = report.render_html(res, "PC-PRUEBA")
    assert html.count("<tr>") == 31 and "Jorge Gutiérrez" in html and "REQUIERE REVISIÓN" in html
    pdf = report.render_pdf(res, "PC-PRUEBA", tmp_path / "a.pdf")
    from pypdf import PdfReader

    text = "".join(p.extract_text() for p in PdfReader(str(pdf)).pages)
    assert "Firma SMB requerida en servidor" in text and "NO CUMPLE" in text


@pytest.mark.skipif(not __import__("sys").platform.startswith("win"), reason="Solo Windows")
def test_live_collection_on_this_pc():
    raw = collect.collect()
    res = evaluate.evaluate(raw)
    assert len(res["controles"]) == 30 and raw.get("os")
