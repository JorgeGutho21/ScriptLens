# Avisos de terceros

ScriptLens IA se distribuye bajo licencia MIT. Incluye o utiliza los siguientes componentes, cada uno bajo su propia licencia. Las versiones corresponden a `backend/requirements.txt`, `frontend/package.json` y `src-tauri/Cargo.toml`.

## Componentes incluidos en el instalador

| Componente | Licencia | Uso |
|---|---|---|
| [psutil](https://github.com/giampaolo/psutil) | BSD-3-Clause | Métricas del sistema, servicios y respaldo de lectura de procesos |
| [FastAPI](https://github.com/fastapi/fastapi) · [Starlette](https://github.com/encode/starlette) | MIT · BSD-3-Clause | API local |
| [Pydantic](https://github.com/pydantic/pydantic) | MIT | Validación de parámetros |
| [Uvicorn](https://github.com/encode/uvicorn) | BSD-3-Clause | Servidor HTTP local |
| [scikit-learn](https://github.com/scikit-learn/scikit-learn) | BSD-3-Clause | TF-IDF, regresión logística, validación cruzada |
| [NumPy](https://github.com/numpy/numpy) · [SciPy](https://github.com/scipy/scipy) | BSD-3-Clause | Cálculo numérico (dependencias de scikit-learn) |
| [joblib](https://github.com/joblib/joblib) | BSD-3-Clause | Guardar y cargar el modelo |
| [reportlab](https://www.reportlab.com/opensource/) | BSD | Informes PDF |
| [cryptography](https://github.com/pyca/cryptography) | Apache-2.0 o BSD-3-Clause | Certificado TLS propio del acceso remoto |
| [Qwen3 1.7B](https://ollama.com/library/qwen3) (opcional, se descarga con Ollama) | Apache-2.0 | Modo «IA rápida» del asistente; no se distribuye con ScriptLens |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) (bootloader) | GPL-2.0 con excepción de bootloader | Empaquetado del motor; la excepción permite distribuir programas empaquetados bajo cualquier licencia |
| [Tauri](https://github.com/tauri-apps/tauri) · [tauri-plugin-single-instance](https://github.com/tauri-apps/plugins-workspace) | MIT / Apache-2.0 | Contenedor de escritorio, instalador NSIS, instancia única |
| [NSIS](https://nsis.sourceforge.io/) | zlib/libpng | Instalador de Windows |
| [React](https://github.com/facebook/react) | MIT | Interfaz |
| [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) | MIT | Estilos |
| [Lucide](https://github.com/lucide-icons/lucide) | ISC | Iconos |
| [three.js](https://github.com/mrdoob/three.js) | MIT | Elemento 3D |

Las dependencias transitivas de Rust y npm conservan sus licencias en los respectivos paquetes.

## Herramientas externas utilizadas (no incluidas)

| Herramienta | Licencia | Uso |
|---|---|---|
| [Ollama](https://github.com/ollama/ollama) | MIT | Ejecución local del modelo de lenguaje (instalación opcional por el usuario) |
| [Qwen3 4B Instruct](https://ollama.com/library/qwen3) | Apache-2.0 | Modelo de lenguaje descargado por Ollama con autorización del usuario |
| Windows PowerShell, Microsoft Defender, WinGet | Componentes de Windows | Consultas de solo lectura |

## Datos de terceros

**MITRE ATT&CK®**: nombres y tácticas de 30 técnicas extraídos de [mitre-attack/attack-stix-data](https://github.com/mitre-attack/attack-stix-data) (ATT&CK 20.1) en `backend/scripts/data/attack_subset.json`. ATT&CK® es una marca registrada de The MITRE Corporation; se usa conforme a su licencia, que permite el uso para investigación, desarrollo y fines comerciales con atribución.

## Proyectos usados como referencia conceptual (sin código copiado)

| Proyecto | Licencia | Concepto adoptado |
|---|---|---|
| [System Informer](https://github.com/winsiderss/systeminformer) | MIT | Enumeración de procesos con `NtQuerySystemInformation` en una sola llamada |
| [Glances](https://github.com/nicolargo/glances) | LGPL-3.0 | Umbrales por niveles y promedio en ventana |
| [osquery](https://github.com/osquery/osquery) | Apache-2.0 / GPL-2.0 | Auditoría organizada como fuentes de solo lectura |
| [PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer) | MIT | Catálogo de reglas de riesgo en PowerShell |
| [PowerDetect](https://github.com/KyootyBella/PowerDetect) | MIT | Señales de ofuscación |
| [MaliciousPowerShellDetector](https://github.com/Arjunren/MaliciousPowerShellDetector) | MIT | Metodología TF-IDF + modelo lineal |
| [WinGet](https://github.com/microsoft/winget-cli) | MIT | Referencia para métodos oficiales de instalación y desinstalación |

## Proyecto académico de origen

El catálogo de 24 reglas, el pipeline de clasificación, el generador de corpus y la política híbrida provienen del proyecto académico del propio autor, «ScriptLens IA — Guía de implementación 03B» (Jorge Gutiérrez, Universidad Popular del Cesar, 2026). El concepto de verificación cifra por cifra proviene de su proyecto «BitácoraIA» (guía 02B).
