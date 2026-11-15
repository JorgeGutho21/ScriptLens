/** Formato de unidades. Se usan unidades binarias (1 GB = 1024³ bytes), igual que Windows. */

const UNITS = ['B', 'KB', 'MB', 'GB', 'TB']

export function bytes(value: number | null | undefined, digits = 1): string {
  if (value == null) return '—'
  let v = value
  let i = 0
  while (v >= 1024 && i < UNITS.length - 1) {
    v /= 1024
    i++
  }
  return `${v.toFixed(i === 0 ? 0 : digits)} ${UNITS[i]}`
}

export function rate(value: number | null | undefined): string {
  if (value == null) return '—'
  return `${bytes(value)}/s`
}

export function pct(value: number | null | undefined, digits = 0): string {
  if (value == null) return '—'
  return `${value.toFixed(digits)} %`
}

export function duration(seconds: number): string {
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (d > 0) return `${d} d ${h} h`
  if (h > 0) return `${h} h ${m} min`
  return `${m} min`
}

export function clock(ts: number): string {
  return new Date(ts * 1000).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export type Level = 'ok' | 'warn' | 'danger'

export function levelFor(percent: number | null | undefined, warn = 70, danger = 88): Level {
  if (percent == null) return 'ok'
  if (percent >= danger) return 'danger'
  if (percent >= warn) return 'warn'
  return 'ok'
}
