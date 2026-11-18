"""Captura páginas con Microsoft Edge sin ventana (protocolo DevTools) para la documentación.

Uso (PowerShell, desde la raíz del repositorio):
    .\\.venv\\Scripts\\python scripts\\capturar_navegador.py pasos.json

``pasos.json`` es una lista de pasos que se ejecutan en orden:
    {"tam": [1440, 900, 1, false]}      ancho, alto, escala y si emula un celular
    {"ir": "http://localhost:1420/"}    abrir una dirección
    {"js": "document.title"}            evaluar JavaScript (se imprime el resultado)
    {"esperar": 2}                      esperar segundos
    {"foto": "docs/capturas/x.png"}     guardar el área visible ("completa": true = toda la página)
    {"foto": "x.png", "elemento": "#id"} guardar solo un elemento de la página
    {"pestana": "celular"}              cambiar de pestaña (se crea si no existe)
    {"js": "...", "guardar": "codigo"}  guardar el resultado; después {{codigo}} se sustituye en otros "js"

El perfil del navegador se guarda en ``.dev-data/edge-capturas`` (ignorada por Git), así que las
cookies de una ejecución siguen disponibles en la siguiente.
"""

from __future__ import annotations

import asyncio
import base64
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import websockets

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
ROOT = Path(__file__).resolve().parents[1]
PORT = 9333


async def run(steps: list[dict]) -> None:
    profile = ROOT / ".dev-data" / "edge-capturas"
    proc = subprocess.Popen([EDGE, "--headless=new", f"--remote-debugging-port={PORT}", "--remote-debugging-address=127.0.0.1", f"--user-data-dir={profile}", "--no-first-run", "--hide-scrollbars", "about:blank"])
    try:
        for _ in range(50):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
                ws_url = next(t["webSocketDebuggerUrl"] for t in tabs if t["type"] == "page")
                break
            except Exception:  # noqa: BLE001
                time.sleep(0.2)
        tabs: dict[str, object] = {}
        counter = [0]

        async def open_tab(name: str, url: str | None = None):
            if url is None:
                target = ws_url
            else:
                info = json.load(urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?about:blank", method="PUT")))
                target = info["webSocketDebuggerUrl"]
            ws = await websockets.connect(target, max_size=None)
            tabs[name] = ws
            return ws

        async def cmd(ws, method: str, **params):
            counter[0] += 1
            n = counter[0]
            await ws.send(json.dumps({"id": n, "method": method, "params": params}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == n:
                    if "error" in msg:
                        raise RuntimeError(msg["error"])
                    return msg.get("result", {})

        saved: dict[str, str] = {}
        ws = await open_tab("principal")
        await cmd(ws, "Page.enable")
        for s in steps:
            if "pestana" in s:
                ws = tabs.get(s["pestana"]) or await open_tab(s["pestana"], "nueva")
                await cmd(ws, "Page.enable")
                await cmd(ws, "Page.bringToFront")  # las pestañas de fondo pausan sus temporizadores
            if "tam" in s:
                w, h, scale, mobile = s["tam"]
                await cmd(ws, "Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=scale, mobile=mobile)
                await cmd(ws, "Emulation.setTouchEmulationEnabled", enabled=bool(mobile))
            if "ir" in s:
                await cmd(ws, "Page.navigate", url=s["ir"])
                await asyncio.sleep(s.get("pausa", 3))
            if "js" in s:
                expr = s["js"]
                for k, v in saved.items():
                    expr = expr.replace("{{" + k + "}}", v)
                r = await cmd(ws, "Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)
                value = r.get("result", {}).get("value")
                if "guardar" in s:
                    saved[s["guardar"]] = str(value)
                print("js:", json.dumps(value, ensure_ascii=False)[:900])
            if "esperar" in s:
                await asyncio.sleep(s["esperar"])
            if "foto" in s:
                extra = {}
                if "elemento" in s:  # recortar a un elemento (selector CSS) con un margen de 8 px
                    q = json.dumps(s["elemento"])
                    box = (await cmd(ws, "Runtime.evaluate", returnByValue=True, expression=f"(()=>{{const e=document.querySelector({q});e.scrollIntoView({{block:'center'}});const r=e.getBoundingClientRect();return {{x:r.left+scrollX-8,y:r.top+scrollY-8,width:r.width+16,height:r.height+16}}}})()"))["result"]["value"]
                    extra = {"clip": {**box, "scale": 1}, "captureBeyondViewport": True}
                r = await cmd(ws, "Page.captureScreenshot", format="png", **({"captureBeyondViewport": bool(s.get("completa"))} | extra))
                out = ROOT / s["foto"]
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(base64.b64decode(r["data"]))
                print("foto:", out)
        for t in tabs.values():
            await t.close()
    finally:
        proc.terminate()


if __name__ == "__main__":
    asyncio.run(run(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))))
