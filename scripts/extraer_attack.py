"""Extrae del paquete STIX oficial de MITRE ATT&CK los nombres de las técnicas usadas
por el catálogo de ScriptLens y los guarda en backend/scripts/data/attack_subset.json.

Uso (PowerShell, desde la raíz del repositorio):
    .\\.venv\\Scripts\\python scripts\\extraer_attack.py <ruta a enterprise-attack.json>

Fuente: https://github.com/mitre-attack/attack-stix-data (enterprise-attack.json).
ATT&CK® es una marca registrada de The MITRE Corporation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.scripts.catalog import RULES  # noqa: E402


def main(bundle_path: str) -> None:
    bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
    wanted = {r.attack for r in RULES if r.attack != "-"}
    version = next((o.get("x_mitre_version") for o in bundle["objects"] if o.get("type") == "x-mitre-collection"), None)
    techniques = {}
    for o in bundle["objects"]:
        if o.get("type") != "attack-pattern" or o.get("revoked") or o.get("x_mitre_deprecated"):
            continue
        ext = next((r for r in o.get("external_references", []) if r.get("source_name") == "mitre-attack"), None)
        if not ext or ext.get("external_id") not in wanted:
            continue
        tid = ext["external_id"]
        techniques[tid] = {
            "id": tid,
            "nombre": o["name"],
            "tacticas": [p["phase_name"] for p in o.get("kill_chain_phases", []) if p.get("kill_chain_name") == "mitre-attack"],
            "url": ext.get("url"),
        }
    missing = sorted(wanted - set(techniques))
    out = {
        "fuente": "https://github.com/mitre-attack/attack-stix-data (enterprise-attack.json)",
        "version_attack": version,
        "aviso": "ATT&CK® es una marca registrada de The MITRE Corporation. Uso conforme a su licencia, con atribución.",
        "tecnicas": dict(sorted(techniques.items())),
        "no_encontradas": missing,
    }
    dest = ROOT / "backend" / "scripts" / "data" / "attack_subset.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ATT&CK {version}: {len(techniques)} técnicas guardadas; no encontradas: {missing}")


if __name__ == "__main__":
    main(sys.argv[1])
