"""Lectura masiva de procesos en Windows mediante NtQuerySystemInformation.

Concepto adoptado de System Informer (winsiderss/systeminformer, MIT): en lugar
de abrir un handle por proceso (≈2 ms cada uno y AccessDenied en procesos
protegidos), una sola llamada a ``NtQuerySystemInformation(SystemProcessInformation)``
devuelve nombre, PID, PID padre, hora de creación, tiempos de CPU, conjunto de
trabajo y número de hilos de todos los procesos, sin requerir privilegios.

Implementación propia en ctypes; no se copia código de System Informer.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from dataclasses import dataclass

IS_WINDOWS = sys.platform == "win32"
_SystemProcessInformation = 5
_STATUS_INFO_LENGTH_MISMATCH = 0xC0000004
_EPOCH_AS_FILETIME = 116444736000000000  # 1601-01-01 → 1970-01-01 en unidades de 100 ns


class _UNICODE_STRING(ctypes.Structure):
    _fields_ = [("Length", wintypes.USHORT), ("MaximumLength", wintypes.USHORT), ("Buffer", ctypes.c_void_p)]


class _SYSTEM_PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("NextEntryOffset", wintypes.ULONG),
        ("NumberOfThreads", wintypes.ULONG),
        ("WorkingSetPrivateSize", ctypes.c_longlong),
        ("HardFaultCount", wintypes.ULONG),
        ("NumberOfThreadsHighWatermark", wintypes.ULONG),
        ("CycleTime", ctypes.c_ulonglong),
        ("CreateTime", ctypes.c_longlong),
        ("UserTime", ctypes.c_longlong),
        ("KernelTime", ctypes.c_longlong),
        ("ImageName", _UNICODE_STRING),
        ("BasePriority", wintypes.LONG),
        ("UniqueProcessId", ctypes.c_void_p),
        ("InheritedFromUniqueProcessId", ctypes.c_void_p),
        ("HandleCount", wintypes.ULONG),
        ("SessionId", wintypes.ULONG),
        ("UniqueProcessKey", ctypes.c_size_t),
        ("PeakVirtualSize", ctypes.c_size_t),
        ("VirtualSize", ctypes.c_size_t),
        ("PageFaultCount", wintypes.ULONG),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivatePageCount", ctypes.c_size_t),
    ]


@dataclass(frozen=True)
class RawProcess:
    pid: int
    ppid: int
    name: str
    create_time: float | None  # segundos Unix
    cpu_time_100ns: int  # usuario + núcleo, acumulado
    working_set: int  # bytes (equivale a rss de psutil)
    private_bytes: int  # bytes confirmados privados
    threads: int
    handles: int
    session_id: int


def _filetime_to_unix(ft: int) -> float | None:
    if ft <= 0:
        return None
    return (ft - _EPOCH_AS_FILETIME) / 1e7


def snapshot() -> list[RawProcess]:
    """Devuelve todos los procesos con una única llamada al sistema."""
    if not IS_WINDOWS:
        raise OSError("NtQuerySystemInformation solo está disponible en Windows")
    ntdll = ctypes.WinDLL("ntdll")
    query = ntdll.NtQuerySystemInformation
    query.restype = wintypes.LONG
    query.argtypes = [wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG, ctypes.POINTER(wintypes.ULONG)]

    size = 512 * 1024
    for _ in range(8):
        buf = ctypes.create_string_buffer(size)
        needed = wintypes.ULONG(0)
        status = query(_SystemProcessInformation, buf, size, ctypes.byref(needed)) & 0xFFFFFFFF
        if status == _STATUS_INFO_LENGTH_MISMATCH:
            size = max(size * 2, needed.value + 64 * 1024)  # la lista puede crecer entre llamadas
            continue
        if status != 0:
            raise OSError(f"NtQuerySystemInformation falló: 0x{status:08X}")
        break
    else:
        raise OSError("No fue posible reservar memoria para la lista de procesos")

    base = ctypes.addressof(buf)
    offset = 0
    result: list[RawProcess] = []
    while True:
        info = _SYSTEM_PROCESS_INFORMATION.from_address(base + offset)
        pid = info.UniqueProcessId or 0
        if info.ImageName.Buffer and info.ImageName.Length:
            name = ctypes.wstring_at(info.ImageName.Buffer, info.ImageName.Length // 2)
        else:
            name = "System Idle Process" if pid == 0 else ""
        result.append(
            RawProcess(
                pid=pid,
                ppid=info.InheritedFromUniqueProcessId or 0,
                name=name,
                create_time=_filetime_to_unix(info.CreateTime),
                cpu_time_100ns=info.UserTime + info.KernelTime,
                working_set=info.WorkingSetSize,
                private_bytes=info.PrivatePageCount,
                threads=info.NumberOfThreads,
                handles=info.HandleCount,
                session_id=info.SessionId,
            )
        )
        if info.NextEntryOffset == 0:
            break
        offset += info.NextEntryOffset
    return result
