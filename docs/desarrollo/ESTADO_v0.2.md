# ScriptLens IA — Auditoría inicial y estado de la versión 0.2

**Fecha de la auditoría:** 2026-11-18 · **Base:** `main` en `c94cfe3` (tras fusionar el PR #8) · **Release pública:** v0.1.1

Este documento distingue lo que existe, lo que se probó y lo que falta. Los estados se asignan por evidencia
(pruebas ejecutadas, lectura de código o ensayo manual), no por número de archivos.

## 1. Estado del repositorio al comenzar

| Elemento | Hallazgo |
| --- | --- |
| Rama principal | `main` = `c94cfe3`. La historia se reescribió antes de esta fase; la copia local antigua (`14a7420`) y la rama `feat/desarrollo-integral` no comparten base con `main` y no se reutilizan. |
| PR abiertos | #8 (guía oficial y bloqueo de tráileres automáticos): CI y Pages en verde, sin conflictos → **fusionado** antes de empezar. |
| Releases | v0.1.0 y v0.1.1 (Latest). Se conservan. |
| CI | `ci.yml` (pytest, compilación React, `cargo check`), `instalador.yml` (PyInstaller + NSIS + SHA-256 como artefacto), `pages.yml` (GitHub Pages). |
| Pruebas | 135 pruebas de pytest, todas aprobadas en Windows 11 Pro 26200 (este equipo). La interfaz compila (`tsc -b && vite build`). |
| Herramientas locales | Python 3.12.10, Node 26, Cargo 1.100, Ollama con `qwen3:4b-instruct` y `qwen3:4b`. |

## 2. Matriz de funcionalidades

Leyenda: **IMPLEMENTADO** (código completo) · **PARCIAL** · **PENDIENTE** · **PROBADO** (prueba automática o ensayo registrado) · **NO PROBADO**.

| Área | Funcionalidad | Estado de implementación | Estado de prueba | Evidencia |
| --- | --- | --- | --- | --- |
| Diagnóstico local | CPU total y por núcleo, RAM, swap, disco y red por segundo | IMPLEMENTADO | PROBADO | `monitoring/sampler.py`, `test_api.py`, `test_monitoring.py` |
| Diagnóstico local | Hallazgos explicados (consumo sostenido, RAM alta, disco lleno) | IMPLEMENTADO | PROBADO | `monitoring/diagnosis.py` |
| Procesos | Lista, detalle, firma Authenticode, categorías, señales | IMPLEMENTADO | PROBADO | `processes/*`, `test_processes.py` |
| Acciones supervisadas | Cerrar procesos y desactivar inicios con confirmación y registro | IMPLEMENTADO | PROBADO | `actions/operations.py`, `test_actions.py` |
| Seguridad | Defender, firewall, inicio automático, tareas programadas | IMPLEMENTADO | PROBADO | `security/*`, `test_security.py` |
| Scripts | Analizador por reglas + clasificador TF-IDF + explicación por línea | IMPLEMENTADO | PROBADO | `scripts/*`, `test_scripts.py` |
| Historial | Diagnósticos guardados y comparación antes/después | IMPLEMENTADO | PROBADO | `storage/*`, `test_history.py` |
| Informes | PDF y HTML del diagnóstico | IMPLEMENTADO | PROBADO | `reports/*`, `test_reports.py` |
| Asistente | Enrutador determinista, herramientas de lectura, Ollama con streaming, verificación de cifras, modo sin IA | IMPLEMENTADO | PROBADO (sin modelo); con modelo, NO MEDIDO | `assistant/*`, `test_assistant.py` |
| Acceso remoto | Ver la PC desde celular u otra laptop | **PENDIENTE** | — | El motor solo escucha en `127.0.0.1` (`core/config.py`) |
| Varias computadoras | Agente + consola central | **PENDIENTE** | — | No existe ningún módulo |
| Estadísticas | Historial persistente por hora/día/semana, sesiones, tiempo activo | **PENDIENTE** (solo hay 10 min en memoria) | — | `SystemSampler.history_seconds = 600` |
| Auditoría 30 controles | Integración del taller | **PENDIENTE** (el Centro de seguridad cubre ~6 de los 30) | — | `security/collect.py` |
| Chatbot rápido | Respuestas inmediatas, modos rápido/detallado, cancelación, métricas | **PARCIAL** (streaming y `think:false` ya existen) | NO MEDIDO | `assistant/llm.py` |
| Instalador | PyInstaller + NSIS por usuario, SHA-256 | IMPLEMENTADO | PROBADO (v0.1.1) | `scripts/construir_instalador.ps1` |

## 3. Problemas detectados en la auditoría

1. `assistant/service.py` llama a `llm.status()` (dos peticiones HTTP a Ollama) en **cada** pregunta.
2. El modelo recibe siempre `num_ctx=8192` y hasta 700 tokens aunque la pregunta sea trivial; las preguntas simples
   («¿cuánta RAM uso?») podrían contestarse con los datos medidos sin invocar al modelo.
3. No hay forma de cancelar una respuesta: si el usuario abandona, la generación continúa en Ollama.
4. `requirements.txt` no incluye una biblioteca criptográfica; el acceso remoto la necesitará para TLS.
5. La CSP de Tauri solo permite `http://127.0.0.1:*`; la consola de varias PC debe pasar por el motor local, no por la interfaz.

## 4. Material del taller (análisis estático, nada se ejecutó)

- `Controles_Windows10_30.ps1`: **30 controles de solo lectura** (`Get-*`, lectura de registro, `auditpol /get`, `net accounts`).
  Además vuelca todas las variables de entorno, seriales de BIOS/placa, `whoami /all` y `netstat`; esos anexos **no** se
  reproducen en ScriptLens porque pueden contener secretos.
- BAT de los grupos: contienen persistencia oculta (VBS + registro), atributos ocultos, cierre automático de procesos y
  envío por FTP/curl de imágenes del Escritorio y de Imágenes. Las líneas con credenciales vienen redactadas en el paquete.
  **Si las credenciales FTP de los originales siguen vigentes, deben rotarse.** Solo se reutilizan las consultas seguras:
  sistema operativo, RAM total, IPv4, MAC, procesos, proceso de mayor RAM/CPU y puertos en escucha.
- «30 controles» (ZIP) y «30 peticiones» (mencionadas por el profesor) **no se han verificado como equivalentes**; el texto
  de clase no enumera las 30 peticiones.

## 5. Arquitectura mínima elegida

```
                 ┌──────────────── PC con ScriptLens (agente) ────────────────┐
 Interfaz Tauri ─┤ API local 127.0.0.1:<aleatorio> + X-ScriptLens-Token (igual) │
                 │            │ mismo Engine (un solo muestreo)                  │
                 │ API remota de SOLO LECTURA (apagada por defecto)              │
                 │   HTTPS con certificado propio, solo IP privadas, lista       │
                 │   explícita de rutas GET, sesiones con caducidad y revocación │
                 └──────────▲───────────────────────────────▲──────────────────┘
                            │ navegador (celular / laptop)  │ consola «Mis computadoras»
                            │ código temporal + aprobación  │ (otra PC con ScriptLens): sondeo
                            │ en la PC propietaria          │ periódico con huella TLS fijada
```

- **Acceso remoto**: segundo servidor uvicorn en el mismo proceso, con su propia aplicación FastAPI que solo registra
  rutas `GET` de consulta. Reutiliza `Engine`, por lo que no se duplica el muestreo. Escucha solo en las direcciones IPv4
  privadas del equipo y solo mientras el usuario lo mantiene activo.
- **Consola de varias PC** (patrón *hub/agent* de Beszel): cada PC que activa el acceso remoto actúa como agente; la
  consola es cualquier ScriptLens que se vincula a ella con el mismo código + aprobación, guarda la huella del certificado
  (TOFU) y consulta cada pocos segundos. El historial se guarda en la consola con `device_id` y marca de tiempo.
- **Estadísticas**: agregación por minuto y por hora en SQLite a partir del muestreo existente, con retención configurable.
- **30 controles**: script PowerShell constante del repositorio, solo lectura, que devuelve JSON; informes PDF/HTML.
- **Chatbot**: respuesta inmediata determinista, modo rápido (Qwen3 1.7B) y detallado (Qwen3 4B Instruct), caché de estado,
  contexto reducido y cancelación.

Kubernetes no aporta valor a una aplicación de escritorio en LAN; no se usa ni se presenta como usado.
