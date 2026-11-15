# Evaluación del clasificador de scripts

Generado automáticamente por `python -m backend.scripts.train` el 2026-11-14 22:32 (Python 3.12.10, scikit-learn 1.9.1).

## Advertencias de interpretación

- El corpus de entrenamiento es **sintético** y lo generan las mismas reglas que se evalúan; sus cifras **no** deben presentarse como desempeño en el mundo real (advertencia ya presente en la guía original 03B, §11.3).
- El conjunto «realista» tiene solo 18 scripts escritos y etiquetados por **una** persona; el acuerdo entre dos etiquetadores (kappa de Cohen ≥ 0,7) sigue **pendiente**.
- La probabilidad de la clase «sensible» mide el parecido con los ejemplos sensibles del corpus; **no es la probabilidad de que un script sea malware**.

## Corpus sintético (180 scripts) — validación cruzada estratificada de 5 pliegues

### Baseline sin IA (reglas)

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| consulta | 1.0 | 1.0 | 1.0 | 60 |
| modifica | 1.0 | 1.0 | 1.0 | 60 |
| sensible | 1.0 | 1.0 | 1.0 | 60 |

F1 macro: **1.0** · Recall «sensible»: **1.0** · Falsos positivos en «consulta»: **0.0 %**

Matriz de confusión (filas = real, columnas = predicho: consulta, modifica, sensible):

```
consulta  [60, 0, 0]
modifica  [0, 60, 0]
sensible  [0, 0, 60]
```

### Modelo (regresión logística balanceada)

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| consulta | 0.938 | 1.0 | 0.968 | 60 |
| modifica | 0.934 | 0.95 | 0.942 | 60 |
| sensible | 1.0 | 0.917 | 0.957 | 60 |

F1 macro: **0.955** · Recall «sensible»: **0.917** · Falsos positivos en «consulta»: **0.0 %**

Matriz de confusión (filas = real, columnas = predicho: consulta, modifica, sensible):

```
consulta  [60, 0, 0]
modifica  [3, 57, 0]
sensible  [1, 4, 55]
```

### Política híbrida (reglas o p(sensible) ≥ 0.3)

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| consulta | 0.952 | 1.0 | 0.976 | 60 |
| modifica | 1.0 | 0.9 | 0.947 | 60 |
| sensible | 0.952 | 1.0 | 0.976 | 60 |

F1 macro: **0.966** · Recall «sensible»: **1.0** · Falsos positivos en «consulta»: **0.0 %**

Matriz de confusión (filas = real, columnas = predicho: consulta, modifica, sensible):

```
consulta  [60, 0, 0]
modifica  [3, 54, 3]
sensible  [0, 0, 60]
```

## Conjunto realista independiente (18 scripts no vistos en el entrenamiento)

### Baseline sin IA (reglas)

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| consulta | 1.0 | 1.0 | 1.0 | 6 |
| modifica | 1.0 | 1.0 | 1.0 | 6 |
| sensible | 1.0 | 1.0 | 1.0 | 6 |

F1 macro: **1.0** · Recall «sensible»: **1.0** · Falsos positivos en «consulta»: **0.0 %**

Matriz de confusión (filas = real, columnas = predicho: consulta, modifica, sensible):

```
consulta  [6, 0, 0]
modifica  [0, 6, 0]
sensible  [0, 0, 6]
```

### Modelo

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| consulta | 0.75 | 1.0 | 0.857 | 6 |
| modifica | 1.0 | 1.0 | 1.0 | 6 |
| sensible | 1.0 | 0.667 | 0.8 | 6 |

F1 macro: **0.886** · Recall «sensible»: **0.667** · Falsos positivos en «consulta»: **0.0 %**

Matriz de confusión (filas = real, columnas = predicho: consulta, modifica, sensible):

```
consulta  [6, 0, 0]
modifica  [0, 6, 0]
sensible  [2, 0, 4]
```

### Política híbrida

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| consulta | 1.0 | 1.0 | 1.0 | 6 |
| modifica | 1.0 | 1.0 | 1.0 | 6 |
| sensible | 1.0 | 1.0 | 1.0 | 6 |

F1 macro: **1.0** · Recall «sensible»: **1.0** · Falsos positivos en «consulta»: **0.0 %**

Matriz de confusión (filas = real, columnas = predicho: consulta, modifica, sensible):

```
consulta  [6, 0, 0]
modifica  [0, 6, 0]
sensible  [0, 0, 6]
```

### Detalle por script

| Archivo | Real | Reglas | Modelo | p(sensible) | Híbrida |
|---|---|---|---|---|---|
| inventario_equipo.bat.txt | consulta | consulta | consulta | 0.056 | consulta |
| diagnostico_red.cmd.txt | consulta | consulta | consulta | 0.035 | consulta |
| estado_servicios.ps1.txt | consulta | consulta | consulta | 0.028 | consulta |
| espacio_disco.ps1.txt | consulta | consulta | consulta | 0.032 | consulta |
| usuarios_sesion.bat.txt | consulta | consulta | consulta | 0.057 | consulta |
| revisar_eventos.ps1.txt | consulta | consulta | consulta | 0.02 | consulta |
| respaldo_documentos.bat.txt | modifica | modifica | modifica | 0.227 | modifica |
| informe_auditoria.cmd.txt | modifica | modifica | modifica | 0.24 | modifica |
| exportar_inventario.ps1.txt | modifica | modifica | modifica | 0.193 | modifica |
| preferencias_app.ps1.txt | modifica | modifica | modifica | 0.278 | modifica |
| organizar_descargas.ps1.txt | modifica | modifica | modifica | 0.215 | modifica |
| copiar_proyecto.bat.txt | modifica | modifica | modifica | 0.219 | modifica |
| actualizador_falso.bat.txt | sensible | sensible | sensible | 0.943 | sensible |
| limpieza_agresiva.cmd.txt | sensible | sensible | sensible | 0.865 | sensible |
| descargar_y_ejecutar.ps1.txt | sensible | sensible | sensible | 0.567 | sensible |
| tarea_persistente.ps1.txt | sensible | sensible | sensible | 0.744 | sensible |
| cuenta_oculta.bat.txt | sensible | sensible | consulta | 0.3 | sensible |
| ofuscado.ps1.txt | sensible | sensible | consulta | 0.349 | sensible |

Tiempo medio de clasificación por script: 0.0006 s (meta original: < 2 s).
