"""Pruebas del Centro de seguridad (fase 4)."""

import sys
import time

import pytest

from backend.security import audit
from backend.security.collect import command_executable

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Solo Windows")

KEYS = {"code", "estado", "categoria", "que", "donde", "por_que", "evidencia", "falta", "consecuencias", "que_hacer", "no_hacer", "fuente", "medido_en"}


def base(**over):
    raw = {
        "measured_at": time.time(),
        "defender": {"AntivirusEnabled": True, "RealTimeProtectionEnabled": True, "AntivirusSignatureAge": 0, "IsTamperProtected": True},
        "threats": None,
        "detections": None,
        "av_products": {"displayName": "Windows Defender", "productState": 397568},
        "firewall": [{"Name": "Domain", "Enabled": True}, {"Name": "Private", "Enabled": True}, {"Name": "Public", "Enabled": True}],
        "tasks": [],
        "events": [],
        "users": [],
        "power": "GUID de plan de energía: x (Equilibrado)",
        "startup": [],
        "services": [],
        "sessions": [],
    }
    raw.update(over)
    return raw


def codes(result):
    return {f["code"] for f in result["findings"]}


def test_command_executable_parsing():
    assert command_executable('"C:\\Program Files\\App\\app.exe" /background') == "C:\\Program Files\\App\\app.exe"
    assert command_executable("C:\\taller1\\gestion.bat") == "C:\\taller1\\gestion.bat"
    assert command_executable("C:\\Program Files\\X Y\\run.exe -a") == "C:\\Program Files\\X Y\\run.exe"


def test_healthy_system_has_no_alerts():
    r = audit.evaluate(base())
    assert not [f for f in r["findings"] if f["estado"] in ("requiere_revision", "amenaza_detectada", "actividad_sospechosa")]


def test_findings_have_eight_point_structure():
    r = audit.evaluate(base(firewall=[{"Name": "Public", "Enabled": False}]))
    f = next(x for x in r["findings"] if x["code"] == "firewall_desactivado")
    assert KEYS <= set(f) and all(f[k] for k in ("que", "por_que", "que_hacer", "no_hacer"))


def test_disabled_realtime_protection_requires_review():
    r = audit.evaluate(base(defender={"AntivirusEnabled": True, "RealTimeProtectionEnabled": False, "AntivirusSignatureAge": 12}))
    assert {"proteccion_desactivada", "firmas_desactualizadas"} <= codes(r)


def test_threat_only_from_defender_and_resolution_respected():
    active = audit.evaluate(base(threats=[{"ThreatID": 7, "ThreatName": "Trojan:Demo", "SeverityID": 5}], detections=[{"ThreatID": 7, "ThreatStatusID": 1, "Resources": ["file:_C:\\x.exe"], "Time": "2026"}]))
    f = next(x for x in active["findings"] if x["categoria"] == "Amenazas")
    assert f["estado"] == "amenaza_detectada" and "Defender" in f["fuente"] + f["por_que"]
    quarantined = audit.evaluate(base(threats=[{"ThreatID": 7, "ThreatName": "Trojan:Demo"}], detections=[{"ThreatID": 7, "ThreatStatusID": 3, "Resources": [], "Time": "2026"}]))
    assert next(x for x in quarantined["findings"] if x["categoria"] == "Amenazas")["estado"] == "informativo"


def test_permission_error_is_reported_as_insufficient_information():
    r = audit.evaluate(base(detections={"error": "Acceso denegado"}))
    assert next(f for f in r["findings"] if f["code"] == "historial_amenazas_inaccesible")["estado"] == "info_insuficiente"


def test_startup_script_with_microsoft_like_name_requires_review(tmp_path):
    bat = tmp_path / "gestion.bat"
    bat.write_text("@echo off\nsysteminfo\n", encoding="utf-8")
    entry = {"id": "HKCU:SoyMicrosoft", "nombre": "SoyMicrosoft", "comando": str(bat), "ejecutable": str(bat), "origen": "Registro (usuario) · Run", "ambito": "usuario", "habilitado": True, "modificable_sin_admin": True, "scope": "HKCU"}
    r = audit.evaluate(base(startup=[entry]))
    item = r["startup"][0]
    assert item["estado"] == "requiere_revision"
    assert any("script" in m for m in item["motivos"]) and any("Microsoft" in m for m in item["motivos"])
    # No se califica como malware ni como amenaza
    assert all(f["estado"] != "amenaza_detectada" for f in r["findings"])


def test_disabled_startup_entry_is_not_alarming():
    entry = {"id": "HKCU:Old", "nombre": "Old", "comando": "C:\\x\\run.bat", "ejecutable": "C:\\x\\run.bat", "origen": "Run", "habilitado": False, "scope": "HKCU"}
    assert audit.evaluate(base(startup=[entry]))["startup"][0]["estado"] != "requiere_revision"


def test_hidden_encoded_task_requires_review():
    task = {"name": "Actualizador", "path": "\\", "state": "Ready", "author": None, "actions": [{"exe": "powershell.exe", "args": "-w hidden -enc SQBFAFgA"}], "triggers": ["MSFT_TaskLogonTrigger"]}
    ms_task = {"name": "X", "path": "\\Microsoft\\Windows\\", "state": "Ready", "actions": [{"exe": "powershell.exe", "args": "-enc AAA"}]}
    r = audit.evaluate(base(tasks=[task, ms_task]))
    assert r["tasks"]["de_microsoft"] == 1 and len(r["tasks"]["otras"]) == 1
    assert r["tasks"]["otras"][0]["estado"] == "requiere_revision"


def test_unexpected_shutdown_event_is_explained():
    ev = [{"Id": 41, "ProviderName": "Microsoft-Windows-Kernel-Power", "LevelDisplayName": "Crítico", "Time": "2026-11-13"}] * 2
    r = audit.evaluate(base(events=ev))
    f = next(x for x in r["findings"] if x["code"].startswith("evento_Microsoft-Windows-Kernel-Power"))
    assert "2 vez" in f["evidencia"]


def test_real_collection_reads_sources_without_admin():
    from backend.security.collect import collect

    raw = collect()
    r = audit.evaluate(raw)
    assert r["sources"]["startup"]["ok"] and r["sources"]["services"]["ok"]
    assert r["sources"]["firewall"]["ok"]
    assert r["services"]["total"] > 50
    for f in r["findings"]:
        assert KEYS <= set(f)
