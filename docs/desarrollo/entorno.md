# Preparación del entorno de desarrollo (registro real)

Equipo de desarrollo: Windows 11 Pro 10.0.26200, 8 procesadores lógicos, 32 GB de RAM.

## Herramientas encontradas al iniciar (2026-11-14)

| Herramienta | Estado inicial |
|---|---|
| Git 2.56, GitHub CLI 2.103, Node.js 26.13, npm 11.20, WinGet 1.29, Ollama 0.40.16 | Instaladas |
| Python | No instalado (solo el alias de Microsoft Store) |
| Rust | No instalado |
| Visual Studio Build Tools (C++) | No instalado |

## Instalación realizada (autorizada por el autor)

Ejecutado en **PowerShell**:

```powershell
winget install --id Python.Python.3.12 -e --scope user --accept-package-agreements --accept-source-agreements --silent
winget install --id Rustlang.Rustup -e --accept-package-agreements --accept-source-agreements --silent
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
rustup default stable
```

Resultado: Python 3.12.10, rustup 1.29.3 / cargo 1.100.0, MSVC 14.44.35207 y SDK 10.0.26100.0.

### Problemas encontrados

1. **`python` no se reconocía tras instalar.** La sesión de terminal conservaba el PATH anterior y el alias de Microsoft Store tenía prioridad. Solución: usar la ruta absoluta `%LOCALAPPDATA%\Programs\Python\Python312\python.exe` para crear `.venv`, o abrir una terminal nueva.
2. **`link.exe not found` al compilar con cargo.** MSVC quedó instalado en disco, pero `vswhere` no registró la instancia y `vcvars64.bat` falló. Solución: `scripts/msvc-env.ps1` carga manualmente `PATH`, `LIB` e `INCLUDE` en la sesión.

## Entorno del proyecto

En **PowerShell**, desde la raíz del repositorio:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
.\.venv\Scripts\pip install -r backend\requirements-dev.txt
npm install                    # CLI de Tauri
npm --prefix frontend install  # dependencias de la interfaz
```

## Modo navegador (solo para desarrollo de interfaz)

Terminal 1 (PowerShell):
```powershell
$env:SCRIPTLENS_PORT='8765'; $env:SCRIPTLENS_TOKEN='dev-local-token'; .\.venv\Scripts\python -m backend
```

Crear `frontend/.env.development.local` (ignorado por Git):
```
VITE_BACKEND_URL=http://127.0.0.1:8765
VITE_BACKEND_TOKEN=dev-local-token
```

Terminal 2: `npm --prefix frontend run dev` y abrir http://127.0.0.1:1420.
