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

---

## 6. Resultado de la versión 0.2 (actualizado el 2026-11-18)

### Matriz de funcionalidades después del desarrollo

| Área | Estado de implementación | Estado de prueba | Evidencia |
| --- | --- | --- | --- |
| Acceso remoto de solo lectura | IMPLEMENTADO | PROBADO (automático + LAN real del mismo equipo) | `test_remote.py` (13), `scripts/probar_remoto.py` contra `https://192.168.1.20:8765` |
| Consola «Mis computadoras» | IMPLEMENTADO | PROBADO con dos agentes simulados en un equipo | `test_fleet.py` (6), revisión visual con un segundo agente en el puerto 8766 |
| Estadísticas | IMPLEMENTADO (dominios web: PENDIENTE, requiere extensión voluntaria) | PROBADO | `test_stats.py` (7), 78 eventos reales de arranque leídos |
| Auditoría de 30 controles | IMPLEMENTADO | PROBADO | `test_audit30.py` (10), ejecución real: 19 CUMPLE, 5 NO CUMPLE, 4 REVISIÓN, 2 NO APLICA |
| Chatbot rápido | IMPLEMENTADO | MEDIDO | `docs/pruebas/asistente/RESULTADOS.md` |
| Interfaz rediseñada | IMPLEMENTADO | REVISADO visualmente en escritorio (1280 × 720) | Panel, Acceso remoto, Mis computadoras, Estadísticas y Auditoría |

### Matriz de aceptación (`CRITERIOS_ACEPTACION.md`)

| N.º | Criterio | Resultado | Evidencia |
| --- | --- | --- | --- |
| 1 | Diagnóstico local igual tras el cambio | ✅ | Las 135 pruebas anteriores siguen aprobadas dentro de las 186 actuales |
| 2 | Acceso remoto inicia apagado | ✅ | `test_local_control_api`; el estado nunca se restaura al abrir |
| 3 | El propietario habilita y empareja desde la PC | ✅ | Pantalla Acceso remoto: botón Autorizar probado con la frase `GM-6L` |
| 4 | Un celular ve datos actualizados de esa PC | ⚠️ PARCIAL | Probado con un cliente HTTPS por la IP de la LAN; **falta un celular físico** |
| 5 | Sesión no autorizada rechazada | ✅ | `test_unauthenticated_requests_are_rejected` (incluye el token interno de Tauri) |
| 6 | Remoto no puede POST/DELETE de acciones, ajustes ni archivos | ✅ | `test_no_write_or_local_route_reachable_remotely` recorre todas las rutas locales |
| 7 | Desactivar/revocar corta conexiones existentes y futuras | ✅ | `test_revocation_and_disable_cut_existing_sessions`, `test_revocation_marks_device_disconnected` |
| 8 | El modo remoto indica el origen y la antigüedad de las cifras | ✅ | `medido_en` en cada respuesta; «En vivo / Datos atrasados / Desconectado» |
| 9 | Dos equipos se vinculan y muestran CPU/RAM separados | ⚠️ SIMULADO | Dos agentes con identidad, certificado y datos propios en el mismo hardware |
| 10 | Equipo desconectado se muestra offline, no en vivo | ✅ | Prueba automática y visual («Desconectado · última lectura 1:41:02») |
| 11 | Historial con `device_id` y marcas de tiempo | ✅ | `test_two_agents_are_independent` |
| 12 | Estadísticas por día/semana/mes, sesiones y tiempo activo distinguidos | ✅ | `test_active_time_and_session_are_distinct` |
| 13 | Apps y dominios opt-in; pausa, borrado y retención | ✅ apps / ❌ dominios | Dominios no implementados a propósito (sin extensión de navegador) |
| 14 | Los 30 controles con evidencia, estado e informe PDF/HTML | ✅ | `test_real_windows11_capture`, `test_reports`, `test_routes_run_and_report` |
| 15 | La auditoría no cambia configuraciones | ✅ | `test_collection_script_is_read_only` (análisis estático del script) |
| 16 | Chatbot: datos antes y después | ✅ | 32,7 s → 3,5 s de mediana total; RAM/VRAM del modelo registrada |
| 17 | Preguntas simples sin esperar al modelo | ✅ | `test_instant_answers_without_model_and_with_verified_figures` |
| 18 | Con y sin Ollama; 10 preguntas; cancelación | ✅ | `test_works_without_ollama`, benchmark de 10 preguntas, `test_cancellation_stops_generation` |
| 19 | Interfaz móvil/escritorio sin recortes, onboarding | ⚠️ PARCIAL | Escritorio revisado; vista del celular verificada solo por código (CSS adaptable), sin captura en un teléfono |
| 20 | CI de Python, React/TS, Rust y seguridad remota | ✅ | GitHub Actions en verde en cada fase |
| 21 | Instalador actualizado, sin administrador, datos conservados | ✅ | Instalación silenciosa por usuario en 9 s sobre la 0.1.1; base migrada al esquema 2 con los datos previos; motor solo en 127.0.0.1 |
| 22 | Versión, SHA-256 y release solo si aprobada | ✅ | Release v0.2.0 publicada tras CI en verde; SHA-256 verificado en la descarga pública |
| 23 | README/Pages enlazan a la versión publicada | ✅ | PR #10 |
| 24 | Windows 10 y equipos de 4 GB | ❌ NO PROBADOS | Solo hay un equipo Windows 11 de 31,8 GB |
| 25 | Demostración real con 2 PC y celular | ❌ SIMULADA | Procedimiento en `docs/guias/Conectar_y_supervisar_computadoras.md` |
| 26 | Licencias y atribuciones, sin secretos en Git | ✅ | Licencias de referencias verificadas en GitHub; BAT del taller no se subieron |

### Errores encontrados y corregidos durante el desarrollo

- Volver a vincular una consola dejaba viva la sesión anterior en la otra PC → se cierra antes de reemplazarla.
- Sin administrador, `Get-Tpm` informa `TpmPresent=False` aunque el TPM exista → solo se usa elevado.
- La respuesta inmediata incluía una fecha que no estaba en los datos medidos (la verificación la marcó) → se añadió
  la fecha real del último arranque a los datos.
- Las rutas de la auditoría no se registraron en el commit de la fase 4 (la orden falló antes de ejecutarse) → corregido
  y cubierto con una prueba de rutas.
- La pantalla de auditoría dejaba de consultar rápido justo después de pulsar el botón → espera un resultado posterior al clic.
## 7. Publicación

| Elemento | Resultado |
| --- | --- |
| PR #9 | Fusionado en `main` como `35055c0` con 7 comprobaciones en verde; árbol idéntico a la rama probada |
| Release | `v0.2.0` (*Latest*) sobre `35055c0`; se conservan v0.1.0 y v0.1.1 |
| Instalador | `ScriptLens-IA_0.2.0_x64-setup.exe`, 54 531 345 bytes |
| SHA-256 | `FAE79D9D26BDE040E14E9F2504F304554FAF6A166DDA0F0F88B2EFE099813E2C` (comprobado tras descargarlo de forma anónima desde GitHub) |
| Motor empaquetado | Probado por la LAN: vinculación, datos en vivo, 404 en operaciones prohibidas y 401 tras revocar; auditoría de 30 controles en 17,9 s |
| GitHub Pages | Desplegado desde `main` con las secciones de uso, acceso remoto, preguntas frecuentes y capturas de la 0.2.0 |