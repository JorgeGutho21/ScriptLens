// Vista remota de ScriptLens IA (solo lectura). Sin dependencias externas.
// Todo texto que llega de la PC se inserta con textContent: nunca como HTML.
'use strict'

const $ = (id) => document.getElementById(id)
const state = { by: 'cpu', cpuHist: [], ramHist: [], lastOk: 0, lastMeasured: 0, timers: [], requestId: null }
const STALE_AFTER = 10 // s sin una medición nueva → no se presenta como actual

function el(tag, text, cls) {
  const e = document.createElement(tag)
  if (text != null) e.textContent = text
  if (cls) e.className = cls
  return e
}

const GB = 1024 ** 3
function bytes(v) {
  if (v == null) return '—'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++ }
  return `${v.toFixed(i ? 1 : 0)} ${u[i]}`
}
const rate = (v) => (v == null ? '—' : `${bytes(v)}/s`)
const pct = (v) => (v == null ? '—' : `${Math.round(v)} %`)
function dur(s) {
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60)
  return d ? `${d} d ${h} h` : h ? `${h} h ${m} min` : `${m} min`
}
const hhmm = (ts) => new Date(ts * 1000).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
const dateTime = (ts) => new Date(ts * 1000).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })

async function get(path) {
  const r = await fetch(path, { credentials: 'same-origin', cache: 'no-store' })
  if (r.status === 401) throw Object.assign(new Error('auth'), { auth: true })
  if (!r.ok) {
    let msg = `Error ${r.status}`
    try { msg = (await r.json()).detail || msg } catch { /* sin JSON */ }
    throw Object.assign(new Error(msg), { status: r.status })
  }
  return r.json()
}

function show(id) {
  for (const s of ['pair', 'wait', 'dash']) $(s).hidden = s !== id
}

function setConn(kind, text) {
  $('conn').className = `conn ${kind}`
  $('conn-text').textContent = text
}

// --- Vinculación ---------------------------------------------------------
$('pair-form').addEventListener('submit', async (ev) => {
  ev.preventDefault()
  $('pair-msg').textContent = ''
  $('pair-btn').disabled = true
  try {
    const r = await fetch('/remote/api/pair/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ codigo: $('code').value.trim(), nombre: $('devname').value.trim(), tipo: 'navegador' }),
    })
    const j = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(typeof j.detail === 'string' ? j.detail : 'Revise el código e inténtelo de nuevo.')
    state.requestId = j.solicitud
    $('phrase').textContent = j.frase
    $('fp').textContent = j.huella || '—'
    $('pc-name').textContent = j.equipo
    show('wait')
    waitApproval()
  } catch (e) {
    $('pair-msg').textContent = e.message
  } finally {
    $('pair-btn').disabled = false
  }
})

$('cancel').addEventListener('click', () => { state.requestId = null; show('pair') })

async function waitApproval() {
  const id = state.requestId
  while (state.requestId === id) {
    await new Promise((r) => setTimeout(r, 2000))
    if (state.requestId !== id) return
    try {
      const j = await get(`/remote/api/pair/status?solicitud=${encodeURIComponent(id)}`)
      if (j.estado === 'autorizada') { state.requestId = null; return start() }
      if (j.estado === 'rechazada' || j.estado === 'caducada') {
        state.requestId = null
        show('pair')
        $('pair-msg').textContent = j.estado === 'rechazada' ? 'La PC rechazó la solicitud.' : 'La solicitud caducó. Pida un código nuevo.'
        return
      }
    } catch { /* la PC puede no responder un momento; se reintenta */ }
  }
}

// --- Panel ---------------------------------------------------------------
function spark(canvas, values, color) {
  const dpr = window.devicePixelRatio || 1
  const w = canvas.clientWidth, h = canvas.clientHeight
  canvas.width = w * dpr; canvas.height = h * dpr
  const c = canvas.getContext('2d')
  c.scale(dpr, dpr)
  c.clearRect(0, 0, w, h)
  if (values.length < 2) return
  c.beginPath()
  values.forEach((v, i) => {
    const x = (i / (values.length - 1)) * w, y = h - (Math.max(0, Math.min(100, v)) / 100) * (h - 2) - 1
    i ? c.lineTo(x, y) : c.moveTo(x, y)
  })
  c.strokeStyle = color; c.lineWidth = 2; c.stroke()
  c.lineTo(w, h); c.lineTo(0, h); c.closePath()
  c.globalAlpha = 0.15; c.fillStyle = color; c.fill()
}

function cssVar(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim() }

function renderOverview(o) {
  const s = o.actual
  $('pc-name').textContent = `${o.equipo} · ${o.so}`
  state.lastMeasured = o.medido_en || 0
  const skew = (o.hora_servidor || 0) - Date.now() / 1000 // reloj de la PC frente al del celular
  state.skew = skew
  if (s) {
    $('cpu').textContent = pct(s.cpu_percent)
    $('ram').textContent = pct(s.mem_percent)
    $('ram-detail').textContent = `${(s.mem_used / GB).toFixed(1)} de ${(s.mem_total / GB).toFixed(1)} GB`
    $('net').textContent = `↑ ${rate(s.net_sent_bps)}  ↓ ${rate(s.net_recv_bps)}`
    $('diskio').textContent = `Lee ${rate(s.disk_read_bps)} · Escribe ${rate(s.disk_write_bps)}`
    if (s.ts !== state.lastTs) {
      state.lastTs = s.ts
      state.cpuHist.push(s.cpu_percent); state.ramHist.push(s.mem_percent)
      state.cpuHist = state.cpuHist.slice(-150); state.ramHist = state.ramHist.slice(-150)
    }
    spark($('cpu-chart'), state.cpuHist, cssVar('--cpu'))
    spark($('ram-chart'), state.ramHist, cssVar('--ram'))
    const cores = $('cores')
    cores.replaceChildren(...s.cpu_per_core.map((v, i) => {
      const d = el('div', null, 'core'), bar = el('div', null, 'bar'), fill = el('i')
      fill.style.height = `${Math.max(0, Math.min(100, v))}%`
      bar.append(fill); d.append(bar, el('span', `${i + 1}: ${Math.round(v)}%`))
      return d
    }))
  }
  $('uptime').textContent = dur(o.tiempo_encendido_s)
  $('boot').textContent = `Encendida desde ${dateTime(o.arranque)}`
  const sys = $('sys')
  const rows = [['Equipo', o.equipo], ['Sistema', `${o.so} (${o.so_version})`], ['Procesador', o.procesador || '—'], ['Núcleos', `${o.nucleos_fisicos ?? '—'} físicos · ${o.nucleos_logicos ?? '—'} lógicos`], ['RAM total', bytes(o.ram_total)], ['Procesos', s ? String(s.process_count) : '—'], ['ScriptLens', `v${o.version}`]]
  sys.replaceChildren(...rows.flatMap(([k, v]) => [el('dt', k), el('dd', v)]))
  $('disks').replaceChildren(...o.discos.map((d) => {
    const box = el('div', null, 'disk'), row = el('div', null, 'row')
    row.append(el('span', d.unidad), el('span', `${bytes(d.libre)} libres de ${bytes(d.total)}`, 'muted'))
    const t = el('div', null, 'track'), f = el('i', null, d.porcentaje >= 90 ? 'danger' : d.porcentaje >= 80 ? 'warn' : '')
    f.style.width = `${d.porcentaje}%`
    t.append(f); box.append(row, t)
    return box
  }))
}

function renderProcesses(p) {
  $('procs').replaceChildren(...p.programas.map((x) => {
    const tr = el('tr')
    const name = el('td', x.instancias > 1 ? `${x.nombre} (${x.instancias})` : x.nombre)
    name.title = x.tipo
    tr.append(name, el('td', `${x.cpu_prom_1min_pct.toFixed(1)} %`), el('td', `${x.ram_mb.toFixed(0)} MB`))
    return tr
  }))
  $('proc-note').textContent = `${p.criterio}. Medido a las ${hhmm(p.medido_en)}.`
}

function renderFindings(f) {
  $('findings').replaceChildren(...f.rendimiento.map((h) => {
    const li = el('li', h.titulo, h.estado)
    li.append(el('small', h.evidencia))
    return li
  }))
  const box = $('security')
  box.replaceChildren()
  const s = f.seguridad
  if (s) {
    box.append(el('h2', `Seguridad (revisada ${s.medido})`, 'sp'))
    const dl = el('dl', null, 'sys')
    const fw = Object.entries(s.firewall).map(([k, v]) => `${k}: ${v ? 'activo' : 'desactivado'}`).join(', ')
    for (const [k, v] of [['Antivirus', s.antivirus_activo ? 'Activo' : 'No confirmado'], ['Tiempo real', s.proteccion_tiempo_real ? 'Activa' : 'No confirmada'], ['Firewall', fw], ['Amenazas (Defender)', String(s.amenazas_activas_defender)]]) dl.append(el('dt', k), el('dd', v))
    box.append(dl)
    if (s.hallazgos.length) {
      const ul = el('ul', null, 'findings')
      for (const h of s.hallazgos) ul.append(el('li', h.que, h.estado))
      box.append(ul)
    }
  } else {
    box.append(el('p', 'La PC no comparte una revisión de seguridad reciente.', 'muted small'))
  }
}

function renderStats(st) {
  if (!st || !st.disponible) { $('stats-card').hidden = true; return }
  $('stats-card').hidden = false
  const rows = [['Tiempo encendido hoy', dur(st.encendido_s)], ['Uso activo hoy', dur(st.activo_s)], ['CPU promedio', pct(st.cpu_prom)], ['RAM promedio', pct(st.ram_prom)]]
  if (st.primer_arranque) rows.push(['Primer encendido', dateTime(st.primer_arranque)])
  $('stats').replaceChildren(...rows.flatMap(([k, v]) => [el('dt', k), el('dd', v)]))
}

function freshness() {
  const now = Date.now() / 1000 + (state.skew || 0)
  const age = state.lastMeasured ? now - state.lastMeasured : Infinity
  const offline = Date.now() / 1000 - state.lastOk > STALE_AFTER
  if (!state.lastMeasured) return
  if (offline) {
    setConn('off', 'Desconectado')
    $('fresh').textContent = `Sin conexión con la PC. Última lectura: ${hhmm(state.lastMeasured)} (no son datos actuales).`
    $('dash').classList.add('stale-data')
  } else if (age > STALE_AFTER) {
    setConn('stale', 'Datos atrasados')
    $('fresh').textContent = `La PC no ha enviado mediciones nuevas desde las ${hhmm(state.lastMeasured)}.`
    $('dash').classList.add('stale-data')
  } else {
    setConn('ok', 'En vivo')
    $('fresh').textContent = `Medido en la PC a las ${hhmm(state.lastMeasured)}`
    $('dash').classList.remove('stale-data')
  }
}

function loop(fn, ms) {
  const tick = async () => {
    if (document.visibilityState === 'visible') {
      try {
        await fn()
        state.lastOk = Date.now() / 1000
      } catch (e) {
        if (e.auth) return stop(true)
      }
    }
    state.timers.push(setTimeout(tick, ms))
  }
  tick()
}

function stop(revoked) {
  state.timers.forEach(clearTimeout)
  state.timers = []
  if (revoked) {
    show('pair')
    setConn('off', 'Sin sesión')
    $('pair-msg').textContent = state.lastOk ? 'La sesión terminó o fue revocada desde la PC. Vincule de nuevo si tiene permiso.' : ''
    $('dash').classList.remove('stale-data')
  }
}

async function start() {
  stop(false)
  let who
  try {
    who = await get('/remote/api/whoami')
  } catch (e) {
    show('pair')
    setConn('off', e.auth ? 'Sin vincular' : 'Sin conexión')
    if (!e.auth) $('pair-msg').textContent = e.message
    return
  }
  show('dash')
  $('proc-card').hidden = !who.comparte.procesos
  try {
    const h = await get('/remote/api/history?seconds=300')
    state.cpuHist = h.muestras.map((s) => s.cpu_percent)
    state.ramHist = h.muestras.map((s) => s.mem_percent)
  } catch { /* el historial es opcional */ }
  loop(async () => renderOverview(await get('/remote/api/overview')), 2000)
  if (who.comparte.procesos) loop(async () => renderProcesses(await get(`/remote/api/processes?by=${state.by}&limit=8`)), 5000)
  loop(async () => renderFindings(await get('/remote/api/findings')), 15000)
  if (who.comparte.estadisticas) loop(async () => renderStats(await get('/remote/api/stats?period=dia')), 60000)
  state.timers.push(setInterval(freshness, 1000))
}

document.querySelectorAll('.seg button').forEach((b) => b.addEventListener('click', async () => {
  state.by = b.dataset.by
  document.querySelectorAll('.seg button').forEach((x) => x.setAttribute('aria-checked', String(x === b)))
  try { renderProcesses(await get(`/remote/api/processes?by=${state.by}&limit=8`)) } catch { /* siguiente ciclo */ }
}))

$('logout').addEventListener('click', async () => {
  try { await fetch('/remote/api/logout', { method: 'POST', credentials: 'same-origin' }) } catch { /* sin conexión */ }
  state.lastOk = 0
  stop(true)
})

window.addEventListener('resize', () => {
  spark($('cpu-chart'), state.cpuHist, cssVar('--cpu'))
  spark($('ram-chart'), state.ramHist, cssVar('--ram'))
})

start()
