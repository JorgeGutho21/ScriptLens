import type { ReactNode } from 'react'
import { AlertTriangle, CheckCircle2, Info, SearchCheck, HelpCircle } from 'lucide-react'
import type { Estado } from '../lib/api'

export function Card({ title, action, children, className = '' }: { title?: ReactNode; action?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`card animate-rise p-5 ${className}`}>
      {(title || action) && (
        <header className="mb-4 flex items-center justify-between gap-3">
          {title && <h2 className="text-[13px] font-semibold uppercase tracking-[0.06em] text-muted">{title}</h2>}
          {action}
        </header>
      )}
      {children}
    </section>
  )
}

export function Stat({ icon, label, value, hint }: { icon: ReactNode; label: ReactNode; value: ReactNode; hint?: ReactNode }) {
  return (
    <div className="card animate-rise flex items-start gap-3.5 p-4">
      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-accent-soft text-accent">{icon}</div>
      <div className="min-w-0">
        <div className="text-[12.5px] text-muted">{label}</div>
        <div className="tabular truncate font-display text-xl font-semibold text-fg">{value}</div>
        {hint && <div className="tabular mt-0.5 truncate text-xs text-faint">{hint}</div>}
      </div>
    </div>
  )
}

const ESTADOS: Record<Estado, { label: string; cls: string; icon: ReactNode }> = {
  normal: { label: 'Normal', cls: 'bg-ok-soft text-ok', icon: <CheckCircle2 size={15} /> },
  informativo: { label: 'Informativo', cls: 'bg-accent-soft text-info', icon: <Info size={15} /> },
  consumo_elevado: { label: 'Consumo elevado', cls: 'bg-warn-soft text-warn', icon: <AlertTriangle size={15} /> },
  requiere_revision: { label: 'Requiere revisión', cls: 'bg-danger-soft text-danger', icon: <SearchCheck size={15} /> },
  info_insuficiente: { label: 'Información insuficiente', cls: 'bg-surface-3 text-muted', icon: <HelpCircle size={15} /> },
}

export function EstadoBadge({ estado }: { estado: Estado }) {
  const e = ESTADOS[estado]
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${e.cls}`}>
      {e.icon}
      {e.label}
    </span>
  )
}

export function Bar({ value, tone = 'var(--accent)' }: { value: number; tone?: string }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-3">
      <div className="h-full rounded-full transition-[width] duration-700" style={{ width: `${Math.max(0, Math.min(100, value))}%`, background: tone }} />
    </div>
  )
}

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`pulse-dot rounded-lg bg-surface-3 ${className}`} />
}
