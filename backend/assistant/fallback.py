"""Respuestas sin modelo de lenguaje (cuando Ollama no está disponible).

Se construyen con plantillas a partir de los mismos datos medidos, de modo que
el asistente funciona aunque el usuario no instale Ollama.
"""

from __future__ import annotations


def _fmt(v, unit=""):
    return "—" if v is None else f"{v}{unit}"


def answer(route: dict, data: dict) -> str:
    parts: list[str] = []
    r = data.get("resumen_rendimiento")
    if r:
        parts.append(
            f"Ahora el procesador está al {_fmt(r['cpu_ahora_pct'], ' %')} (promedio del último minuto: {_fmt(r['cpu_prom_1min_pct'], ' %')}) "
            f"y la memoria RAM al {_fmt(r['ram_ahora_pct'], ' %')} ({r['ram_usada_gb']} GB de {r['ram_total_gb']} GB)."
        )
        for f in r["hallazgos"][:2]:
            parts.append(f"{f['titulo']}. {f['evidencia']}")
    for key, label, field, unit in (("procesos_top_memoria", "Programas que más memoria usan", "ram_mb", " MB"), ("procesos_top_cpu", "Programas que más procesador usan (promedio de 1 minuto)", "cpu_prom_1min_pct", " %")):
        t = data.get(key)
        if t:
            items = ", ".join(f"{p['nombre']} ({p[field]}{unit})" for p in t["programas"][:5])
            parts.append(f"{label}: {items}.")
    c = data.get("cerrables")
    if c:
        apps = c["aplicaciones_abiertas_no_esenciales"]
        if apps:
            parts.append("Aplicaciones abiertas que puede cerrar sin afectar a Windows (guarde antes su trabajo): " + ", ".join(f"{a['nombre']} ({a['ram_mb']} MB)" for a in apps[:6]) + ".")
        else:
            parts.append("No hay aplicaciones abiertas no esenciales con consumo destacable.")
    b = data.get("segundo_plano")
    if b:
        parts.append("Procesos por tipo: " + ", ".join(f"{k}: {v}" for k, v in b["conteo_por_tipo"].items()) + ".")
        parts.append("En segundo plano, los que más memoria usan: " + ", ".join(f"{p['nombre']} ({p['ram_mb']} MB)" for p in b["mayor_consumo_en_segundo_plano"][:5]) + ".")
    s = data.get("seguridad")
    if s and s.get("disponible"):
        parts.append(
            f"Microsoft Defender: antivirus {'activo' if s['antivirus_activo'] else 'no confirmado'}, protección en tiempo real {'activa' if s['proteccion_tiempo_real'] else 'no confirmada'}; "
            f"amenazas activas registradas por Defender: {s['amenazas_activas_defender']}."
        )
        relevantes = [h for h in s["hallazgos"] if h["estado"] in ("requiere_revision", "amenaza_detectada", "actividad_sospechosa")]
        if relevantes:
            parts.append("Requieren revisión: " + "; ".join(h["que"] for h in relevantes[:4]) + ". Esto no significa que sean maliciosos.")
    rv = data.get("en_revision")
    if rv and rv["procesos"]:
        parts.append("Procesos con señales para revisar: " + ", ".join(f"{p['nombre']} ({p['estado'].replace('_', ' ')})" for p in rv["procesos"][:5]) + ".")
    elif rv:
        parts.append("Ningún proceso en ejecución muestra señales que requieran revisión con la evidencia disponible.")
    i = data.get("inicio_automatico")
    if i and i.get("entradas") is not None:
        on = [e["nombre"] for e in i["entradas"] if e["habilitado"]]
        parts.append(f"Programas que inician con Windows ({len(on)} habilitados): {', '.join(on) or 'ninguno'}.")
    t = data.get("tareas")
    if t and t.get("de_otros_programas") is not None:
        parts.append(f"Hay {t['total_activas']} tareas programadas activas; {t['de_windows']} son de Windows. De otros programas: " + ", ".join(x["nombre"] for x in t["de_otros_programas"][:8]) + ".")
    d = data.get("disco")
    if d:
        parts.append("Almacenamiento: " + "; ".join(f"{u['unidad']} {u['usado_pct']} % usado, {u['libre_gb']} GB libres" for u in d["unidades"]) + ".")
    ch = data.get("cambios")
    if ch:
        parts.extend(ch["resumen"] if ch.get("disponible") else [ch["motivo"]])
    sc = data.get("ultimo_script")
    if sc:
        if sc.get("disponible"):
            parts.append(f"El script «{sc['archivo']}» se clasificó como {sc['decision_hibrida']} (severidad {sc['severidad']}).")
            parts.extend(f"Línea {l['n']}: {l['explicacion']}" for l in sc["lineas"][:25] if l["explicacion"])
        else:
            parts.append(sc["motivo"])
    p = data.get("proceso")
    if p:
        if p.get("encontrado"):
            parts.append(
                f"{p['nombre']}: {p['conocimiento'] or p['descripcion_archivo'] or 'sin descripción disponible'}. "
                f"Usa {p['ram_total_mb']} MB en {p['instancias']} proceso(s). Firma: {p['firma']}"
                + (f" ({p['firmante']})" if p.get("firmante") else "")
                + ". "
                + ("ScriptLens no permite finalizarlo porque es esencial." if not p["se_puede_finalizar_desde_scriptlens"] else "Puede cerrarlo desde Procesos con confirmación.")
            )
        else:
            parts.append(f"No hay ningún proceso llamado «{p['nombre']}» en ejecución." + (f" Información general: {p['conocimiento']}" if p.get("conocimiento") else ""))
    if not parts:
        parts.append("No tengo datos suficientes para responder esa pregunta.")
    return "\n\n".join(parts)
