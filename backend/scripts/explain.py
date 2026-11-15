"""Explicaciones línea por línea en lenguaje sencillo."""

from __future__ import annotations

import re

from .catalog import is_comment

# Comandos frecuentes sin implicaciones de riesgo (explicación genérica).
_COMUNES = [
    (r"^@?echo\s+off\b", "Oculta el eco de los comandos en la consola (no afecta al equipo)."),
    (r"^@?echo\b", "Muestra un mensaje en la pantalla."),
    (r"^title\b", "Cambia el título de la ventana de la consola."),
    (r"^cls\b|^Clear-Host\b", "Limpia la pantalla de la consola."),
    (r"^pause\b", "Espera a que el usuario pulse una tecla."),
    (r"^timeout\b|^Start-Sleep\b", "Espera unos segundos antes de continuar."),
    (r"^set\s+/p\b|^Read-Host\b", "Pide un dato al usuario."),
    (r"^set\b|^\$[\w:]+\s*=", "Guarda un valor en una variable."),
    (r"^setlocal\b|^endlocal\b", "Limita las variables al script (no cambia el sistema)."),
    (r"^chcp\b", "Cambia la página de códigos de la consola para mostrar acentos."),
    (r"^cd\b|^chdir\b|^pushd\b|^popd\b|^Set-Location\b", "Cambia la carpeta de trabajo."),
    (r"^if\b", "Ejecuta algo solo si se cumple una condición."),
    (r"^for\b|^foreach\b|^while\b|^do\b", "Repite instrucciones (bucle)."),
    (r"^goto\b", "Salta a otra parte del script."),
    (r"^call\b", "Ejecuta otra parte del script o otro script y luego regresa."),
    (r"^exit\b", "Termina el script."),
    (r"^:\w+", "Etiqueta: marca un punto al que el script puede saltar."),
    (r"^function\b", "Define una función reutilizable."),
    (r"^param\b", "Declara los parámetros que recibe el script."),
    (r"^Write-(Host|Output|Verbose)\b", "Muestra un mensaje en la pantalla."),
    (r"^try\b|^catch\b|^finally\b", "Maneja errores para que el script no se detenga de forma brusca."),
    (r"^[{}()]+$", "Delimita un bloque de instrucciones."),
    (r"^Import-Module\b", "Carga un módulo de PowerShell."),
    (r"^date\b|^time\b", "Muestra la fecha u hora."),
    (r"^ver\b", "Muestra la versión de Windows."),
    (r"^hostname\b", "Muestra el nombre del equipo."),
    (r"^type\b|^more\b|^Get-Content\b", "Muestra el contenido de un archivo."),
    (r"^findstr\b|^find\b|^Select-String\b|^Where-Object\b|^Select-Object\b|^Sort-Object\b|^Format-", "Filtra u ordena información."),
    (r"^start\b|^Start-Process\b", "Abre otro programa o archivo."),
]
_COMUNES_RX = [(re.compile(p, re.I), e) for p, e in _COMUNES]


def explain_lines(texto: str, findings: list[dict], tipo: str) -> list[dict]:
    by_line: dict[int, list[dict]] = {}
    for f in findings:
        by_line.setdefault(f["linea"], []).append(f)
    out = []
    for n, raw in enumerate(texto.splitlines(), start=1):
        s = raw.strip()
        if not s:
            continue
        if is_comment(raw) or s.startswith("<#"):
            out.append({"linea": n, "codigo": s[:200], "tipo": "comentario", "operacion": None, "explicacion": "Comentario: texto para personas, no se ejecuta."})
            continue
        hits = by_line.get(n, [])
        if hits:
            ops = {h["operacion"] for h in hits}
            op = "sensible" if "sensible" in ops else ("modificacion" if "modificacion" in ops else "consulta")
            exp = " · ".join(dict.fromkeys(h["explicacion"] for h in hits))
            out.append({"linea": n, "codigo": s[:200], "tipo": "regla", "operacion": op, "explicacion": exp + ".", "reglas": [h["regla"] for h in hits]})
            continue
        cmd = s.lstrip("@")
        exp = next((e for rx, e in _COMUNES_RX if rx.search(cmd)), None)
        out.append(
            {
                "linea": n,
                "codigo": s[:200],
                "tipo": "comun" if exp else "no_catalogado",
                "operacion": "consulta" if exp else None,
                "explicacion": exp or "Instrucción no incluida en el catálogo; ScriptLens no puede explicar con certeza qué hace.",
            }
        )
    return out
