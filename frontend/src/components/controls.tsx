import type { ReactNode } from 'react'

export function Row({ label, hint, children }: { label: ReactNode; hint?: ReactNode; children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-t border-line py-4 first:border-t-0 first:pt-0">
      <div className="min-w-0 flex-1">
        <div className="text-sm font-medium text-fg">{label}</div>
        {hint && <div className="mt-0.5 text-[13px] text-muted">{hint}</div>}
      </div>
      {children}
    </div>
  )
}

export function Toggle({ checked, onChange, label, disabled = false }: { checked: boolean; onChange: (v: boolean) => void; label: string; disabled?: boolean }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative h-6 w-11 shrink-0 rounded-full transition-colors disabled:opacity-50 ${checked ? 'bg-accent' : 'bg-surface-3'}`}
    >
      <span className={`absolute left-0 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-5' : 'translate-x-0.5'}`} />
    </button>
  )
}

export function Button({
  children,
  onClick,
  tone = 'ghost',
  disabled = false,
  icon,
  type = 'button',
}: {
  children: ReactNode
  onClick?: () => void
  tone?: 'primary' | 'ghost' | 'danger'
  disabled?: boolean
  icon?: ReactNode
  type?: 'button' | 'submit'
}) {
  const cls = {
    primary: 'bg-accent text-white hover:bg-accent-strong',
    ghost: 'border border-line text-fg hover:bg-surface-2',
    danger: 'border border-danger/40 text-danger hover:bg-danger-soft',
  }[tone]
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`inline-flex items-center justify-center gap-2 rounded-xl px-3.5 py-2 text-sm font-medium transition-colors disabled:opacity-50 ${cls}`}>
      {icon}
      {children}
    </button>
  )
}

export function Notice({ tone = 'info', children }: { tone?: 'info' | 'warn' | 'danger' | 'ok'; children: ReactNode }) {
  const cls = { info: 'bg-accent-soft text-fg', warn: 'bg-warn-soft text-fg', danger: 'bg-danger-soft text-fg', ok: 'bg-ok-soft text-fg' }[tone]
  return <div className={`rounded-xl px-3.5 py-2.5 text-sm leading-relaxed ${cls}`}>{children}</div>
}
