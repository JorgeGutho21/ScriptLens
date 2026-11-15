<p align="center">
  <img src="assets/branding/scriptlens-icon.svg" width="96" alt="Logotipo de ScriptLens IA">
</p>

<h1 align="center">ScriptLens IA</h1>

<p align="center">
  Sistema inteligente de diagnóstico, seguridad, auditoría y optimización del sistema operativo Windows.<br>
  <strong>Desarrollado por Jorge Gutiérrez</strong> · GitHub: <a href="https://github.com/JorgeGutho21">@JorgeGutho21</a><br>
  Universidad Popular del Cesar · Ingeniería de Sistemas · ExpoSoftware 2026-II
</p>

> **Estado:** en desarrollo (versión 0.1.0). Aún no hay instalador publicado en Releases. El estado detallado de cada módulo está en [docs/ESTADO_DESARROLLO.md](docs/ESTADO_DESARROLLO.md).

## Qué es

ScriptLens IA explica, en lenguaje sencillo, por qué un computador con Windows va lento, qué programas están funcionando y si algo merece revisión. Todo el análisis ocurre en el propio equipo.

## Características

| Módulo | Estado |
|---|---|
| Panel de rendimiento en tiempo real (CPU, núcleos, RAM, disco, red, tiempo encendido) | ✅ Implementado |
| Diagnóstico de consumo sostenido con explicaciones sencillas | ✅ Implementado |
| Procesos que más consumen y consumo sostenido por proceso | ✅ Implementado |
| Modo sencillo / avanzado, modo claro / oscuro, tamaño de texto, reducir animaciones | ✅ Implementado |
| Asistente de primera ejecución y glosario contextual | ✅ Implementado |
| Administrador de procesos con árbol, firmas y explicaciones | 🔜 Próxima fase |
| Centro de seguridad (Microsoft Defender, firewall, inicio automático, tareas programadas) | 🔜 |
| Analizador de scripts BAT/CMD/PowerShell (reglas, MITRE ATT&CK, regresión logística balanceada) | 🔜 |
| Asistente local con Ollama + Qwen3 | 🔜 |
| Comparar mi computador, historial SQLite e informes PDF/HTML | 🔜 |
| Acciones supervisadas con confirmación y auditoría | 🔜 |
| Instalador Windows en GitHub Releases | 🔜 |

## Tecnologías

Tauri 2 · React 19 · TypeScript · Tailwind CSS 4 · Python 3.12 · psutil · FastAPI · API nativa de Windows (`NtQuerySystemInformation`) · pytest · GitHub Actions.

Arquitectura: [docs/arquitectura/arquitectura.md](docs/arquitectura/arquitectura.md) · Sistema de diseño: [docs/arquitectura/sistema_diseno.md](docs/arquitectura/sistema_diseno.md) · Investigación de repositorios: [docs/arquitectura/investigacion_repositorios.md](docs/arquitectura/investigacion_repositorios.md).

## Instalación

### Método A — Instalador gráfico (usuarios)

Disponible cuando se publique la primera versión en [Releases](https://github.com/JorgeGutho21/ScriptLens/releases). Las instrucciones paso a paso con capturas se añadirán junto con el instalador verificado.

### Método B — PowerShell (descarga verificada)

Se documentará con el primer instalador publicado, incluyendo la verificación del hash SHA-256. No existe aún un paquete WinGet oficial.

### Método C — Desarrolladores (desde el código fuente)

Requisitos: Git, Python 3.12, Node.js 20+, Rust estable, Visual Studio Build Tools con "Desarrollo de escritorio con C++".

En **PowerShell**:

```powershell
git clone https://github.com/JorgeGutho21/ScriptLens.git
cd ScriptLens
py -3.12 -m venv .venv
.\.venv\Scripts\pip install -r backend\requirements-dev.txt
npm install
npm --prefix frontend install
npm run dev
```

`npm run dev` abre la aplicación de escritorio y arranca automáticamente el motor de análisis. Si Rust informa `link.exe not found`, ejecute antes `. .\scripts\msvc-env.ps1` en la misma ventana.

Pruebas: `.\.venv\Scripts\python -m pytest`

## Privacidad

El análisis es local. ScriptLens no envía listas de procesos, registros, archivos ni datos personales a ningún servidor. Ver [SECURITY.md](SECURITY.md).

## Licencia y atribuciones

MIT © 2026 Jorge Gutiérrez. Componentes y referencias de terceros en [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
