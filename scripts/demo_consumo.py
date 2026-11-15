"""DEMOSTRACIÓN CONTROLADA de consumo elevado de CPU para ExpoSoftware.

Ocupa los núcleos indicados durante un tiempo limitado y luego termina solo.
No escribe archivos, no usa la red y no modifica el sistema. Ctrl+C lo detiene.

Uso (PowerShell, raíz del repositorio):
    .\\.venv\\Scripts\\python scripts\\demo_consumo.py --nucleos 4 --segundos 90
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import time


def busy(until: float) -> None:
    x = 0
    while time.time() < until:
        x = (x * 1103515245 + 12345) % 2**31


def main() -> None:
    ap = argparse.ArgumentParser(description="Carga de CPU controlada para la demostración de ScriptLens IA")
    ap.add_argument("--nucleos", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--segundos", type=int, default=90)
    a = ap.parse_args()
    n = max(1, min(a.nucleos, os.cpu_count() or 1))
    segundos = max(5, min(a.segundos, 600))
    until = time.time() + segundos
    print(f"Demostración: {n} núcleo(s) ocupados durante {segundos} s (PID {os.getpid()}). Ctrl+C para detener.")
    procs = [mp.Process(target=busy, args=(until,), daemon=True) for _ in range(n)]
    for p in procs:
        p.start()
    try:
        for p in procs:
            p.join()
    except KeyboardInterrupt:
        for p in procs:
            p.terminate()
    print("Demostración terminada.")


if __name__ == "__main__":
    main()
