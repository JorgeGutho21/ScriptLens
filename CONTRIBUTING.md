# Guía de contribución

## Preparar el entorno (PowerShell)

```powershell
git clone https://github.com/JorgeGutho21/ScriptLens.git
cd ScriptLens
py -3.12 -m venv .venv
.\.venv\Scripts\pip install -r backend\requirements-dev.txt
npm install
npm --prefix frontend install
```

Requisitos: Git, Python 3.12, Node.js 20+, Rust estable y Visual Studio Build Tools con "Desarrollo de escritorio con C++".

## Ejecutar

```powershell
npm run dev          # abre la aplicación de escritorio (Tauri) y arranca el motor
.\.venv\Scripts\python -m pytest     # pruebas del motor
npm --prefix frontend run build      # verificación de tipos y compilación de la interfaz
```

## Convenciones

- Mensajes de commit en español, en infinitivo y describiendo una unidad lógica ("Implementar el árbol de procesos").
- Separar responsabilidades: interfaz (`frontend/`), recolección (`backend/monitoring`, `backend/processes`), diagnóstico, IA (`backend/assistant`) y acciones (`backend/actions`).
- Ningún dato inventado: si una métrica no está disponible, se devuelve `null` y la interfaz lo explica.
- Toda acción que modifique el sistema debe pasar por `backend/actions` con confirmación y registro de auditoría.
