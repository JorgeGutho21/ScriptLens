# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versionado semántico.

## [Sin publicar]

### Añadido
- Arquitectura inicial: contenedor Tauri 2, interfaz React/TypeScript/Tailwind y motor de análisis Python.
- Motor de monitoreo real con psutil: CPU total y por núcleo, RAM, archivo de paginación, actividad de disco y red, tiempo encendido.
- Lectura nativa de procesos mediante `NtQuerySystemInformation` (concepto de System Informer), con respaldo en psutil.
- Diagnóstico de consumo sostenido con explicaciones en lenguaje sencillo.
- API local en 127.0.0.1 con token aleatorio por arranque.
- Panel general con indicadores circulares, gráfico de 5 minutos, comparación actual/promedio, procesos más costosos.
- Sistema de diseño con modo claro/oscuro, tamaño de texto, reducción de animaciones, modo sencillo/avanzado.
- Asistente de primera ejecución (8 pasos) y glosario contextual.
- Identidad gráfica: logotipo e iconos de Windows.
- Pruebas automatizadas del motor y flujo de CI en GitHub Actions.
