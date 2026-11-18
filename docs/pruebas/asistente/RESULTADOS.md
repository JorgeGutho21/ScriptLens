# Rendimiento del asistente: antes y después (medido)

**Fecha:** 2026-11-18 · **Equipo:** Windows 11 Pro 25H2 (build 26200), 31,8 GB de RAM, GPU con memoria compartida
(Ollama colocó 2,2 GB del modelo 4B en VRAM y 1,6 GB del 1.7B por completo en VRAM) · **Ollama** activo ·
**Script:** `scripts/benchmark_asistente.py` · **Datos crudos:** los `.json` de esta carpeta.

Cada medición recorre las **diez preguntas de referencia** con el flujo completo que vive el usuario (recopilar datos
→ modelo → verificación de cifras). La primera pregunta de cada serie empieza con el modelo **descargado de memoria**
(arranque en frío, `--descargar`).

## Resumen (medianas de las 10 preguntas)

| Configuración | 1.er fragmento | Total | Tokens/s | Cifras verificadas | Memoria del modelo |
| --- | ---: | ---: | ---: | :---: | --- |
| **Antes** — código v0.1.1, `qwen3:4b-instruct` | 7,0 s | 32,7 s | ≈ 6,0* | 10/10 | 3,9 GB (2,2 GB en GPU) |
| **Después — Automático** (predeterminado) | 2,0 s | **3,5 s** | 51,1 | 10/10 | 1,6 GB (todo en GPU) |
| Después — IA detallada, mismo `qwen3:4b-instruct` | 5,6 s | 22,4 s | 7,1 | 10/10 | 3,9 GB (2,2 GB en GPU) |
| Después — IA rápida, `qwen3:1.7b` | 2,2 s | 4,6 s | 53,1 | 10/10 | 1,6 GB (todo en GPU) |

\* En la versión anterior Ollama no entregaba sus contadores a ScriptLens; los tokens/s «antes» se estimaron con los
fragmentos recibidos por segundo. Después se usan `eval_count / eval_duration` de Ollama.

En modo **Automático**, 3 de las 10 preguntas («¿Qué programa consume más RAM?», «¿Qué proceso consume más CPU?»,
«¿Qué está ocupando el disco?») se respondieron **sin modelo**, con los datos medidos, en menos de 0,05 s.

## Qué cambió y cuánto aportó

1. **Respuesta inmediata** para preguntas que piden un dato (CPU, RAM, disco, tiempo encendido): 0,02 s frente a ~20 s.
2. **Modelo pequeño que cabe entero en la GPU** (`qwen3:1.7b`): ~51 tokens/s frente a ~7 del 4B, que en este equipo
   reparte capas entre GPU y CPU. Es la mejora principal en las preguntas que sí usan IA.
3. **Menos tokens de entrada**: datos compactados (listas de 5 elementos, sin campos vacíos) y contexto de 4096 en
   modo rápido; con el mismo modelo 4B el total bajó de 32,7 s a 22,4 s (−31 %) y el primer fragmento de 7,0 a 5,6 s.
4. **Estado de Ollama en caché 15 s** (antes: dos peticiones HTTP por pregunta) y `keep_alive` de 30 min.
5. **Precarga** del modelo al abrir el asistente si hay ≥ 3,5 GB de RAM libres, porque el arranque en frío domina la
   primera pregunta (carga medida del 1.7B: 14,2 s; primer fragmento del 4B en frío: 33,7 s).
6. **Cancelación real** («Detener»): se cierra la conexión y Ollama deja de generar (probado en `test_assistant.py`).

## Exactitud (revisión manual, no solo cifras)

- La verificación de cifras aprobó todas las respuestas en las cuatro series.
- **Error detectado en el modo rápido (1.7B):** a «¿Qué tareas se ejecutan en segundo plano?» respondió que Chrome y
  Edge «son necesarios para el funcionamiento del sistema», lo cual es falso. La verificación de cifras no detecta
  este tipo de error. Por eso la interfaz identifica el modo («IA rápida») y el modo **IA detallada** sigue
  disponible para explicaciones en las que se vaya a tomar una decisión.
- Las respuestas inmediatas no pasan por un modelo: solo reformulan los datos medidos y nunca inventan valores.

## Limitaciones de estas mediciones

- Un solo equipo. Durante la serie «IA detallada» también se ejecutaron la revisión visual de la interfaz y la
  auditoría de 30 controles, que compitieron por la CPU; sus tiempos pueden estar ligeramente penalizados.
- En un portátil sin GPU utilizable por Ollama los tiempos serán mayores; **no se probó**.
- Sin Ollama, el asistente responde con plantillas a partir de los mismos datos (probado en `test_assistant.py`).
