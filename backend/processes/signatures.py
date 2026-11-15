"""Verificación de firmas digitales (Authenticode) y datos del editor.

Se usa ``Get-AuthenticodeSignature`` de Windows porque, a diferencia de una
llamada directa a ``WinVerifyTrust`` sobre el archivo, también valida los
binarios del sistema firmados mediante catálogo (la mayoría de los ejecutables
de Windows no llevan la firma incrustada).

Las rutas se verifican por lotes en un hilo de fondo y se guardan en caché por
(ruta, tamaño, fecha de modificación); un archivo cambiado se vuelve a verificar.
"""

from __future__ import annotations

import os
import re
import threading
import time
from dataclasses import dataclass

from backend.core.winps import PowerShellError, run_ps

_SCRIPT = r"""
$paths = [Console]::In.ReadToEnd() | ConvertFrom-Json
$out = foreach ($p in $paths) {
  $s = Get-AuthenticodeSignature -LiteralPath $p
  $v = (Get-Item -LiteralPath $p).VersionInfo
  [pscustomobject]@{
    path = $p
    status = [string]$s.Status
    signer = if ($s.SignerCertificate) { $s.SignerCertificate.Subject } else { $null }
    os_binary = [bool]$s.IsOSBinary
    company = $v.CompanyName
    description = $v.FileDescription
    product = $v.ProductName
    version = $v.FileVersion
  }
}
ConvertTo-Json -InputObject @($out) -Compress -Depth 3
"""

# Traducción de Get-AuthenticodeSignature.Status
STATUS_ES = {
    "Valid": ("valida", "Firma digital válida"),
    "NotSigned": ("sin_firma", "El archivo no tiene firma digital"),
    "HashMismatch": ("alterada", "El archivo fue modificado después de firmarse"),
    "NotTrusted": ("no_confiable", "Firmado con un certificado no confiable"),
    "UnknownError": ("desconocido", "No se pudo verificar la firma"),
    "NotSupportedFileFormat": ("no_aplica", "Formato de archivo sin firma Authenticode"),
}


def signer_name(subject: str | None) -> str | None:
    """Extrae el nombre legible (CN u O) del sujeto del certificado."""
    if not subject:
        return None
    for key in ("CN", "O"):
        m = re.search(rf"(?:^|,\s*){key}=(\"[^\"]+\"|[^,]+)", subject)
        if m:
            return m.group(1).strip('"')
    return subject


@dataclass
class SignatureInfo:
    path: str
    estado: str
    descripcion_estado: str
    firmante: str | None
    binario_windows: bool
    editor: str | None
    descripcion: str | None
    producto: str | None
    version: str | None
    verificado_en: float

    def to_dict(self) -> dict:
        return dict(self.__dict__)


def _file_key(path: str) -> tuple | None:
    try:
        st = os.stat(path)
        return (path.lower(), st.st_size, int(st.st_mtime))
    except OSError:
        return None


def verify_batch(paths: list[str]) -> list[SignatureInfo]:
    if not paths:
        return []
    raw = run_ps(_SCRIPT, paths, timeout=max(30.0, 0.5 * len(paths))) or []
    now = time.time()
    result = []
    for r in raw:
        estado, desc = STATUS_ES.get(r.get("status") or "", ("desconocido", "No se pudo verificar la firma"))
        result.append(
            SignatureInfo(
                path=r.get("path"),
                estado=estado,
                descripcion_estado=desc,
                firmante=signer_name(r.get("signer")),
                binario_windows=bool(r.get("os_binary")),
                editor=(r.get("company") or None),
                descripcion=(r.get("description") or None),
                producto=(r.get("product") or None),
                version=(r.get("version") or None),
                verificado_en=now,
            )
        )
    return result


class SignatureCache:
    """Caché de firmas con verificación en segundo plano."""

    BATCH = 40

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache: dict[tuple, SignatureInfo] = {}
        self._pending: dict[str, None] = {}
        self._event = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, daemon=True, name="sl-signatures")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._event.set()

    def get(self, path: str | None) -> SignatureInfo | None:
        if not path:
            return None
        key = _file_key(path)
        if key is None:
            return None
        with self._lock:
            info = self._cache.get(key)
            if info is None:
                self._pending[path] = None
                self._event.set()
        return info

    def request(self, paths) -> None:
        with self._lock:
            for p in paths:
                key = _file_key(p) if p else None
                if key and key not in self._cache:
                    self._pending[p] = None
        self._event.set()

    def verify_now(self, path: str) -> SignatureInfo | None:
        """Verificación inmediata (para el detalle de un proceso)."""
        key = _file_key(path)
        if key is None:
            return None
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        try:
            infos = verify_batch([path])
        except PowerShellError:
            return None
        with self._lock:
            for info in infos:
                self._cache[key] = info
        return infos[0] if infos else None

    def _loop(self) -> None:
        while not self._stop.is_set():
            self._event.wait(5.0)
            self._event.clear()
            with self._lock:
                batch = list(self._pending)[: self.BATCH]
                for p in batch:
                    self._pending.pop(p, None)
            if not batch:
                continue
            try:
                infos = verify_batch(batch)
            except PowerShellError:
                continue
            with self._lock:
                for info in infos:
                    key = _file_key(info.path)
                    if key:
                        self._cache[key] = info
            if self._pending:
                self._event.set()
