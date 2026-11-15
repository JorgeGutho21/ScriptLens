# Motor de análisis (backend)

Proceso Python que mide el equipo y expone una API local en `127.0.0.1` (puerto aleatorio, token aleatorio por arranque). En la aplicación instalada se ejecuta empaquetado como `scriptlens-backend.exe` y se cierra solo si la aplicación desaparece.

| Paquete | Responsabilidad |
|---|---|
| `core/` | Configuración, API (`api.py`), motor e hilos (`engine.py`), PowerShell controlado (`winps.py`), actualizaciones (`updates.py`) |
| `monitoring/` | Muestreo de CPU, núcleos, RAM, disco y red; reglas de consumo sostenido |
| `processes/` | Lectura nativa de procesos, rutas, firmas, base de conocimiento, señales y explicaciones |
| `storage/` | SQLite: diagnósticos, comparación, conversaciones, auditoría, ajustes |
| `security/` | Recolección de solo lectura y reglas de auditoría |
| `scripts/` | Analizador estático, catálogo, flujo, desofuscación, modelo, corpus y entrenamiento |
| `actions/` | Acciones supervisadas con confirmación y auditoría |
| `assistant/` | Enrutador, herramientas de solo lectura, cliente de Ollama, verificación y plantillas |
| `reports/` | Informes HTML y PDF |

## Endpoints (todos requieren `X-ScriptLens-Token`)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health`, `/api/system/info`, `/api/metrics/current`, `/api/metrics/history`, `/api/metrics/summary` | Monitoreo |
| GET | `/api/processes`, `/api/processes/{pid}`, `/api/processes/top`, `/api/processes/sustained` | Procesos |
| GET/POST/DELETE | `/api/history/diagnostics[/{id}]`, `/api/history/compare` | Historial y comparación |
| GET/POST | `/api/settings` · GET `/api/privacy/info` · DELETE `/api/privacy/{diagnostics,conversations,actions}` | Privacidad |
| GET/POST | `/api/security/audit` | Auditoría de seguridad (bajo demanda) |
| POST · GET | `/api/scripts/analyze` · `/api/scripts/model` | Analizador de scripts y métricas del modelo |
| POST | `/api/actions/{process,startup,programs,temp}/prepare` → `/api/actions/execute` | Acciones en dos pasos |
| GET | `/api/actions/log`, `/api/actions/programs`, `/api/actions/temp/preview` | Auditoría y vistas previas |
| GET · POST | `/api/assistant/status`, `/api/assistant/conversations[/{id}]` · `/api/assistant/ask` (NDJSON), `/api/assistant/pull` | Asistente |
| GET · POST | `/api/reports` · `/api/reports`, `/api/reports/open/{nombre}`, `/api/reports/open-folder` | Informes |
| GET · POST | `/api/updates/check` · `/api/open-link` | Actualizaciones y enlaces de la lista permitida |

Ejecutar en desarrollo: `.\scripts\dev-backend.ps1` (puerto 8765) o `.\.venv\Scripts\python -m backend`.
