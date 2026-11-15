# Arquitectura de ScriptLens IA

```
┌──────────────────────────── ScriptLens IA (proceso Tauri, Rust) ───────────────────────────┐
│  Ventana WebView2                                                                          │
│  ┌──────────────── Interfaz React + TypeScript + Tailwind ─────────────────┐                │
│  │ Panel · Procesos · Seguridad · Scripts · Asistente · Comparar · Informes │                │
│  └───────────────▲─────────────────────────────────────────────────────────┘                │
│                  │ HTTP 127.0.0.1:<puerto aleatorio> + encabezado X-ScriptLens-Token        │
│  comando backend_info ◄── lee {"event":"ready","port","token"} del stdout del motor         │
└──────────────────┼─────────────────────────────────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────── Motor de análisis (Python, proceso hijo) ───────────────────┐
│ core/        API FastAPI local, configuración, arranque                                    │
│ monitoring/  SystemSampler (1 s) · diagnóstico por reglas · información del equipo         │
│ processes/   ProcessMonitor (2 s) · ntquery (NtQuerySystemInformation) · respaldo psutil    │
│ security/    (fase 4) Defender, firewall, inicio automático, tareas programadas            │
│ scripts/     (fase 5) reglas + TF-IDF/n-gramas + regresión logística balanceada + ATT&CK   │
│ assistant/   (fase 7) Ollama/Qwen3 con herramientas internas de solo lectura               │
│ actions/     (fase 6) acciones supervisadas con confirmación y auditoría                   │
│ storage/     (fase 3) SQLite local: diagnósticos, historial, conversaciones                │
│ reports/     (fase 8) HTML/PDF con marca de agua                                           │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Decisiones

1. **Separación motor/interfaz.** La interfaz no lee el sistema directamente; todo pasa por el motor, que valida parámetros (p. ej. `by` solo acepta `cpu|memory`, `seconds` acotado). Esto facilita las pruebas y la seguridad de la IA: el asistente solo podrá usar los mismos endpoints de solo lectura.
2. **API local autenticada.** Puerto aleatorio en 127.0.0.1 y token aleatorio por arranque, comparado en tiempo constante. CORS limitado al origen de Tauri. Sin `/docs` ni `/openapi.json`.
3. **Sin privilegios de administrador.** La lectura nativa de procesos no requiere elevar privilegios. El instalador NSIS se instala por usuario (`installMode: currentUser`).
4. **Bajo consumo propio.** Muestreo global cada 1 s y de procesos cada 2 s; historial acotado (10 min en memoria); la interfaz deja de consultar cuando la ventana no es visible; gráficos SVG sin librerías.
5. **Honestidad de datos.** Valores no disponibles se devuelven como `null` y se muestran como "—" (p. ej. temperatura en Windows). Los módulos pendientes se indican como "Próximo" sin datos simulados.

## Flujo de arranque

1. Tauri inicia y lanza el motor (`scriptlens-backend.exe` empaquetado o `.venv\Scripts\python -m backend` en desarrollo) sin ventana de consola.
2. El motor enlaza un puerto libre, inicia los hilos de muestreo y escribe la línea `ready`.
3. La interfaz consulta `backend_info` hasta obtener puerto y token, y muestra la pantalla de carga mientras tanto.
4. Al cerrar la aplicación, Tauri finaliza el proceso del motor.
