"""Punto de entrada para empaquetar el motor con PyInstaller (scriptlens-backend.exe)."""

import multiprocessing
import sys

from backend.__main__ import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
