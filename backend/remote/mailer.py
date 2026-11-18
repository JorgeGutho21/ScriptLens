"""Envío de las invitaciones por correo.

Modos (variable de entorno ``SCRIPTLENS_MAIL_MODE``):

- ``local`` (predeterminado): el correo se guarda como archivo ``.eml`` en la carpeta de salida de
  ScriptLens. Sirve para probar sin cuentas ni claves; el propietario puede abrir el archivo con su
  programa de correo y reenviarlo, o copiar el enlace.
- ``smtp``: envío real por SMTP con STARTTLS. Los datos se leen de variables de entorno
  (``SCRIPTLENS_SMTP_HOST``, ``SCRIPTLENS_SMTP_PORT``, ``SCRIPTLENS_SMTP_USER``,
  ``SCRIPTLENS_SMTP_PASSWORD``, ``SCRIPTLENS_SMTP_FROM``). La contraseña nunca se guarda en la base
  de datos ni aparece en la interfaz o en los registros.
"""

from __future__ import annotations

import os
import smtplib
import ssl
import time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from html import escape
from pathlib import Path

PERM_TEXT = {
    "procesos": "los programas que más consumen (sin rutas ni usuarios)",
    "seguridad": "el resumen de seguridad de la última revisión",
    "estadisticas": "las estadísticas resumidas del día",
}


def build_message(*, to: str, sender: str, equipo: str, enlace: str, huella: str, caduca: float, horas: int, permisos: dict) -> EmailMessage:
    vence = time.strftime("%d/%m/%Y %H:%M", time.localtime(caduca))
    extra = [PERM_TEXT[k] for k, v in permisos.items() if v and k in PERM_TEXT]
    ve = "procesador, memoria, discos, red y tiempo encendido" + (", " + ", ".join(extra) if extra else "")
    text = f"""Hola:

Le han dado acceso de SOLO LECTURA al estado de la computadora «{equipo}» con ScriptLens IA.

Abra este enlace desde un dispositivo conectado a la MISMA red (WiFi, cable o hotspot) que esa computadora:

{enlace}

- Al abrirlo, escriba este mismo correo ({to}) para confirmar que es usted.
- El enlace sirve UNA sola vez y caduca el {vence}.
- Podrá ver: {ve}, durante {horas} hora(s).
- No podrá cerrar programas, cambiar ajustes ni ejecutar nada.
- El navegador avisará de un certificado propio de la PC. Continúe solo si la huella coincide:
  {huella}

Si no esperaba este correo, ignórelo: sin el enlace y su correo nadie puede entrar.

ScriptLens IA · Desarrollado por Jorge Gutiérrez · GitHub @JorgeGutho21
"""
    html = f"""<!doctype html><html lang="es"><body style="font-family:Segoe UI,Arial,sans-serif;color:#0f172a;line-height:1.5">
<p>Hola:</p>
<p>Le han dado acceso de <b>solo lectura</b> al estado de la computadora <b>{escape(equipo)}</b> con ScriptLens IA.</p>
<p><a href="{escape(enlace)}" style="display:inline-block;background:#2b68d8;color:#fff;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600">Ver el estado de {escape(equipo)}</a></p>
<ul>
<li>Ábralo desde un dispositivo en la <b>misma red</b> que esa computadora.</li>
<li>Escriba este mismo correo (<b>{escape(to)}</b>) para confirmar que es usted.</li>
<li>El enlace sirve <b>una sola vez</b> y caduca el {escape(vence)}.</li>
<li>Podrá ver: {escape(ve)}, durante {horas} hora(s). No podrá cambiar nada.</li>
<li>Huella del certificado de la PC: <code>{escape(huella)}</code></li>
</ul>
<p style="color:#475569">Si no esperaba este correo, ignórelo.</p>
<p style="color:#475569;font-size:12px">ScriptLens IA · Desarrollado por Jorge Gutiérrez · GitHub @JorgeGutho21</p>
</body></html>"""
    msg = EmailMessage()
    msg["Subject"] = f"Acceso de solo lectura a {equipo} con ScriptLens IA"
    msg["From"] = sender
    msg["To"] = to
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="scriptlens.local")
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    return msg


class LocalOutbox:
    mode = "local"

    def __init__(self, folder: Path):
        self.folder = folder
        self.sender = "ScriptLens IA <no-responder@scriptlens.local>"

    def send(self, msg: EmailMessage, ref: str) -> dict:
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / f"{time.strftime('%Y%m%d_%H%M%S')}_{ref}.eml"
        path.write_bytes(bytes(msg))
        return {"modo": self.mode, "archivo": str(path)}

    def list(self, limit: int = 20) -> list[dict]:
        if not self.folder.exists():
            return []
        files = sorted(self.folder.glob("*.eml"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
        return [{"archivo": str(p), "nombre": p.name, "fecha": p.stat().st_mtime} for p in files]


class SmtpMailer:
    mode = "smtp"

    def __init__(self, env=os.environ):
        self.host = env.get("SCRIPTLENS_SMTP_HOST", "")
        self.port = int(env.get("SCRIPTLENS_SMTP_PORT", "587"))
        self.user = env.get("SCRIPTLENS_SMTP_USER", "")
        self._password = env.get("SCRIPTLENS_SMTP_PASSWORD", "")
        self.sender = env.get("SCRIPTLENS_SMTP_FROM", self.user)
        if not (self.host and self.sender):
            raise ValueError("Faltan SCRIPTLENS_SMTP_HOST o SCRIPTLENS_SMTP_FROM.")

    def send(self, msg: EmailMessage, ref: str) -> dict:
        with smtplib.SMTP(self.host, self.port, timeout=20) as s:
            s.starttls(context=ssl.create_default_context())
            if self.user:
                s.login(self.user, self._password)
            s.send_message(msg)
        return {"modo": self.mode, "servidor": self.host}

    def list(self, limit: int = 20) -> list[dict]:
        return []


def create_mailer(folder: Path, env=os.environ):
    if env.get("SCRIPTLENS_MAIL_MODE", "local").lower() == "smtp":
        return SmtpMailer(env)
    return LocalOutbox(folder)
