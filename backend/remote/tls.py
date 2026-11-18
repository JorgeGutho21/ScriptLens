"""Certificado TLS propio del equipo para el acceso remoto en la red local.

No existe una autoridad de certificación para direcciones como 192.168.1.25, así que ScriptLens
genera un certificado autofirmado una sola vez y lo conserva en su carpeta de datos. La
autenticidad se comprueba con la **huella SHA-256** que la PC muestra en pantalla:

- El navegador del celular avisará de que el certificado no está firmado por una autoridad;
  la persona puede comparar la huella antes de continuar.
- La consola «Mis computadoras» fija la huella al vincular (TOFU) y rechaza cualquier otro
  certificado en conexiones posteriores.

La clave privada nunca sale del equipo; se guarda en la carpeta de datos del usuario.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import ipaddress
import socket
import ssl
from pathlib import Path

CERT_NAME = "remote-cert.pem"
KEY_NAME = "remote-key.pem"
VALID_DAYS = 825


def fingerprint_der(der: bytes) -> str:
    """Huella SHA-256 en el formato habitual de los navegadores (AA:BB:…)."""
    h = hashlib.sha256(der).hexdigest().upper()
    return ":".join(h[i : i + 2] for i in range(0, len(h), 2))


def short_fingerprint(fp: str) -> str:
    """Primeros 8 bytes de la huella, cómodos de comparar a simple vista."""
    return ":".join(fp.split(":")[:8])


def fingerprint_of_pem(cert_path: Path) -> str:
    return fingerprint_der(ssl.PEM_cert_to_DER_cert(cert_path.read_text(encoding="ascii")))


def ensure_certificate(folder: Path) -> tuple[Path, Path, str]:
    """Devuelve (certificado, clave, huella). Crea el par la primera vez o si caducó."""
    folder.mkdir(parents=True, exist_ok=True)
    cert_path, key_path = folder / CERT_NAME, folder / KEY_NAME
    if cert_path.exists() and key_path.exists() and not _expired(cert_path):
        return cert_path, key_path, fingerprint_of_pem(cert_path)

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    host = socket.gethostname() or "ScriptLens"
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"ScriptLens IA - {host}"[:64]), x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ScriptLens IA")])
    now = dt.datetime.now(dt.timezone.utc)
    san = [x509.DNSName(host), x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(minutes=5))
        .not_valid_after(now + dt.timedelta(days=VALID_DAYS))
        .add_extension(x509.SubjectAlternativeName(san), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(key, hashes.SHA256())
    )
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return cert_path, key_path, fingerprint_of_pem(cert_path)


def _expired(cert_path: Path) -> bool:
    try:
        from cryptography import x509

        cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
        return cert.not_valid_after_utc < dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=7)
    except Exception:  # noqa: BLE001 — un archivo dañado se regenera
        return True
