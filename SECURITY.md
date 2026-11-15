# Política de seguridad

## Principios de diseño

- **Análisis local.** Ninguna métrica, lista de procesos, registro o script se envía a servidores externos.
- **API local protegida.** El motor escucha solo en `127.0.0.1`, en un puerto aleatorio, y exige un token aleatorio generado en cada arranque.
- **Sin privilegios innecesarios.** La aplicación se instala por usuario y no solicita permisos de administrador para su funcionamiento normal.
- **Solo lectura por defecto.** Las acciones que modifican el sistema (fases siguientes) requieren confirmación explícita del usuario, revalidan la identidad del proceso y quedan registradas.
- **IA sin ejecución libre.** El asistente solo podrá usar herramientas internas de solo lectura con parámetros validados; los nombres de procesos, rutas y scripts se tratan como datos no confiables.
- **Nunca** se desactiva el antivirus, el firewall ni las actualizaciones de Windows.

## Reportar una vulnerabilidad

Abra un aviso privado en la pestaña *Security → Report a vulnerability* del repositorio
<https://github.com/JorgeGutho21/ScriptLens>. No publique detalles en issues públicos hasta que exista una corrección.

## Versiones con soporte

| Versión | Soporte |
|---|---|
| 0.x (desarrollo) | Correcciones en la rama principal |
