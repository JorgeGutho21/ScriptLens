"""Cliente de prueba del acceso remoto: simula un segundo dispositivo de la red local.

Uso (PowerShell, desde la raíz del repositorio):
    .\\.venv\\Scripts\\python scripts\\probar_remoto.py https://192.168.1.20:8765 123456 --huella F3:03:1E:CF

1. Se conecta por HTTPS y compara la huella del certificado con la que muestra la PC.
2. Envía el código temporal y espera a que el propietario autorice en la PC.
3. Consulta datos (solo lectura) e intenta operaciones prohibidas para demostrar que se rechazan.
No guarda la credencial de sesión en disco ni la imprime.
"""

from __future__ import annotations

import argparse
import http.client
import json
import ssl
import sys
import time
from urllib.parse import urlparse

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from backend.remote.tls import fingerprint_der  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("codigo")
    ap.add_argument("--huella", default="", help="primeros bytes de la huella que muestra la PC")
    ap.add_argument("--nombre", default="Dispositivo de prueba")
    a = ap.parse_args()
    u = urlparse(a.url)
    ctx = ssl.create_default_context()
    ctx.check_hostname, ctx.verify_mode = False, ssl.CERT_NONE  # la autenticidad se comprueba con la huella

    def call(method, path, body=None, token=None):
        c = http.client.HTTPSConnection(u.hostname, u.port or 443, context=ctx, timeout=10)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        c.request(method, path, json.dumps(body) if body is not None else None, headers)
        r = c.getresponse()
        fp = fingerprint_der(c.sock.getpeercert(binary_form=True))
        data = r.read()
        c.close()
        try:
            return r.status, json.loads(data), fp
        except ValueError:
            return r.status, data[:80], fp

    st, body, fp = call("GET", "/remote/api/overview")
    print(f"Sin sesión: HTTP {st} (esperado 401). Huella del servidor: {fp}")
    if a.huella and not fp.startswith(a.huella.upper()):
        print("¡La huella NO coincide con la que muestra la PC! Se cancela.")
        return 2
    st, body, _ = call("POST", "/remote/api/pair/request", {"codigo": a.codigo, "nombre": a.nombre, "tipo": "consola"})
    if st != 200:
        print("Vinculación rechazada:", st, body)
        return 1
    print(f"Solicitud enviada a {body['equipo']}. Autorice en la PC si ve la frase: {body['frase']}")
    token = None
    for _ in range(150):
        time.sleep(2)
        st, body2, _ = call("GET", f"/remote/api/pair/status?solicitud={body['solicitud']}")
        if body2.get("estado") == "autorizada":
            token = body2["token"]
            break
        if body2.get("estado") in ("rechazada", "caducada"):
            print("Solicitud", body2["estado"])
            return 1
    if not token:
        return 1
    st, o, _ = call("GET", "/remote/api/overview", token=token)
    s = o["actual"]
    print(f"HTTP {st} · {o['equipo']} · {o['so']} · CPU {s['cpu_percent']} % · RAM {s['mem_percent']} % · encendido {o['tiempo_encendido_s'] // 3600} h")
    st, p, _ = call("GET", "/remote/api/processes?by=memory&limit=3", token=token)
    print("Procesos:", st, [x["nombre"] for x in p.get("programas", [])] if isinstance(p, dict) else p)
    for method, path in (("POST", "/api/actions/terminate"), ("POST", "/api/settings"), ("DELETE", "/api/privacy/actions"), ("POST", "/api/assistant/ask"), ("GET", "/api/remote/status")):
        st, _, _ = call(method, path, {}, token=token)
        print(f"Prohibido {method} {path}: HTTP {st}")
    call("POST", "/remote/api/logout", token=token)
    st, _, _ = call("GET", "/remote/api/overview", token=token)
    print(f"Tras cerrar la sesión: HTTP {st} (esperado 401)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
