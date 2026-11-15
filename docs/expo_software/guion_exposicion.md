# ScriptLens IA — Material para ExpoSoftware 2026-II

Autor: Jorge Gutiérrez (@JorgeGutho21) · Universidad Popular del Cesar · Docente: Oswaldo Rueda Carreño (confirmar grafía oficial)

## 1. Resumen ejecutivo

ScriptLens IA es una aplicación de escritorio para Windows que explica, en lenguaje sencillo, por qué un computador va lento, qué programas funcionan, qué arranca con el sistema y si algo merece revisión. Analiza scripts BAT, CMD y PowerShell **sin ejecutarlos** con reglas asociadas a MITRE ATT&CK y una regresión logística balanceada, y responde preguntas con un modelo de lenguaje **local** (Qwen3 4B Instruct en Ollama) cuyas cifras se verifican contra los datos medidos. Ninguna acción se ejecuta sin confirmación y la IA no puede actuar.

Resultados medidos: 135 pruebas automatizadas aprobadas; en 18 scripts realistas no vistos, la política híbrida detectó 6 de 6 scripts sensibles (el modelo solo, 4 de 6); lectura de procesos en menos de 0,05 s; instalador de 49,3 MB sin administrador, probado en Windows 11.

## 2. Guion de exposición (7 minutos)

| Tiempo | Qué decir | Qué mostrar |
|---|---|---|
| 0:00–0:45 | «¿Cuántas veces su computador se puso lento y no supo por qué? ¿O ejecutó un script de un compañero sin leerlo?» Presentar el problema | Diapositivas 1–2 |
| 0:45–1:30 | Qué es ScriptLens: medir, explicar y actuar con supervisión; todo local | Diapositiva 3 y Panel general |
| 1:30–2:30 | Demostración de consumo elevado (sección 3, paso 2) | Panel → consumo sostenido → Procesos |
| 2:30–3:30 | Análisis de un script de demostración sin ejecutarlo | Analizar scripts → ejemplo de persistencia |
| 3:30–4:30 | Asistente: «¿Hay programas sospechosos?» y verificación de cifras | Asistente IA |
| 4:30–5:30 | Seguridad y acción supervisada (confirmación con «Cancelar» por defecto) | Seguridad → Inicio automático |
| 5:30–6:30 | Resultados medidos y limitaciones honestas | Diapositivas de resultados |
| 6:30–7:00 | Cierre: «Antes de ejecutar un script, léalo. ScriptLens le ayuda a leerlo.» | Diapositiva final |

## 3. Demostración guiada y reproducible

Preparación (PowerShell, la noche anterior):

1. Instale ScriptLens con el instalador y ábralo una vez (el primer arranque es lento).
2. Abra Ollama y compruebe en el asistente que diga «Ollama activo» y que `qwen3:4b-instruct` aparezca como descargado.
3. En **Seguridad**, pulse **Revisar ahora** para que la auditoría quede lista.
4. Cierre programas innecesarios para que las cifras sean claras.

Durante la exposición:

1. **Estado normal.** Muestre el Panel general: «Su computador funciona con normalidad».
2. **Consumo controlado.** En una ventana de PowerShell, en la carpeta del repositorio, ejecute:
   `.\.venv\Scripts\python scripts\demo_consumo.py --nucleos 6 --segundos 90`
   (si no hay repositorio, cualquier programa exigente sirve). Tras unos 30 s el panel pasa a «El procesador está muy ocupado de forma continua». En **Procesos → Consumo elevado** aparece `python.exe`. Explique que ScriptLens no lo llama peligroso: solo «consumo elevado». El script se detiene solo.
3. **Script sin ejecutar.** En **Analizar scripts**, pulse **Ejemplo: persistencia**: decisión «Sensible», severidad «Alta», técnicas T1547.001, T1564.001, T1070.004 y explicación por línea. Señale el rótulo «No se ejecutó». Opcional: arrastre `tests\fixtures\scripts_reales\ofuscado.ps1.txt` para mostrar la decodificación de Base64.
4. **Asistente.** Pregunte «¿Qué programa consume más RAM?» y «¿Hay programas sospechosos?». Muestre el indicador de cifras verificadas y la «Evidencia usada».
5. **Acción supervisada.** En **Seguridad → Inicio automático** pulse un interruptor: muestre el diálogo y pulse **Cancelar**. Explique la revalidación de identidad y el registro de acciones.
6. **Informe.** En **Informes**, pulse **Crear PDF** y muestre la marca de agua.

Todos los datos de la demostración son reales del equipo, salvo los dos scripts de ejemplo, que están rotulados como ejemplos y nunca se ejecutan. No se usa malware real.

Plan B sin Ollama: desmarque «Usar IA local»; el asistente responde con plantillas y los mismos datos.

## 4. Explicación del modelo de IA (para el jurado)

- **Motor analítico (aprendizaje supervisado):** cada script se convierte en n-gramas de 3 a 5 caracteres ponderados con TF-IDF más el número de hallazgos por categoría; una regresión logística con clases balanceadas estima consulta / modifica / sensible. Se combina con reglas: «sensible» si lo dicen las reglas o si el modelo da al menos 0,30.
- **Asistente (IA generativa local):** un enrutador determinista elige herramientas de solo lectura; Qwen3 4B Instruct redacta; un verificador comprueba cada cifra.
- **Por qué no solo el modelo de lenguaje:** porque puede inventar (se observó: «más del 70 % de la RAM» sin respaldo) y porque no debe decidir acciones.

## 5. Comparación frente a herramientas existentes

| | Administrador de tareas | System Informer | Microsoft Defender | ScriptLens IA |
|---|---|---|---|---|
| Explica en lenguaje sencillo | No | No | Parcial | Sí |
| Distingue consumo sostenido | No | Parcial | — | Sí |
| Analiza scripts sin ejecutarlos | No | No | Detecta malware conocido | Explica riesgo y técnicas |
| Asistente con IA local | No | No | No | Sí, con cifras verificadas |
| Acciones con confirmación y auditoría | No | No | — | Sí |

## 6. Preguntas frecuentes del jurado

1. **¿Por qué regresión logística y no una red neuronal?** Funciona bien con pocos datos, es rápida (10 ms por script) e interpretable: la aplicación muestra qué fragmentos empujan hacia «sensible».
2. **¿Las métricas son reales?** Sí, se regeneran con `python -m backend.scripts.train`. Advertimos que el corpus es sintético y que el conjunto realista es pequeño y con un solo etiquetador.
3. **¿Por qué el baseline tiene F1 = 1,0?** Porque el corpus sintético usa los mismos comandos que buscan las reglas (circularidad). Por eso evaluamos aparte con 18 scripts escritos a mano.
4. **¿Qué pasa si un proceso se llama «svchost.exe» pero está en Temp?** Se marca «posible suplantación» si además no tiene firma válida; no se califica como malware.
5. **¿La IA puede borrar archivos o cerrar procesos?** No. No tiene acceso al módulo de acciones; una prueba automática lo comprueba.
6. **¿Qué datos salen del equipo?** Ninguno. Solo «Buscar actualizaciones» consulta GitHub, y solo si el usuario lo pide.
7. **¿Funciona sin Internet?** Sí, incluido el asistente una vez descargado el modelo.
8. **¿Qué no hace?** No es antivirus, no ejecuta scripts, no desactiva protecciones, no vigila en segundo plano.
9. **¿Qué aprendió del proceso?** Que probar el producto instalado revela fallos invisibles en desarrollo: se corrigieron cinco, entre ellos una pantalla en blanco causada por un cambio reciente de WebView2.
10. **¿Siguiente paso?** Ampliar el conjunto realista con dos etiquetadores (kappa de Cohen), firmar el instalador y probar con usuarios reales.

## 7. Evidencias de pruebas

- `docs/pruebas/evaluacion_clasificador.md` — métricas y matrices de confusión.
- `docs/desarrollo/bitacora.md` — fases, errores, soluciones y hashes de commits.
- `docs/capturas/` — 21 capturas reales de la aplicación instalada y del instalador.
- GitHub Actions — pruebas del motor, compilación de la interfaz y del contenedor.

## 8. Instrucciones para usar la demostración

Requisitos: el portátil con ScriptLens instalado, Ollama abierto con `qwen3:4b-instruct`, la carpeta del repositorio (para `demo_consumo.py` y los scripts de ejemplo) y la presentación `ScriptLens_IA_ExpoSoftware.pptx`. Conecte el cargador: con batería, Windows puede reducir el rendimiento y alargar las respuestas del asistente.
