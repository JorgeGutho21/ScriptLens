import { CheckCircle2, ChevronRight, Flame, Play, RefreshCcw, Shield, ShieldAlert, ShieldCheck, XCircle } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { EstadoPill, FirmaTag } from '../components/Badges'
import { Card, Skeleton } from '../components/ui'
import { api, apiPost, type EstadoProceso } from '../lib/api'
import { StartupActions } from './StartupActions'

export interface AuditFinding {
  code: string
  estado: EstadoProceso
  categoria: string
  que: string
  donde: string
  por_que: string
  evidencia: string
  falta: string
  consecuencias: string
  que_hacer: string
  no_hacer: string
  fuente: string
  medido_en: number
}

interface Sig {
  estado: string
  descripcion_estado: string
  firmante: string | null
}

export interface StartupItem {
  id: string
  nombre: string
  comando: string
  ejecutable: string | null
  origen: string
  ambito: string
  habilitado: boolean
  modificable_sin_admin: boolean
  scope: string
  firma: Sig | null
  estado: EstadoProceso
  motivos: string[]
}

export interface AuditResult {
  measured_at: number
  duration_s: number
  sources: Record<string, { etiqueta: string; ok: boolean; error: string | null; registros: number }>
  defender: Record<string, unknown> | null
  av_products: { displayName: string }[]
  firewall: { Name: string; Enabled: boolean }[]
  startup: StartupItem[]
  tasks: { total: number; de_microsoft: number; otras: { nombre: string; ruta: string; estado_tarea: string; autor: string | null; acciones: { exe: string; args: string | null }[]; firma: Sig | null; estado: EstadoProceso; motivos: string[] }[] }
  services: { total: number; en_ejecucion: number; automaticos: number; de_terceros_automaticos: { nombre: string; mostrado: string; estado: string; ejecutable: string; firma: Sig | null }[] }
  events: { total: number; grupos: { proveedor: string; id: number; nivel: string; veces: number; ultima: string }[] }
  users: { total: number; habilitadas: number; sesiones: number }
  power_plan: string | null
  findings: AuditFinding[]
  counts: Record<string, number>
}

type Tab = 'hallazgos' | 'inicio' | 'tareas' | 'servicios' | 'eventos' | 'fuentes'

export function SecurityPage() {
  const [state, setState] = useState<{ running: boolean; error: string | null; result: AuditResult | null } | null>(null)
  const [tab, setTab] = useState<Tab>('hallazgos')

  const poll = async () => {
    const s = await api<{ running: boolean; error: string | null; result: AuditResult | null }>('/api/security/audit')
    setState(s)
    return s
  }

  const start = async () => {
    await apiPost('/api/security/audit')
    setState((s) => ({ running: true, error: null, result: s?.result ?? null }))
  }

  useEffect(() => {
    poll().then((s) => {
      if (!s.result && !s.running) start()
    })
  }, [])

  useEffect(() => {
    if (!state?.running) return
    const id = window.setInterval(poll, 1500)
    return () => window.clearInterval(id)
  }, [state?.running])

  const r = state?.result
  const d = r?.defender as Record<string, unknown> | null | undefined

  return (
    <div className="mx-auto flex max-w-[1300px] flex-col gap-5">
      <section className="card animate-rise flex flex-wrap items-center gap-5 p-5">
        <div className="grid h-12 w-12 place-items-center rounded-2xl bg-accent-soft text-accent">
          <Shield size={24} />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="font-display text-lg font-semibold">Auditoría de seguridad de solo lectura</h2>
          <p className="text-sm text-muted">
            Revisa Microsoft Defender, el firewall, los programas que inician con Windows, las tareas programadas, los servicios y los eventos del sistema. No modifica nada y no es un antivirus.
          </p>
          {r && <p className="mt-1 text-xs text-faint">Última revisión: {new Date(r.measured_at * 1000).toLocaleString('es-CO')} · {r.duration_s} s</p>}
        </div>
        <button onClick={start} disabled={state?.running} className="flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-strong disabled:opacity-60">
          {state?.running ? <RefreshCcw size={16} className="animate-spin" /> : r ? <RefreshCcw size={16} /> : <Play size={16} />}
          {state?.running ? 'Revisando…' : r ? 'Volver a revisar' : 'Revisar ahora'}
        </button>
      </section>

      {state?.error && <p className="rounded-xl bg-danger-soft p-4 text-sm text-danger">{state.error}</p>}
      {!r && <Skeleton className="h-64 w-full" />}

      {r && (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
            <Status ok={!!d?.AntivirusEnabled} label="Antivirus" value={d ? (d.AntivirusEnabled ? 'Activo' : 'Desactivado') : r.av_products.map((a) => a.displayName).join(', ') || 'Sin datos'} />
            <Status ok={!!d?.RealTimeProtectionEnabled} label="Protección en tiempo real" value={d ? (d.RealTimeProtectionEnabled ? 'Activa' : 'Desactivada') : '—'} />
            <Status ok={typeof d?.AntivirusSignatureAge === 'number' && (d.AntivirusSignatureAge as number) < 7} label="Definiciones" value={typeof d?.AntivirusSignatureAge === 'number' ? `${d.AntivirusSignatureAge} día(s)` : '—'} />
            <Status ok={r.firewall.length > 0 && r.firewall.every((f) => f.Enabled)} label="Firewall" value={r.firewall.length ? `${r.firewall.filter((f) => f.Enabled).length} de ${r.firewall.length} perfiles` : 'Sin datos'} />
            <Status ok={!r.counts.amenaza_detectada} label="Amenazas activas (Defender)" value={String(r.counts.amenaza_detectada ?? 0)} icon={<Flame size={18} />} />
          </div>

          <Card className="!p-0">
            <div role="tablist" aria-label="Secciones de la auditoría" className="flex flex-wrap gap-1 border-b border-line px-3 pt-3">
              {(
                [
                  ['hallazgos', `Hallazgos (${r.findings.length})`],
                  ['inicio', `Inicio automático (${r.startup.length})`],
                  ['tareas', `Tareas programadas (${r.tasks.otras.length})`],
                  ['servicios', `Servicios (${r.services.de_terceros_automaticos.length})`],
                  ['eventos', `Eventos (${r.events.total})`],
                  ['fuentes', 'Qué se revisó'],
                ] as [Tab, string][]
              ).map(([id, label]) => (
                <button
                  key={id}
                  role="tab"
                  aria-selected={tab === id}
                  onClick={() => setTab(id)}
                  className={`rounded-t-xl border-b-2 px-3.5 py-2.5 text-sm ${tab === id ? 'border-accent font-medium text-fg' : 'border-transparent text-muted hover:text-fg'}`}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="p-5" role="tabpanel">
              {tab === 'hallazgos' && <Findings findings={r.findings} />}
              {tab === 'inicio' && <StartupTab items={r.startup} onChanged={start} />}
              {tab === 'tareas' && <TasksTab r={r} />}
              {tab === 'servicios' && <ServicesTab r={r} />}
              {tab === 'eventos' && <EventsTab r={r} />}
              {tab === 'fuentes' && <SourcesTab r={r} />}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}

function Status({ ok, label, value, icon }: { ok: boolean; label: string; value: string; icon?: ReactNode }) {
  return (
    <div className="card animate-rise flex items-center gap-3 p-4">
      <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${ok ? 'bg-ok-soft text-ok' : 'bg-warn-soft text-warn'}`}>{icon ?? (ok ? <ShieldCheck size={19} /> : <ShieldAlert size={19} />)}</div>
      <div className="min-w-0">
        <div className="text-xs text-muted">{label}</div>
        <div className="truncate font-medium text-fg">{value}</div>
      </div>
    </div>
  )
}

export function FindingCard({ f, defaultOpen = false }: { f: AuditFinding; defaultOpen?: boolean }) {
  const rows: [string, string][] = [
    ['Dónde', f.donde],
    ['Por qué requiere atención', f.por_que],
    ['Evidencia', f.evidencia],
    ['Qué información falta', f.falta],
    ['Posibles consecuencias', f.consecuencias],
    ['Qué puede hacer', f.que_hacer],
    ['Qué no se recomienda', f.no_hacer],
  ]
  return (
    <details className="group rounded-xl border border-line bg-surface-2" open={defaultOpen}>
      <summary className="flex cursor-pointer list-none items-center gap-3 p-3.5">
        <ChevronRight size={16} className="shrink-0 text-faint transition-transform group-open:rotate-90" />
        <EstadoPill estado={f.estado} />
        <span className="min-w-0 flex-1 truncate text-sm font-medium text-fg">{f.que}</span>
        <span className="hidden text-xs text-faint md:inline">{f.categoria}</span>
      </summary>
      <dl className="grid grid-cols-1 gap-x-6 gap-y-2.5 border-t border-line px-4 py-3.5 text-[13.5px] md:grid-cols-[200px_1fr]">
        {rows.map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="text-faint">{k}</dt>
            <dd className={`break-words ${k === 'Qué no se recomienda' ? 'text-warn' : 'text-fg'}`}>{v}</dd>
          </div>
        ))}
        <dt className="text-faint">Fuente y fecha</dt>
        <dd className="text-muted">{f.fuente} · {new Date(f.medido_en * 1000).toLocaleString('es-CO')}</dd>
      </dl>
    </details>
  )
}

function Findings({ findings }: { findings: AuditFinding[] }) {
  if (findings.length === 0)
    return (
      <div className="flex items-center gap-3 rounded-xl bg-ok-soft p-4 text-ok">
        <CheckCircle2 /> No se encontraron aspectos que requieran revisión con la información disponible.
      </div>
    )
  return (
    <div className="space-y-2">
      {findings.map((f, i) => (
        <FindingCard key={f.code} f={f} defaultOpen={i === 0 && f.estado !== 'informativo'} />
      ))}
    </div>
  )
}

function StartupTab({ items, onChanged }: { items: StartupItem[]; onChanged: () => void }) {
  return (
    <div className="overflow-x-auto">
      <p className="mb-3 text-[13px] text-muted">Programas que se abren automáticamente al iniciar sesión. Desactivar uno no lo desinstala: solo evita que arranque solo.</p>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-faint">
            <th className="pb-2 font-normal">Programa</th>
            <th className="pb-2 font-normal">Origen</th>
            <th className="pb-2 font-normal">Firma</th>
            <th className="pb-2 font-normal">Estado</th>
            <th className="pb-2 text-right font-normal">Inicio</th>
          </tr>
        </thead>
        <tbody>
          {items.map((e) => (
            <tr key={e.id} className="border-t border-line align-top">
              <td className="max-w-[340px] py-2.5 pr-3">
                <div className="font-medium text-fg">{e.nombre}</div>
                <div className="truncate font-mono text-[11px] text-faint" title={e.comando}>{e.comando}</div>
                {e.motivos.map((m) => (
                  <div key={m} className="mt-0.5 text-xs text-warn">• {m}</div>
                ))}
              </td>
              <td className="py-2.5 pr-3 text-xs text-muted">{e.origen}</td>
              <td className="py-2.5 pr-3">
                <FirmaTag estado={e.firma?.estado ?? null} />
                {e.firma?.firmante && <div className="text-[11px] text-faint">{e.firma.firmante}</div>}
              </td>
              <td className="py-2.5 pr-3"><EstadoPill estado={e.estado} compact={e.estado === 'normal'} /></td>
              <td className="py-2.5 text-right">
                <StartupActions item={e} onChanged={onChanged} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function TasksTab({ r }: { r: AuditResult }) {
  return (
    <div>
      <p className="mb-3 text-[13px] text-muted">
        {r.tasks.total} tareas activas en total; {r.tasks.de_microsoft} pertenecen a Windows (carpeta \Microsoft\) y se omiten. Se muestran las {r.tasks.otras.length} de otros programas.
      </p>
      <div className="space-y-2">
        {r.tasks.otras.map((t) => (
          <div key={t.ruta + t.nombre} className="rounded-xl border border-line bg-surface-2 p-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-fg">{t.nombre}</span>
              <EstadoPill estado={t.estado} compact={t.estado === 'normal'} />
              <FirmaTag estado={t.firma?.estado ?? null} />
              <span className="ml-auto text-xs text-faint">{t.autor ?? 'Autor no indicado'}</span>
            </div>
            {t.acciones.map((a, i) => (
              <div key={i} className="mt-1 break-all font-mono text-[11.5px] text-muted">{a.exe} {a.args ?? ''}</div>
            ))}
            {t.motivos.map((m) => <div key={m} className="mt-1 text-xs text-warn">• {m}</div>)}
          </div>
        ))}
      </div>
    </div>
  )
}

function ServicesTab({ r }: { r: AuditResult }) {
  return (
    <div>
      <p className="mb-3 text-[13px] text-muted">
        {r.services.total} servicios ({r.services.en_ejecucion} en ejecución, {r.services.automaticos} de inicio automático). Se listan los automáticos instalados fuera de la carpeta de Windows.
      </p>
      <table className="w-full text-sm">
        <tbody>
          {r.services.de_terceros_automaticos.map((s) => (
            <tr key={s.nombre} className="border-t border-line">
              <td className="py-2 pr-3">
                <div className="font-medium text-fg">{s.mostrado}</div>
                <div className="truncate font-mono text-[11px] text-faint">{s.ejecutable}</div>
              </td>
              <td className="py-2 pr-3 text-xs text-muted">{s.estado === 'running' ? 'En ejecución' : 'Detenido'}</td>
              <td className="py-2"><FirmaTag estado={s.firma?.estado ?? null} /><div className="text-[11px] text-faint">{s.firma?.firmante}</div></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function EventsTab({ r }: { r: AuditResult }) {
  return (
    <div>
      <p className="mb-3 text-[13px] text-muted">Errores y eventos críticos del registro «Sistema» en los últimos 7 días, agrupados. Muchos errores son habituales y no afectan el uso del equipo.</p>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-faint">
            <th className="pb-2 font-normal">Origen</th>
            <th className="pb-2 font-normal">ID</th>
            <th className="pb-2 font-normal">Nivel</th>
            <th className="pb-2 text-right font-normal">Veces</th>
            <th className="pb-2 text-right font-normal">Última</th>
          </tr>
        </thead>
        <tbody>
          {r.events.grupos.map((g) => (
            <tr key={`${g.proveedor}-${g.id}`} className="border-t border-line">
              <td className="py-2 text-fg">{g.proveedor}</td>
              <td className="py-2 tabular text-muted">{g.id}</td>
              <td className="py-2 text-muted">{g.nivel}</td>
              <td className="py-2 text-right tabular">{g.veces}</td>
              <td className="py-2 text-right text-xs text-faint">{new Date(g.ultima).toLocaleString('es-CO')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SourcesTab({ r }: { r: AuditResult }) {
  return (
    <div>
      <p className="mb-3 text-[13px] text-muted">Transparencia: estas son todas las fuentes consultadas. ScriptLens no instala servicios de vigilancia ni envía estos datos fuera del equipo.</p>
      <ul className="divide-y divide-line">
        {Object.entries(r.sources).map(([k, s]) => (
          <li key={k} className="flex items-start gap-3 py-2.5 text-sm">
            {s.ok ? <CheckCircle2 size={17} className="mt-0.5 text-ok" /> : <XCircle size={17} className="mt-0.5 text-warn" />}
            <div className="min-w-0 flex-1">
              <div className="text-fg">{s.etiqueta}</div>
              {s.error && <div className="text-xs text-warn">No disponible: {s.error.slice(0, 160)}</div>}
            </div>
            <span className="text-xs tabular text-faint">{s.ok ? `${s.registros} registro(s)` : ''}</span>
          </li>
        ))}
        <li className="py-2.5 text-sm text-muted">Cuentas locales: {r.users.total} ({r.users.habilitadas} habilitadas) · Sesiones: {r.users.sesiones} · Plan de energía: {r.power_plan ?? '—'}</li>
      </ul>
    </div>
  )
}
