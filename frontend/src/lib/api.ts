/**
 * Cliente de la API local de ScriptLens.
 *
 * En la aplicación de escritorio, Tauri arranca el backend y entrega el puerto y
 * el token mediante el comando `backend_info`. En desarrollo desde el navegador
 * se usan VITE_BACKEND_URL y VITE_BACKEND_TOKEN.
 */

export interface Sample {
  ts: number
  cpu_percent: number
  cpu_per_core: number[]
  mem_total: number
  mem_used: number
  mem_available: number
  mem_percent: number
  swap_percent: number
  disk_read_bps: number | null
  disk_write_bps: number | null
  net_sent_bps: number | null
  net_recv_bps: number | null
  process_count: number
}

export interface DiskInfo {
  mountpoint: string
  fstype: string
  total: number
  used: number
  free: number
  percent: number
}

export interface SystemInfo {
  os: string
  os_version: string
  machine: string
  processor: string
  cpu_physical: number | null
  cpu_logical: number | null
  cpu_max_mhz: number | null
  mem_total: number
  boot_time: number
  disks: DiskInfo[]
  temperature: { available: boolean; reason: string | null }
}

export type Estado = 'informativo' | 'normal' | 'consumo_elevado' | 'requiere_revision' | 'info_insuficiente'

export interface Finding {
  code: string
  estado: Estado
  titulo: string
  explicacion: string
  evidencia: string
  recomendacion: string
}

export interface Summary {
  current: Sample | null
  window_seconds: number
  averages: { cpu_1m: number | null; ram_1m: number | null; cpu_long: number | null; ram_long: number | null; long_samples: number }
  findings: Finding[]
  scriptlens: { pid: number; memory_rss: number | null; cpu_percent: number | null }
}

export interface ProcessRow {
  pid: number
  name: string
  ppid: number | null
  create_time: number | null
  threads: number | null
  cpu_percent: number | null
  memory_rss: number | null
  acceso_limitado: boolean
}

export type EstadoProceso = Estado | 'actividad_sospechosa' | 'amenaza_detectada'
export type Categoria = 'sistema' | 'servicio' | 'aplicacion' | 'segundo_plano'

export interface ProcessListRow extends ProcessRow {
  session_id: number | null
  private_bytes: number | null
  handles: number | null
  path: string | null
  category: Categoria
  category_label: string
  publisher: string | null
  description: string | null
  signature: 'valida' | 'sin_firma' | 'alterada' | 'no_confiable' | 'desconocido' | 'no_aplica' | 'pendiente' | null
  estado: EstadoProceso
  signals: string[]
  cpu_avg_60s: number | null
}

export interface Signal {
  code: string
  estado: EstadoProceso
  titulo: string
  evidencia: string
  fuente: string
  tipo: 'comprobado' | 'estimado'
}

export interface ProcessDetail extends Omit<ProcessListRow, 'signature' | 'signals'> {
  measured_at: number
  signature: SignatureInfo | null
  signals: Signal[]
  stats: { seconds: number; samples: number; cpu_avg: number | null; cpu_max: number | null; memory_avg: number | null; memory_max: number | null } | null
  parent: { pid: number; name: string; create_time: number | null } | null
  children: { pid: number; name: string; create_time: number | null }[]
  can_terminate: boolean
  terminate_reason: string
  cmdline: string | null
  user: string | null
  status: string | null
  connections: { total: number; establecidas: number; escuchando: number[]; remotas: string[] } | null
  explicacion: { pregunta: string; respuesta: string; tipo: 'comprobado' | 'estimado' }[]
}

export interface SignatureInfo {
  estado: string
  descripcion_estado: string
  firmante: string | null
  binario_windows: boolean
  editor: string | null
  descripcion: string | null
  producto: string | null
  version: string | null
}

export interface SustainedRow {
  pid: number
  name: string
  samples: number
  cpu_avg: number
  cpu_max: number
  memory_avg: number | null
}

interface Connection {
  baseUrl: string
  token: string
}

let connection: Promise<Connection> | null = null

function isTauri(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window
}

async function resolveConnection(): Promise<Connection> {
  if (isTauri()) {
    const { invoke } = await import('@tauri-apps/api/core')
    // Espera a que el backend publique su puerto (el arranque puede tardar unos segundos).
    for (let attempt = 0; attempt < 60; attempt++) {
      const info = await invoke<{ port: number; token: string } | null>('backend_info')
      if (info) return { baseUrl: `http://127.0.0.1:${info.port}`, token: info.token }
      await new Promise((r) => setTimeout(r, 250))
    }
    throw new Error('El motor de análisis no respondió a tiempo.')
  }
  const baseUrl = import.meta.env.VITE_BACKEND_URL as string | undefined
  const token = import.meta.env.VITE_BACKEND_TOKEN as string | undefined
  if (!baseUrl || !token) throw new Error('Falta VITE_BACKEND_URL / VITE_BACKEND_TOKEN para el modo navegador.')
  return { baseUrl, token }
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(method: string, path: string, params?: Record<string, string | number>, body?: unknown): Promise<T> {
  connection ??= resolveConnection().catch((e) => {
    connection = null
    throw e
  })
  const { baseUrl, token } = await connection
  const url = new URL(path, baseUrl)
  if (params) for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v))
  const headers: Record<string, string> = { 'X-ScriptLens-Token': token }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const res = await fetch(url, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined })
  if (!res.ok) {
    let detail = `Error ${res.status}`
    try {
      const j = await res.json()
      if (typeof j.detail === 'string') detail = j.detail
    } catch {
      /* respuesta sin JSON */
    }
    throw new ApiError(res.status, detail)
  }
  return (await res.json()) as T
}

/** POST con respuesta NDJSON (una línea JSON por evento), para respuestas en streaming. */
export async function* apiStream<T>(path: string, body: unknown, signal?: AbortSignal): AsyncGenerator<T> {
  connection ??= resolveConnection().catch((e) => {
    connection = null
    throw e
  })
  const { baseUrl, token } = await connection
  const res = await fetch(new URL(path, baseUrl), { method: 'POST', headers: { 'X-ScriptLens-Token': token, 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal })
  if (!res.ok || !res.body) {
    let detail = `Error ${res.status}`
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      /* sin JSON */
    }
    throw new ApiError(res.status, detail)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    let nl: number
    while ((nl = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, nl).trim()
      buf = buf.slice(nl + 1)
      if (line) yield JSON.parse(line) as T
    }
  }
  if (buf.trim()) yield JSON.parse(buf) as T
}

export const api = <T,>(path: string, params?: Record<string, string | number>) => request<T>('GET', path, params)
export const apiPost = <T,>(path: string, body?: unknown, params?: Record<string, string | number>) => request<T>('POST', path, params, body ?? {})
export const apiDelete = <T,>(path: string) => request<T>('DELETE', path)

/** Abre en el navegador una dirección de la lista permitida por el motor (repositorio, Ollama). */
export const openLink = (url: string) => request('POST', '/api/open-link', undefined, { url })

export interface DiagnosticRow {
  id: number
  created_at: number
  label: string
  window_seconds: number
  cpu_avg: number | null
  ram_avg: number | null
  ram_used: number
  ram_total: number
  process_count: number
}

export interface Comparison {
  a: { id: number | null; label: string; created_at: number; window_seconds: number }
  b: { id: number | null; label: string; created_at: number; window_seconds: number }
  metrics: Record<'cpu_avg' | 'ram_avg' | 'ram_used' | 'process_count', { antes: number | null; despues: number | null; delta: number | null }>
  processes: {
    name: string
    estado: 'nuevo' | 'ausente' | 'presente'
    memory_antes: number | null
    memory_despues: number | null
    memory_delta: number
    cpu_antes: number | null
    cpu_despues: number | null
    cpu_delta: number
    instancias_antes: number
    instancias_despues: number
  }[]
  summary: string[]
  limitaciones: string[]
}
