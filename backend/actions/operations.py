"""Acciones supervisadas sobre el sistema.

Garantías:
- Ninguna acción se ejecuta sin un token de confirmación emitido por «preparar»
  y usado una sola vez dentro de 60 segundos (confirmación explícita en la interfaz).
- La identidad del proceso (PID + hora de creación + nombre) se verifica de nuevo
  inmediatamente antes de actuar: si Windows reutilizó el PID, la acción se cancela.
- Procesos críticos, de seguridad, servicios de Windows (sesión 0) y la propia
  ScriptLens no pueden finalizarse.
- Se prioriza la alternativa menos invasiva: «Solicitar cierre» antes que «Finalizar»;
  desactivar un inicio automático (reversible) en lugar de borrarlo.
- No se desactiva el antivirus, el firewall ni las actualizaciones; no se borran
  archivos fuera de la carpeta temporal del usuario.
- El asistente de IA no tiene acceso a este módulo.
"""

from __future__ import annotations

import os
import secrets
import struct
import threading
import time
import winreg
from dataclasses import dataclass, field
from pathlib import Path

import psutil

from backend.processes.analysis import can_terminate
from backend.processes.winapi import post_close, window_handles
from backend.security.collect import _APPROVED, startup_entries

TOKEN_TTL = 60.0
TEMP_MIN_AGE_DAYS = 7


class ActionError(Exception):
    pass


@dataclass
class Pending:
    kind: str
    params: dict
    resumen: str
    created: float = field(default_factory=time.time)


class ActionManager:
    def __init__(self, engine):
        self.engine = engine
        self._pending: dict[str, Pending] = {}
        self._lock = threading.Lock()

    # --- Confirmación en dos pasos --------------------------------------
    def _issue(self, kind: str, params: dict, resumen: str) -> str:
        token = secrets.token_urlsafe(24)
        with self._lock:
            now = time.time()
            self._pending = {k: v for k, v in self._pending.items() if now - v.created < TOKEN_TTL}
            self._pending[token] = Pending(kind, params, resumen)
        return token

    def _consume(self, token: str) -> Pending:
        with self._lock:
            p = self._pending.pop(token, None)
        if p is None or time.time() - p.created > TOKEN_TTL:
            raise ActionError("La confirmación expiró o ya se usó. Vuelva a solicitar la acción.")
        return p

    # --- Mediciones antes / después --------------------------------------
    def _metrics(self) -> dict:
        window = self.engine.sampler.history(10)
        if not window:
            return {}
        return {
            "cpu_10s": round(sum(s.cpu_percent for s in window) / len(window), 1),
            "ram_percent": window[-1].mem_percent,
            "ram_used": window[-1].mem_used,
            "procesos": window[-1].process_count,
            "medido_en": window[-1].ts,
        }

    def _record_after(self, action_id: int, delay: float = 12.0) -> None:
        def later():
            time.sleep(delay)
            after = self._metrics()
            import json

            self.engine.db.execute("UPDATE actions SET after_json = ? WHERE id = ?", (json.dumps(after), action_id))

        threading.Thread(target=later, daemon=True, name="sl-after").start()

    # --- Procesos ----------------------------------------------------------
    def _verify_process(self, pid: int, create_time: float, name: str) -> psutil.Process:
        try:
            p = psutil.Process(pid)
            ct, pname = p.create_time(), p.name()
        except psutil.NoSuchProcess as e:
            raise ActionError("El proceso ya no existe.") from e
        except psutil.AccessDenied as e:
            raise ActionError("Windows no permite acceder a este proceso.") from e
        if abs(ct - create_time) > 0.5 or pname.lower() != name.lower():
            raise ActionError("La identidad del proceso cambió (Windows pudo reutilizar el PID). La acción se canceló por seguridad.")
        allowed, reason = can_terminate(pname, pid, self.engine.own_pids)
        if not allowed:
            raise ActionError(reason)
        snap = self.engine.processes.find(pid)
        if snap is not None and snap.session_id == 0:
            raise ActionError("Es un servicio de Windows. Para detenerlo use la consola «Servicios» de Windows; ScriptLens no detiene servicios.")
        return p

    def prepare_process(self, kind: str, pid: int, create_time: float, name: str) -> dict:
        p = self._verify_process(pid, create_time, name)
        mem = p.memory_info().rss
        if kind == "cerrar":
            if not window_handles(pid):
                raise ActionError("Este proceso no tiene ventanas abiertas; no es posible solicitar un cierre normal.")
            resumen = f"Se pedirá a «{name}» que se cierre, como si pulsara la X de su ventana. El programa podrá pedirle guardar cambios."
            advertencias = []
        else:
            resumen = f"Se finalizará «{name}» (PID {pid}) de forma inmediata, sin que pueda guardar su trabajo."
            advertencias = ["Los cambios sin guardar se perderán.", "Si el programa es necesario para otra aplicación, esta podría fallar.", "Prefiera «Solicitar cierre» si el programa tiene ventana."]
        token = self._issue(kind, {"pid": pid, "create_time": create_time, "name": name}, resumen)
        return {"token": token, "resumen": resumen, "advertencias": advertencias, "memoria_actual": mem, "expira_en": TOKEN_TTL}

    def _exec_process(self, p: Pending) -> dict:
        prm = p.params
        before = self._metrics()
        try:
            proc = self._verify_process(prm["pid"], prm["create_time"], prm["name"])  # revalidación inmediata
        except ActionError as e:
            self.engine.db.log_action(p.kind, prm["name"], "cancelada", str(e), before)
            raise
        if p.kind == "cerrar":
            sent = sum(post_close(h) for h in window_handles(prm["pid"]))
            try:
                proc.wait(timeout=6)
                result, detail = "completada", "El programa se cerró."
            except psutil.TimeoutExpired:
                result, detail = "solicitada", f"Se envió la solicitud a {sent} ventana(s); el programa sigue abierto (puede estar esperando que guarde)."
        else:
            try:
                proc.terminate()
                proc.wait(timeout=6)
                result, detail = "completada", "El proceso se finalizó."
            except psutil.AccessDenied:
                result, detail = "fallida", "Windows denegó el permiso para finalizar el proceso."
            except psutil.TimeoutExpired:
                result, detail = "fallida", "El proceso no terminó en 6 segundos."
            except psutil.NoSuchProcess:
                result, detail = "completada", "El proceso ya había terminado."
        aid = self.engine.db.log_action(p.kind, f"{prm['name']} (PID {prm['pid']})", result, detail, before)
        self._record_after(aid)
        return {"resultado": result, "detalle": detail, "accion_id": aid}

    # --- Inicio automático ---------------------------------------------------
    def prepare_startup(self, entry_id: str, enable: bool) -> dict:
        entry = next((e for e in startup_entries() if e["id"] == entry_id), None)
        if entry is None:
            raise ActionError("La entrada de inicio ya no existe.")
        if not entry["modificable_sin_admin"]:
            raise ActionError("Esta entrada pertenece a todos los usuarios del equipo; cambiarla requiere permisos de administrador. Use Configuración → Aplicaciones → Inicio.")
        if entry["habilitado"] == enable:
            raise ActionError("La entrada ya está en ese estado.")
        verbo = "activará" if enable else "desactivará"
        resumen = f"Se {verbo} el inicio automático de «{entry['nombre']}». No se desinstala ni se borra nada; puede revertirlo cuando quiera."
        token = self._issue("inicio", {"id": entry_id, "enable": enable, "scope": entry["scope"], "name": os.path.basename(entry["comando"]) if entry["scope"].startswith("FOLDER") else entry["nombre"]}, resumen)
        return {"token": token, "resumen": resumen, "advertencias": [] if enable else ["El programa ya no se abrirá solo al iniciar sesión; podrá abrirlo manualmente."], "expira_en": TOKEN_TTL}

    def _exec_startup(self, p: Pending) -> dict:
        prm = p.params
        hive, path = _APPROVED[prm["scope"]]
        if hive != winreg.HKEY_CURRENT_USER:
            raise ActionError("Solo se modifican entradas del usuario actual.")
        # Mismo formato que usa el Administrador de tareas: 02 = habilitado; 03 + FILETIME = deshabilitado.
        if prm["enable"]:
            value = bytes([2]) + bytes(11)
        else:
            ft = int((time.time() + 11644473600) * 1e7)
            value = bytes([3, 0, 0, 0]) + struct.pack("<Q", ft)
        with winreg.CreateKeyEx(hive, path, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, prm["name"], 0, winreg.REG_BINARY, value)
        result = "completada"
        detail = "Inicio automático " + ("activado." if prm["enable"] else "desactivado (reversible).")
        aid = self.engine.db.log_action("inicio_activar" if prm["enable"] else "inicio_desactivar", prm["id"], result, detail, self._metrics())
        return {"resultado": result, "detalle": detail, "accion_id": aid}

    # --- Archivos temporales -------------------------------------------------
    @staticmethod
    def temp_preview() -> dict:
        user_temp = Path(os.environ.get("TEMP", ""))
        cutoff = time.time() - TEMP_MIN_AGE_DAYS * 86400
        old_files, old_bytes, total_bytes, total_files = [], 0, 0, 0
        if user_temp.is_dir():
            for root, _dirs, files in os.walk(user_temp):
                for f in files:
                    fp = Path(root) / f
                    try:
                        st = fp.stat()
                    except OSError:
                        continue
                    total_files += 1
                    total_bytes += st.st_size
                    if st.st_mtime < cutoff:
                        old_bytes += st.st_size
                        old_files.append((str(fp), st.st_size))
        old_files.sort(key=lambda x: x[1], reverse=True)

        def size_of(path: Path) -> int | None:
            if not path.is_dir():
                return None
            total = 0
            try:
                for root, _d, files in os.walk(path):
                    for f in files:
                        try:
                            total += (Path(root) / f).stat().st_size
                        except OSError:
                            pass
            except OSError:
                return None
            return total

        return {
            "categorias": [
                {
                    "id": "temp_usuario",
                    "nombre": "Archivos temporales de su usuario con más de 7 días",
                    "ubicacion": str(user_temp),
                    "archivos": len(old_files),
                    "bytes": old_bytes,
                    "limpiable": True,
                    "nota": f"La carpeta contiene en total {total_files} archivos ({total_bytes} bytes). Solo se borran los que llevan más de {TEMP_MIN_AGE_DAYS} días sin cambios; los que estén en uso se omiten.",
                    "muestra": [os.path.basename(p) for p, _ in old_files[:12]],
                },
                {
                    "id": "temp_windows",
                    "nombre": "Temporales de Windows",
                    "ubicacion": r"C:\Windows\Temp",
                    "bytes": size_of(Path(r"C:\Windows\Temp")),
                    "limpiable": False,
                    "nota": "Requiere permisos de administrador. Use Configuración → Sistema → Almacenamiento → Archivos temporales.",
                },
                {
                    "id": "descargas",
                    "nombre": "Carpeta Descargas",
                    "ubicacion": str(Path.home() / "Downloads"),
                    "bytes": size_of(Path.home() / "Downloads"),
                    "limpiable": False,
                    "nota": "Puede contener documentos personales: ScriptLens nunca la limpia. Revísela usted mismo.",
                },
            ]
        }

    def prepare_temp(self) -> dict:
        prev = self.temp_preview()["categorias"][0]
        resumen = f"Se borrarán {prev['archivos']} archivos temporales de su usuario con más de {TEMP_MIN_AGE_DAYS} días ({prev['bytes']} bytes). No se tocan documentos ni carpetas del sistema."
        token = self._issue("temporales", {}, resumen)
        return {"token": token, "resumen": resumen, "advertencias": ["La eliminación es permanente (no pasa por la Papelera).", "Algunos programas podrían tener que volver a descargar datos de caché."], "expira_en": TOKEN_TTL}

    def _exec_temp(self, p: Pending) -> dict:
        user_temp = Path(os.environ.get("TEMP", "")).resolve()
        cutoff = time.time() - TEMP_MIN_AGE_DAYS * 86400
        deleted = skipped = freed = 0
        for root, _dirs, files in os.walk(user_temp):
            for f in files:
                fp = Path(root) / f
                try:
                    if not fp.resolve().is_relative_to(user_temp):  # nunca fuera de %TEMP%
                        skipped += 1
                        continue
                    st = fp.stat()
                    if st.st_mtime >= cutoff:
                        continue
                    fp.unlink()
                    deleted += 1
                    freed += st.st_size
                except OSError:
                    skipped += 1  # en uso o sin permiso
        detail = f"{deleted} archivos eliminados ({freed} bytes liberados); {skipped} omitidos por estar en uso o protegidos."
        aid = self.engine.db.log_action("limpiar_temporales", str(user_temp), "completada", detail, self._metrics(), {"eliminados": deleted, "bytes": freed, "omitidos": skipped})
        return {"resultado": "completada", "detalle": detail, "accion_id": aid, "eliminados": deleted, "bytes": freed}

    # --- Programas instalados -----------------------------------------------
    @staticmethod
    def installed_programs() -> list[dict]:
        roots = [
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall", "equipo"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", "equipo"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall", "usuario"),
        ]
        out, seen = [], set()
        for hive, path, ambito in roots:
            try:
                root = winreg.OpenKey(hive, path)
            except OSError:
                continue
            with root:
                for i in range(winreg.QueryInfoKey(root)[0]):
                    try:
                        sub = winreg.EnumKey(root, i)
                        with winreg.OpenKey(root, sub) as k:
                            vals = {}
                            for name in ("DisplayName", "Publisher", "DisplayVersion", "EstimatedSize", "InstallDate", "UninstallString", "SystemComponent", "ParentKeyName"):
                                try:
                                    vals[name] = winreg.QueryValueEx(k, name)[0]
                                except OSError:
                                    pass
                    except OSError:
                        continue
                    if not vals.get("DisplayName") or vals.get("SystemComponent") == 1 or vals.get("ParentKeyName"):
                        continue
                    key = (vals["DisplayName"], vals.get("DisplayVersion"))
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(
                        {
                            "id": f"{ambito}:{sub}",
                            "nombre": vals["DisplayName"],
                            "editor": vals.get("Publisher"),
                            "version": vals.get("DisplayVersion"),
                            "tamano_kb": vals.get("EstimatedSize"),
                            "instalado": vals.get("InstallDate"),
                            "ambito": ambito,
                            "desinstalable": bool(vals.get("UninstallString")),
                            "_uninstall": vals.get("UninstallString"),
                        }
                    )
        out.sort(key=lambda p: p["nombre"].lower())
        return out

    def prepare_uninstall(self, program_id: str) -> dict:
        prog = next((p for p in self.installed_programs() if p["id"] == program_id), None)
        if prog is None or not prog["desinstalable"]:
            raise ActionError("El programa no existe o no ofrece un desinstalador.")
        resumen = f"Se abrirá el desinstalador oficial de «{prog['nombre']}». ScriptLens no desinstala nada por sí misma: usted completará el proceso en la ventana del programa."
        token = self._issue("desinstalar", {"id": program_id, "nombre": prog["nombre"]}, resumen)
        return {
            "token": token,
            "resumen": resumen,
            "advertencias": ["Windows puede pedir permisos de administrador.", "Una desinstalación no siempre es reversible: podría tener que volver a instalar y configurar el programa."],
            "expira_en": TOKEN_TTL,
        }

    def _exec_uninstall(self, p: Pending) -> dict:
        prog = next((x for x in self.installed_programs() if x["id"] == p.params["id"]), None)
        if prog is None or not prog["_uninstall"]:
            raise ActionError("El programa ya no está instalado.")
        cmd = prog["_uninstall"].strip()
        # Se separa ejecutable y argumentos sin pasar por un intérprete de comandos.
        if cmd.startswith('"'):
            exe, _, args = cmd[1:].partition('"')
        else:
            exe, _, args = cmd.partition(" ")
        if exe.lower().endswith("msiexec.exe") or exe.lower() == "msiexec":
            args = args.replace("/I{", "/X{").replace("/i{", "/x{")  # algunos instaladores registran /I para «modificar»
        import ctypes

        rc = ctypes.windll.shell32.ShellExecuteW(None, "open", exe, args.strip() or None, None, 1)
        ok = rc > 32
        detail = "Se abrió el desinstalador oficial." if ok else f"Windows no pudo abrir el desinstalador (código {rc})."
        aid = self.engine.db.log_action("desinstalar", prog["nombre"], "solicitada" if ok else "fallida", detail, self._metrics())
        return {"resultado": "solicitada" if ok else "fallida", "detalle": detail, "accion_id": aid}

    # --- Ejecución -------------------------------------------------------------
    def execute(self, token: str) -> dict:
        p = self._consume(token)
        if p.kind in ("cerrar", "finalizar"):
            return self._exec_process(p)
        if p.kind == "inicio":
            return self._exec_startup(p)
        if p.kind == "temporales":
            return self._exec_temp(p)
        if p.kind == "desinstalar":
            return self._exec_uninstall(p)
        raise ActionError("Acción desconocida")
