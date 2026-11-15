# Motor de análisis (backend)

Proceso Python que mide el equipo y expone una API local de solo lectura en `127.0.0.1`.

| Módulo | Responsabilidad |
|---|---|
| `core/config.py` | Versión, autoría, rutas de datos locales, parámetros de muestreo |
| `core/api.py` | API FastAPI con token, hilos de muestreo (`Engine`) |
| `monitoring/sampler.py` | Muestras de CPU, núcleos, RAM, paginación, disco y red; información del equipo |
| `monitoring/diagnosis.py` | Reglas de consumo sostenido con explicaciones sencillas |
| `processes/ntquery.py` | Enumeración nativa de procesos (`NtQuerySystemInformation`) |
| `processes/collector.py` | Ranking de procesos, CPU normalizada, consumo sostenido, respaldo psutil |
| `__main__.py` | Arranque: imprime `{"event":"ready","port","token"}` |

Ejecutar: `.\.venv\Scripts\python -m backend` (variables opcionales `SCRIPTLENS_PORT`, `SCRIPTLENS_TOKEN`, `SCRIPTLENS_DATA_DIR`).

## Endpoints (todos requieren `X-ScriptLens-Token`)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health` | Estado, versión, autoría |
| GET | `/api/system/info` | Sistema operativo, CPU, RAM total, discos, disponibilidad de temperatura |
| GET | `/api/metrics/current` | Última muestra y tiempo encendido |
| GET | `/api/metrics/history?seconds=10..3600` | Serie temporal |
| GET | `/api/metrics/summary` | Promedios y hallazgos de diagnóstico; consumo propio de ScriptLens |
| GET | `/api/processes/top?by=cpu|memory&limit=1..50` | Procesos con mayor consumo actual |
| GET | `/api/processes/sustained?seconds=10..600` | Procesos con mayor CPU promedio en la ventana |
