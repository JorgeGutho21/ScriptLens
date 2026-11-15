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

export async function api<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  connection ??= resolveConnection().catch((e) => {
    connection = null
    throw e
  })
  const { baseUrl, token } = await connection
  const url = new URL(path, baseUrl)
  if (params) for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v))
  const res = await fetch(url, { headers: { 'X-ScriptLens-Token': token } })
  if (!res.ok) throw new Error(`Error ${res.status} al consultar ${path}`)
  return (await res.json()) as T
}
