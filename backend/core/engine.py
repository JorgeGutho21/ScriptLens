"""Motor: coordina los hilos de medición y los componentes compartidos."""

from __future__ import annotations

import os
import threading
import time

import psutil

from backend.monitoring.sampler import SystemSampler, system_info
from backend.processes.analysis import PathCache
from backend.processes.collector import ProcessMonitor
from backend.processes.signatures import SignatureCache
from backend.storage.db import Database

from .config import Settings


class Engine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.sampler = SystemSampler(settings.history_seconds, settings.sample_interval)
        self.processes = ProcessMonitor(settings.history_seconds)
        self.paths = PathCache()
        self.signatures = SignatureCache()
        self.db = Database(settings.data_dir / "scriptlens.db")
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self._info_cache: tuple[float, dict] | None = None
        self.own_pids = self._own_pids()

    @staticmethod
    def _own_pids() -> set[int]:
        """PID del motor y de su proceso padre (la aplicación o el lanzador del entorno virtual)."""
        pids = {os.getpid()}
        try:
            parent = psutil.Process().parent()
            if parent:
                pids.add(parent.pid)
        except psutil.Error:
            pass
        parent_env = os.environ.get("SCRIPTLENS_PARENT_PID", "")
        if parent_env.isdigit():
            pids.add(int(parent_env))
        return pids

    def start(self) -> None:
        self.signatures.start()
        self._threads = [
            threading.Thread(target=self._loop, args=(self.sampler.take, self.settings.sample_interval), daemon=True, name="sl-sampler"),
            threading.Thread(target=self._loop, args=(self._sample_processes, self.settings.process_interval), daemon=True, name="sl-procs"),
        ]
        for t in self._threads:
            t.start()

    def _sample_processes(self) -> None:
        snaps = self.processes.sample()
        self.paths.update(snaps)

    def stop(self) -> None:
        self._stop.set()
        self.signatures.stop()

    def _loop(self, fn, interval: float) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            try:
                fn()
            except Exception:  # noqa: BLE001 — un fallo puntual no debe detener el monitoreo
                pass
            self._stop.wait(max(0.05, interval - (time.monotonic() - started)))

    # Enlaces con el módulo de seguridad (fase 4). Devuelven None si aún no hay datos.
    def detections_for(self, path: str | None) -> list | None:
        return None

    def autostart_for(self, path: str | None) -> list | None:
        return None

    def info(self) -> dict:
        # El uso de discos cambia lentamente; se cachea 30 s.
        now = time.monotonic()
        if self._info_cache is None or now - self._info_cache[0] > 30:
            self._info_cache = (now, system_info())
        return self._info_cache[1]
