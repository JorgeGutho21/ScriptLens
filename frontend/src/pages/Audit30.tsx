import { CheckCircle2, ChevronDown, CircleSlash, Download, Play, ShieldAlert, ShieldQuestion, XCircle } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Button, Notice } from '../components/controls'
import { Card } from '../components/ui'
import { api, apiPost } from '../lib/api'
import { usePolling } from '../lib/usePolling'

type Estado = 'CUMPLE' | 'NO CUMPLE' | 'REQUIERE REVISIÓN' | 'NO APLICA'

interface Control {
  numero: number
  area: string
  nombre: string
  proposito: string
  estado: Estado
  evidencia: string
  explicacion: string
  recomendacion: string
}

interface Result {
  administrador: boolean
  sistema: string
  controles: Control[]
  resumen: Record<Estado, number>
  cumplimiento_concluyente_pct: number | null
  nota: string
  medido_en: number
  duracion_s: number
}

const STYLE: Record<Estado, { cls: string; icon: ReactNode }> = {
  CUMPLE: { cls: 'bg-ok-soft text-ok', icon: <CheckCircle2 size={15} /> },
  'NO CUMPLE': { cls: 'bg-danger-soft text-danger', icon: <XCircle size={15} /> },
  'REQUIERE REVISIÓN': { cls: 'bg-warn-soft text-warn', icon: <ShieldQuestion size={15} /> },
  'NO APLICA': { cls: 'bg-surface-3 text-muted', icon: <CircleSlash size={15} /> },
}

function Badge({ estado }: { estado: Estado }) {
  const s = STYLE[estado]
  return (
    <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${s.cls}`}>
      {s.icon}
      {estado}
    </span>
  )
}

export function Audit30Page() {
  const [fast, setFast] = useState(false)
  const q = usePolling(() => api<{ ejecutando: boolean; error: string | null; resultado: Result | null }>('/api/audit30'), fast ? 1500 : 10000, [fast])
  const [filter, setFilter] = useState<Estado | 'todos'>('todos')
  const [open, setOpen] = useState<number | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const d = q.data
  const res = d?.resultado
  const running = !!d?.ejecutando
  if (fast && d && !running) setFast(false)

  const run = async () => {
    await apiPost('/api/audit30/run')
    setFast(true)
  }
  const exportAs = async (formato: 'pdf' | 'html') => {
    const r = await apiPost<{ archivo: string; ruta: string }>('/api/audit30/report', { formato })
    setMsg(`Informe guardado en ${r.ruta}`)
    try {
      await apiPost(`/api/reports/open/${encodeURIComponent(r.archivo)}`)
    } catch {
      /* se puede abrir desde Informes */
    }
  }
  const list = (res?.controles ?? []).filter((c) => filter === 'todos' || c.estado === filter)

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5">
      <Card>
        <div className="flex flex-wrap items-start gap-4">
          <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-accent-soft text-accent">
            <ShieldAlert size={24} />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="font-display text-xl font-semibold">Auditoría de Windows — 30 controles</h2>
            <p className="mt-1 text-sm leading-relaxed text-muted">
              Revisa 30 configuraciones de seguridad del taller de Sistemas Operativos: actualizaciones, firewall, Defender, escritorio remoto, SMB, WinRM, cuentas, UAC, BitLocker, Secure Boot, TPM,
              auditoría, PowerShell, carpetas compartidas, servicios y AutoRun. <b className="text-fg">Solo lee la configuración: no cambia nada.</b>
            </p>
          </div>
          <Button tone="primary" icon={<Play size={15} />} onClick={run} disabled={running}>
            {running ? 'Revisando… (unos 15 s)' : res ? 'Volver a revisar' : 'Ejecutar auditoría'}
          </Button>
        </div>
        {d?.error && (
          <div className="mt-4">
            <Notice tone="danger">{d.error}</Notice>
          </div>
        )}
      </Card>

      {res && (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {(['CUMPLE', 'NO CUMPLE', 'REQUIERE REVISIÓN', 'NO APLICA'] as const).map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => setFilter(filter === k ? 'todos' : k)}
                className={`card p-4 text-left transition-colors ${filter === k ? 'border-accent' : 'hover:border-accent/40'}`}
                aria-pressed={filter === k}
              >
                <div className="text-xs text-muted">{k.charAt(0) + k.slice(1).toLowerCase()}</div>
                <div className="tabular font-display text-2xl font-semibold">{res.resumen[k]}</div>
              </button>
            ))}
            <div className="card col-span-2 p-4 sm:col-span-1">
              <div className="text-xs text-muted">Cumplimiento concluyente</div>
              <div className="tabular font-display text-2xl font-semibold">{res.cumplimiento_concluyente_pct ?? '—'} %</div>
            </div>
          </div>
          <p className="-mt-2 text-xs text-faint">
            {res.sistema} · revisado el {new Date(res.medido_en * 1000).toLocaleString('es-CO')} en {res.duracion_s} s. {res.nota}
          </p>
          {!res.administrador && (
            <Notice tone="warn">
              ScriptLens se ejecutó sin permisos de administrador. Algunos controles (auditoría de seguridad, estado del TPM) no se pueden comprobar y quedan como «Requiere revisión»; nunca se marcan como
              aprobados sin evidencia.
            </Notice>
          )}
          <div className="flex flex-wrap gap-2">
            <Button icon={<Download size={15} />} onClick={() => exportAs('pdf')}>
              Informe PDF
            </Button>
            <Button icon={<Download size={15} />} onClick={() => exportAs('html')}>
              Informe HTML
            </Button>
          </div>
          {msg && <Notice tone="ok">{msg}</Notice>}

          <Card title={filter === 'todos' ? 'Los 30 controles' : `Controles: ${filter.toLowerCase()}`}>
            <ul className="flex flex-col divide-y divide-line">
              {list.map((c) => (
                <li key={c.numero}>
                  <button type="button" onClick={() => setOpen(open === c.numero ? null : c.numero)} className="flex w-full items-center gap-3 py-3 text-left" aria-expanded={open === c.numero}>
                    <span className="tabular w-7 shrink-0 text-sm font-semibold text-faint">{String(c.numero).padStart(2, '0')}</span>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium text-fg">{c.nombre}</div>
                      <div className="text-xs text-muted">{c.area}</div>
                    </div>
                    <Badge estado={c.estado} />
                    <ChevronDown size={16} className={`shrink-0 text-faint transition-transform ${open === c.numero ? 'rotate-180' : ''}`} />
                  </button>
                  {open === c.numero && (
                    <dl className="mb-3 ml-10 grid gap-x-4 gap-y-1.5 rounded-xl bg-surface-2 p-3 text-sm sm:grid-cols-[150px_1fr]">
                      <dt className="text-faint">Para qué sirve</dt>
                      <dd>{c.proposito}</dd>
                      <dt className="text-faint">En palabras sencillas</dt>
                      <dd>{c.explicacion}</dd>
                      <dt className="text-faint">Evidencia técnica</dt>
                      <dd className="break-words font-mono text-xs">{c.evidencia}</dd>
                      <dt className="text-faint">Recomendación</dt>
                      <dd>{c.recomendacion}</dd>
                    </dl>
                  )}
                </li>
              ))}
            </ul>
          </Card>
        </>
      )}
    </div>
  )
}
