import { ArrowDownRight, ArrowRight, ArrowUpRight, Camera, Info, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Confirm } from '../components/Confirm'
import { Term } from '../components/Term'
import { Card, Skeleton } from '../components/ui'
import { api, apiDelete, apiPost, type Comparison, type DiagnosticRow } from '../lib/api'
import { bytes, pct } from '../lib/format'

const when = (ts: number) => new Date(ts * 1000).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })

export function ComparePage() {
  const [list, setList] = useState<DiagnosticRow[] | null>(null)
  const [enabled, setEnabled] = useState(true)
  const [label, setLabel] = useState('')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const [a, setA] = useState<number | null>(null)
  const [b, setB] = useState<string>('actual')
  const [result, setResult] = useState<Comparison | null>(null)
  const [comparing, setComparing] = useState(false)
  const [toDelete, setToDelete] = useState<DiagnosticRow | null>(null)

  const refresh = useCallback(async () => {
    const r = await api<{ diagnostics: DiagnosticRow[]; history_enabled: boolean }>('/api/history/diagnostics')
    setList(r.diagnostics)
    setEnabled(r.history_enabled)
    return r.diagnostics
  }, [])

  useEffect(() => {
    refresh().then((d) => d.length && setA((x) => x ?? d[0].id)).catch((e) => setMsg(String(e.message ?? e)))
  }, [refresh])

  const save = async () => {
    setSaving(true)
    setMsg(null)
    try {
      const d = await apiPost<DiagnosticRow>('/api/history/diagnostics', { label })
      setLabel('')
      await refresh()
      setA(d.id)
      setMsg(`Diagnóstico «${d.label}» guardado con ${d.window_seconds} s de mediciones.`)
    } catch (e) {
      setMsg((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const compare = async () => {
    if (a == null) return
    setComparing(true)
    setMsg(null)
    try {
      setResult(await api<Comparison>('/api/history/compare', { a, b }))
    } catch (e) {
      setMsg((e as Error).message)
    } finally {
      setComparing(false)
    }
  }

  const remove = async () => {
    if (!toDelete) return
    await apiDelete(`/api/history/diagnostics/${toDelete.id}`)
    setToDelete(null)
    setResult(null)
    const d = await refresh()
    setA(d[0]?.id ?? null)
  }

  return (
    <div className="mx-auto flex max-w-[1200px] flex-col gap-5">
      <Card title="1 · Guardar un diagnóstico">
        <p className="mb-4 max-w-3xl text-sm leading-relaxed text-muted">
          Un diagnóstico guarda el promedio del último minuto: procesador, memoria, discos y los programas que más consumen. Guarde uno <strong className="text-fg">antes</strong> de un cambio
          (cerrar programas, reiniciar, instalar algo) y compárelo después.
        </p>
        <div className="flex flex-wrap gap-2">
          <input
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            maxLength={120}
            placeholder="Nombre (opcional), por ejemplo «Antes de reiniciar»"
            aria-label="Nombre del diagnóstico"
            className="min-w-[260px] flex-1 rounded-xl border border-line bg-surface-2 px-3 py-2 text-sm text-fg placeholder:text-faint"
          />
          <button onClick={save} disabled={saving || !enabled} className="flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-strong disabled:opacity-50">
            <Camera size={16} /> {saving ? 'Guardando…' : 'Guardar diagnóstico'}
          </button>
        </div>
        {!enabled && <p className="mt-3 text-sm text-warn">El historial está desactivado en Ajustes. Actívelo para guardar diagnósticos.</p>}
        {msg && <p className="mt-3 text-sm text-muted" role="status">{msg}</p>}
      </Card>

      <Card title="2 · Diagnósticos guardados">
        {!list ? (
          <Skeleton className="h-24 w-full" />
        ) : list.length === 0 ? (
          <p className="text-sm text-muted">Todavía no hay diagnósticos guardados.</p>
        ) : (
          <ul className="divide-y divide-line">
            {list.map((d) => (
              <li key={d.id} className="flex flex-wrap items-center gap-4 py-2.5 text-sm">
                <div className="min-w-0 flex-1">
                  <div className="truncate font-medium text-fg">{d.label}</div>
                  <div className="text-xs text-faint">{when(d.created_at)} · {d.window_seconds} s de mediciones</div>
                </div>
                <span className="tabular text-muted">CPU {pct(d.cpu_avg)}</span>
                <span className="tabular text-muted">RAM {pct(d.ram_avg)} ({bytes(d.ram_used)})</span>
                <span className="tabular text-faint">{d.process_count} procesos</span>
                <button onClick={() => setToDelete(d)} aria-label={`Eliminar ${d.label}`} className="grid h-8 w-8 place-items-center rounded-lg text-faint hover:bg-danger-soft hover:text-danger">
                  <Trash2 size={15} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {list && list.length > 0 && (
        <Card title="3 · Comparar">
          <div className="flex flex-wrap items-end gap-3">
            <Select label="Diagnóstico de referencia (antes)" value={a ?? ''} onChange={(v) => setA(Number(v))} options={list.map((d) => ({ value: String(d.id), label: `${d.label} — ${when(d.created_at)}` }))} />
            <ArrowRight size={18} className="mb-2.5 text-faint" />
            <Select
              label="Comparar con (después)"
              value={b}
              onChange={setB}
              options={[{ value: 'actual', label: 'El estado actual (medir ahora)' }, ...list.filter((d) => d.id !== a).map((d) => ({ value: String(d.id), label: `${d.label} — ${when(d.created_at)}` }))]}
            />
            <button onClick={compare} disabled={comparing || a == null} className="rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-strong disabled:opacity-50">
              {comparing ? 'Comparando…' : 'Comparar'}
            </button>
          </div>
        </Card>
      )}

      {result && <ComparisonView c={result} />}

      {toDelete && (
        <Confirm title="¿Eliminar este diagnóstico?" confirmLabel="Eliminar" danger onConfirm={remove} onCancel={() => setToDelete(null)}>
          <p>Se eliminará «{toDelete.label}» de este equipo. Esta acción no se puede deshacer.</p>
        </Confirm>
      )}
    </div>
  )
}

function Select({ label, value, onChange, options }: { label: string; value: string | number; onChange: (v: string) => void; options: { value: string; label: string }[] }) {
  return (
    <label className="flex min-w-[260px] flex-1 flex-col gap-1 text-xs text-faint">
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)} className="rounded-xl border border-line bg-surface-2 px-3 py-2 text-sm text-fg">
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  )
}

function Delta({ v, unit, invert = false, format }: { v: number | null; unit?: string; invert?: boolean; format?: (n: number) => string }) {
  if (v == null) return <span className="text-faint">—</span>
  const up = v > 0
  const bad = invert ? !up : up
  const tone = Math.abs(v) < 0.5 ? 'text-muted' : bad ? 'text-warn' : 'text-ok'
  const Icon = up ? ArrowUpRight : ArrowDownRight
  return (
    <span className={`inline-flex items-center gap-0.5 tabular ${tone}`}>
      {Math.abs(v) >= 0.5 && <Icon size={14} />}
      {up ? '+' : v < 0 ? '−' : ''}
      {format ? format(Math.abs(v)) : `${Math.abs(v).toFixed(1)}${unit ?? ''}`}
    </span>
  )
}

function ComparisonView({ c }: { c: Comparison }) {
  const m = c.metrics
  const procs = c.processes.filter((p) => Math.abs(p.memory_delta) >= 20 * 1024 ** 2 || Math.abs(p.cpu_delta) >= 1 || p.estado !== 'presente').slice(0, 25)
  const max = Math.max(1, ...procs.map((p) => Math.abs(p.memory_delta)))
  return (
    <>
      <Card title={`Resultado: ${c.a.label} → ${c.b.label}`}>
        <ul className="space-y-2">
          {c.summary.map((s, i) => (
            <li key={i} className={`text-[14.5px] leading-relaxed ${i === c.summary.length - 1 ? 'text-faint' : 'text-fg'}`}>
              {s}
            </li>
          ))}
        </ul>
        <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
          <MetricBox label={<Term id="cpu">CPU promedio</Term>} a={pct(m.cpu_avg.antes, 1)} b={pct(m.cpu_avg.despues, 1)} delta={<Delta v={m.cpu_avg.delta} unit=" pts" />} />
          <MetricBox label={<Term id="ram">RAM promedio</Term>} a={pct(m.ram_avg.antes, 1)} b={pct(m.ram_avg.despues, 1)} delta={<Delta v={m.ram_avg.delta} unit=" pts" />} />
          <MetricBox label="RAM en uso" a={bytes(m.ram_used.antes)} b={bytes(m.ram_used.despues)} delta={<Delta v={m.ram_used.delta} format={(n) => bytes(n)} />} />
          <MetricBox label="Procesos" a={String(m.process_count.antes ?? '—')} b={String(m.process_count.despues ?? '—')} delta={<Delta v={m.process_count.delta} format={(n) => n.toFixed(0)} />} />
        </div>
      </Card>
      <Card title="Diferencias por programa (memoria)">
        {procs.length === 0 ? (
          <p className="text-sm text-muted">No hay diferencias apreciables entre los programas comparados.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-faint">
                <th className="pb-2 font-normal">Programa</th>
                <th className="pb-2 text-right font-normal">Antes</th>
                <th className="pb-2 text-right font-normal">Después</th>
                <th className="w-[34%] pb-2 pl-4 font-normal">Cambio de memoria</th>
                <th className="pb-2 text-right font-normal">CPU</th>
              </tr>
            </thead>
            <tbody>
              {procs.map((p) => (
                <tr key={p.name} className="border-t border-line">
                  <td className="py-2">
                    <span className="font-medium text-fg">{p.name}</span>
                    {p.estado !== 'presente' && <span className="ml-2 rounded-md bg-surface-3 px-1.5 py-0.5 text-[10.5px] text-muted">{p.estado === 'nuevo' ? 'Nuevo' : 'Ya no está'}</span>}
                  </td>
                  <td className="py-2 text-right tabular text-muted">{bytes(p.memory_antes)}</td>
                  <td className="py-2 text-right tabular text-muted">{bytes(p.memory_despues)}</td>
                  <td className="py-2 pl-4">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-3">
                        <div className="h-full rounded-full" style={{ width: `${(Math.abs(p.memory_delta) / max) * 100}%`, background: p.memory_delta > 0 ? 'var(--warn)' : 'var(--ok)' }} />
                      </div>
                      <span className="w-24 text-right"><Delta v={p.memory_delta} format={(n) => bytes(n)} /></span>
                    </div>
                  </td>
                  <td className="py-2 text-right"><Delta v={p.cpu_delta} unit=" %" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="mt-4 rounded-xl bg-surface-2 p-3.5 text-xs leading-relaxed text-muted">
          <div className="mb-1 flex items-center gap-1.5 font-medium text-fg"><Info size={14} /> Limitaciones</div>
          <ul className="list-disc space-y-0.5 pl-5">
            {c.limitaciones.map((l) => <li key={l}>{l}</li>)}
          </ul>
        </div>
      </Card>
    </>
  )
}

function MetricBox({ label, a, b, delta }: { label: React.ReactNode; a: string; b: string; delta: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-surface-2 p-3.5">
      <div className="text-xs text-faint">{label}</div>
      <div className="mt-1 flex items-baseline gap-2 tabular">
        <span className="text-muted">{a}</span>
        <ArrowRight size={13} className="text-faint" />
        <span className="font-display text-lg font-semibold text-fg">{b}</span>
      </div>
      <div className="mt-0.5 text-sm">{delta}</div>
    </div>
  )
}
