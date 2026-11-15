import type { ReactNode } from 'react'
import { levelFor } from '../lib/format'

const COLORS = { ok: 'var(--accent)', warn: 'var(--warn)', danger: 'var(--danger)' }

/** Indicador circular de porcentaje. El color cambia solo cuando el valor lo amerita. */
export function Gauge({
  value,
  label,
  sublabel,
  size = 168,
  color,
}: {
  value: number | null
  label: ReactNode
  sublabel?: ReactNode
  size?: number
  color?: string
}) {
  const stroke = 12
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const v = Math.max(0, Math.min(100, value ?? 0))
  const level = levelFor(value)
  const tone = level === 'ok' ? (color ?? COLORS.ok) : COLORS[level]

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`${value?.toFixed(0) ?? 'sin datos'} por ciento`}>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-3)" strokeWidth={stroke} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={tone}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={c * (1 - v / 100)}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke-dashoffset 0.8s cubic-bezier(.2,.7,.2,1), stroke 0.4s', filter: `drop-shadow(0 0 6px ${tone}55)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="tabular font-display text-4xl font-semibold tracking-tight text-fg">
            {value == null ? '—' : v.toFixed(0)}
            <span className="ml-0.5 text-lg font-medium text-muted">%</span>
          </div>
          {sublabel && <div className="mt-0.5 text-xs text-muted tabular">{sublabel}</div>}
        </div>
      </div>
      <div className="text-sm font-medium text-muted">{label}</div>
    </div>
  )
}
