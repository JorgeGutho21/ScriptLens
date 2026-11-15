# Reglas de diagnóstico de rendimiento

Implementadas en `backend/monitoring/diagnosis.py`. Se evalúan sobre el **promedio del último minuto**, nunca sobre una lectura instantánea, y solo cuando hay al menos 20 mediciones.

| Código | Condición | Estado |
|---|---|---|
| `datos_insuficientes` | < 20 mediciones | Información insuficiente |
| `cpu_sostenida` | CPU promedio ≥ 80 % | Consumo elevado |
| `cpu_elevada` | 60 % ≤ CPU promedio < 80 % | Informativo |
| `ram_alta` | RAM promedio ≥ 85 % | Consumo elevado |
| `ram_elevada` | 75 % ≤ RAM promedio < 85 % | Informativo |
| `disco_lleno_<unidad>` | Unidad ≥ 90 % ocupada | Requiere revisión |
| `estado_normal` | Ninguna condición anterior | Normal |

Cada hallazgo incluye título, explicación sencilla, evidencia medida y recomendación. Los umbrales siguen el criterio de niveles de Glances (cuidado/advertencia/crítico), adaptados a un público no técnico.

## Unidades

- CPU por proceso: psutil y los tiempos del núcleo expresan 100 % por núcleo; ScriptLens divide entre los procesadores lógicos para expresarlo como porcentaje del equipo (igual que el Administrador de tareas).
- Memoria por proceso: *working set* (equivalente a `rss`). El Administrador de tareas muestra por defecto el *private working set*, por lo que los valores pueden diferir ligeramente.
- Bytes en unidades binarias (1 GB = 1024³ B), como Windows.
- Disco y red: diferencia de contadores acumulados dividida por el tiempo real transcurrido; si un contador se reinicia, la tasa se informa como 0.
