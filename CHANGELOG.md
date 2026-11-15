# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versionado semántico.

## [0.1.0] — 2026-11-15 (sin publicar)

### Añadido
- **Monitoreo:** CPU total y por núcleo, RAM, paginación, disco, red y tiempo encendido con psutil; diagnóstico de consumo sostenido.
- **Procesos:** lectura nativa con `NtQuerySystemInformation`, rutas, firmas Authenticode por lotes (incluye catálogos), base de conocimiento de procesos de Windows, árbol padre-hijo, explicaciones comprobadas/estimadas.
- **Historial:** SQLite con migraciones, diagnósticos guardados, comparación sin atribución causal, controles de privacidad.
- **Seguridad:** Defender, Centro de seguridad, firewall, inicio automático, tareas, servicios, eventos, cuentas y plan de energía; hallazgos con ocho puntos.
- **Scripts:** catálogo original de 24 reglas + 19 de ampliación, ATT&CK 20.1, desofuscación estática, flujo, explicación por línea, regresión logística balanceada, baseline, política híbrida y evaluación reproducible.
- **Acciones supervisadas:** confirmación con token de un solo uso, revalidación de identidad, procesos protegidos, inicio automático reversible, limpieza acotada de temporales, desinstaladores oficiales, auditoría con mediciones antes/después.
- **Asistente IA:** Ollama + Qwen3 4B Instruct, herramientas de solo lectura, defensa ante inyección de instrucciones, verificación de cifras, modo sin IA, descarga de modelos con autorización.
- **Informes:** PDF y HTML con marca de agua discreta.
- **Distribución:** motor empaquetado con PyInstaller, instalador NSIS por usuario, instancia única, SHA-256, comprobación de actualizaciones bajo demanda, flujo de GitHub Actions que genera el instalador como artefacto.
- **Interfaz:** modo sencillo/avanzado, claro/oscuro, tamaño de texto, reducción de animaciones, glosario, asistente de primera ejecución, elemento 3D con Three.js en carga diferida, límite de errores por pantalla.

### Corregido
- La regla P01 contaba la lectura de la clave Run como persistencia.
- Windows PowerShell 5.1 no cargaba `Get-AuthenticodeSignature` al heredar `PSModulePath` de PowerShell 7.
- La pantalla del asistente quedaba en blanco porque `scrollIntoView` devuelve una Promise en WebView2.
- Interruptores dibujados como activados en celdas alineadas a la derecha.
- Motor huérfano al cerrar la aplicación; instancias duplicadas.
- Análisis de scripts de 1 MB: de 10,4 s a 3,4 s.
