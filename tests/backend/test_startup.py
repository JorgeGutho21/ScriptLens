"""Prueba de integración del arranque real del motor (python -m backend)."""

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _start(env_extra: dict) -> tuple[subprocess.Popen, dict]:
    env = {**os.environ, **env_extra}
    proc = subprocess.Popen([sys.executable, "-m", "backend"], cwd=ROOT, env=env, stdout=subprocess.PIPE, text=True)
    ready = json.loads(proc.stdout.readline())
    return proc, ready


def test_ready_line_and_immediate_connection():
    proc, ready = _start({})
    try:
        assert ready["event"] == "ready" and ready["port"] > 0 and len(ready["token"]) >= 32
        # Conexión inmediata tras "ready": el socket ya escucha, no debe ser rechazada.
        req = urllib.request.Request(f"http://127.0.0.1:{ready['port']}/api/health", headers={"X-ScriptLens-Token": ready["token"]})
        with urllib.request.urlopen(req, timeout=10) as r:
            assert json.loads(r.read())["status"] == "ok"
    finally:
        proc.kill()
        proc.wait(timeout=10)


def test_backend_exits_when_parent_disappears():
    parent = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    proc, _ = _start({"SCRIPTLENS_PARENT_PID": str(parent.pid)})
    try:
        parent.kill()
        parent.wait(timeout=10)
        deadline = time.time() + 15
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.2)
        assert proc.poll() is not None, "el motor siguió vivo sin la aplicación"
    finally:
        if proc.poll() is None:
            proc.kill()
