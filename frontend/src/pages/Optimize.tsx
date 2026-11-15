import { ClipboardList, Lightbulb, PackageX, Search, Settings2, Trash2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Card, Skeleton } from '../components/ui'
import { api, type ProcessListRow } from '../lib/api'
import { bytes, pct } from '../lib/format'
import { useMetrics } from '../lib/metrics'
import { useSupervised } from '../lib/supervised'
import { usePolling } from '../lib/usePolling'

interface TempCat {
  id: string
  nombre: string
  ubicacion: string
  archivos?: number
  bytes: number | null
  limpiable: boolean
  nota: string
  muestra?: string[]
}

interface Program {
  id: string
  nombre: string
  editor: string | null
  version: string | null
  tamano_kb: number | null
  instalado: string | null
  ambito: string
  desinstalable: boolean
}

interface ActionRow {
  id: number
  created_at: number
  action: string
  target: string
  result: string
  detail: string
  before: { cpu_10s?: number; ram_percent?: number; ram_used?: number } | null
  after: { cpu_10s?: number; ram_percent?: number; ram_used?: number; eliminados?: number } | null
}

const ACCION_ES: Record<string, string> = {
  cerrar: 'Solicitar cierre',
  finalizar: 'Finalizar proceso',
  inicio_activar: 'Activar inicio automático',
  inicio_desactivar: 'Desactivar inicio automático',
  limpiar_temporales: 'Limpiar temporales',
  desinstalar: 'Abrir desinstalador',
}

export function OptimizePage({ goProcesses }: { goProcesses: () => void }) {
  const { summary } = useMetrics()
  const procs = usePolling(() => api<{ processes: ProcessListRow[] }>('/api/processes'), 6000)
  const [log, setLog] = useState<ActionRow[]>([])
  const refreshLog = () => api<{ actions: ActionRow[] }>('/api/actions/log', { limit: 30 }).then((r) => setLog(r.actions))
  useEffect(() => {
    refreshLog()
  }, [])

  const suggestions = useMemo(() => {
    // Nunca se sugieren componentes de Windows ni la propia ScriptLens.
    const excluded = new Set(['explorer.exe', 'scriptlens.exe', 'scriptlens-backend.exe', 'msedgewebview2.exe', 'dwm.exe', 'sihost.exe', 'ctfmon.exe'])
    const apps = (procs.data?.processes ?? []).filter((p) => (p.category === 'aplicacion' || p.category === 'segundo_plano') && !excluded.has(p.name.toLowerCase()))
    const byName = new Map<string, { name: string; mem: number; cpu: number; count: number; open: boolean }>()
    for (const p of apps) {
      const g = byName.get(p.name) ?? { name: p.name, mem: 0, cpu: 0, count: 0, open: false }
      g.mem += p.memory_rss ?? 0
      g.cpu += p.cpu_avg_60s ?? 0
      g.count += 1
      g.open ||= p.category === 'aplicacion'
      byName.set(p.name, g)
    }
    return [...byName.values()].filter((g) => g.open && (g.mem > 400 * 1024 ** 2 || g.cpu > 10)).sort((a, b) => b.mem - a.mem).slice(0, 6)
  }, [procs.data])

  const ram = summary?.averages.ram_1m
  const cpu = summary?.averages.cpu_1m

  return (
    <div className="mx-auto flex max-w-[1200px] flex-col gap-5">
      <Card title={<span className="flex items-center gap-2"><Lightbulb size={14} /> Recomendaciones basadas en las mediciones</span>}>
        <p className="mb-3 text-sm text-muted">
          Ahora: procesador {pct(cpu)} y memoria {pct(ram)} en promedio durante el último minuto.{' '}
          {ram != null && ram < 75 && cpu != null && cpu < 60 ? 'El equipo tiene margen; no es necesario cerrar programas.' : 'Cerrar programas que no use puede liberar recursos.'}
        </p>
        {!procs.data ? (
          <Skeleton className="h-24 w-full" />
        ) : suggestions.length === 0 ? (
          <p className="text-sm text-muted">Ninguna aplicación abierta consume una cantidad destacable de recursos.</p>
        ) : (
          <ul className="divide-y divide-line">
            {suggestions.map((s) => (
              <li key={s.name} className="flex flex-wrap items-center gap-3 py-2.5 text-sm">
                <span className="font-medium text-fg">{s.name}</span>
                <span className="text-xs text-faint">{s.count} proceso{s.count > 1 ? 's' : ''}</span>
                <span className="ml-auto tabular text-muted">{bytes(s.mem)} · CPU 1 min {pct(s.cpu, 1)}</span>
              </li>
            ))}
          </ul>
        )}
        <button onClick={goProcesses} className="mt-3 text-sm text-accent hover:underline">
          Ir a Procesos para solicitar el cierre de una aplicación →
        </button>
        <p className="mt-2 text-xs text-faint">ScriptLens no promete porcentajes de mejora: tras una acción, el registro inferior muestra la memoria y la CPU medidas antes y después.</p>
      </Card>

      <TempCard onDone={refreshLog} />
      <ProgramsCard onDone={refreshLog} />

      <Card title={<span className="flex items-center gap-2"><ClipboardList size={14} /> Registro de acciones</span>}>
        {log.length === 0 ? (
          <p className="text-sm text-muted">Todavía no se ha realizado ninguna acción.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-faint">
                <th className="pb-2 font-normal">Fecha</th>
                <th className="pb-2 font-normal">Acción</th>
                <th className="pb-2 font-normal">Objetivo</th>
                <th className="pb-2 font-normal">Resultado</th>
                <th className="pb-2 text-right font-normal">RAM antes → después</th>
              </tr>
            </thead>
            <tbody>
              {log.map((a) => (
                <tr key={a.id} className="border-t border-line align-top">
                  <td className="py-2 pr-3 text-xs text-faint">{new Date(a.created_at * 1000).toLocaleString('es-CO')}</td>
                  <td className="py-2 pr-3 text-fg">{ACCION_ES[a.action] ?? a.action}</td>
                  <td className="max-w-[260px] truncate py-2 pr-3 text-muted" title={a.target}>{a.target}</td>
                  <td className="py-2 pr-3">
                    <div className="text-fg">{a.result}</div>
                    <div className="text-xs text-faint">{a.detail}</div>
                  </td>
                  <td className="py-2 text-right tabular text-muted">
                    {a.before?.ram_used == null
                      ? '—' // acción sin medición (p. ej., un informe)
                      : `${bytes(a.before.ram_used)} → ${a.after?.ram_used != null ? bytes(a.after.ram_used) : Date.now() / 1000 - a.created_at < 60 ? 'midiendo…' : 'sin medición'}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}

function TempCard({ onDone }: { onDone: () => void }) {
  const [cats, setCats] = useState<TempCat[] | null>(null)
  const load = () => api<{ categorias: TempCat[] }>('/api/actions/temp/preview').then((r) => setCats(r.categorias))
  const { request, dialog, banner } = useSupervised(() => {
    load()
    onDone()
  })
  return (
    <Card title={<span className="flex items-center gap-2"><Trash2 size={14} /> Archivos temporales (vista previa)</span>}>
      {!cats ? (
        <button onClick={load} className="rounded-xl border border-line px-4 py-2 text-sm hover:bg-surface-2">Calcular espacio</button>
      ) : (
        <div className="space-y-3">
          {cats.map((c) => (
            <div key={c.id} className="rounded-xl border border-line bg-surface-2 p-3.5">
              <div className="flex flex-wrap items-center gap-3">
                <span className="font-medium text-fg">{c.nombre}</span>
                <span className="tabular text-sm text-muted">{c.bytes != null ? bytes(c.bytes) : 'No accesible'}{c.archivos != null ? ` · ${c.archivos} archivos` : ''}</span>
                {c.limpiable && (
                  <button
                    disabled={!c.archivos}
                    onClick={() => request('/api/actions/temp/prepare', {}, '¿Eliminar archivos temporales antiguos?', 'Eliminar', true)}
                    className="ml-auto rounded-xl bg-accent px-3.5 py-1.5 text-sm font-medium text-white hover:bg-accent-strong disabled:opacity-50"
                  >
                    Limpiar…
                  </button>
                )}
              </div>
              <div className="mt-1 break-all font-mono text-[11px] text-faint">{c.ubicacion}</div>
              <p className="mt-1 text-xs text-muted">{c.nota}</p>
              {c.muestra && c.muestra.length > 0 && <p className="mt-1 truncate text-[11px] text-faint">Ejemplos: {c.muestra.join(', ')}</p>}
            </div>
          ))}
          {banner}
        </div>
      )}
      {dialog}
    </Card>
  )
}

function ProgramsCard({ onDone }: { onDone: () => void }) {
  const [list, setList] = useState<Program[] | null>(null)
  const [q, setQ] = useState('')
  const { request, dialog, banner } = useSupervised(onDone)
  const shown = (list ?? []).filter((p) => !q || p.nombre.toLowerCase().includes(q.toLowerCase()) || (p.editor ?? '').toLowerCase().includes(q.toLowerCase()))
  return (
    <Card title={<span className="flex items-center gap-2"><PackageX size={14} /> Programas instalados</span>}>
      {!list ? (
        <button onClick={() => api<{ programas: Program[] }>('/api/actions/programs').then((r) => setList(r.programas))} className="rounded-xl border border-line px-4 py-2 text-sm hover:bg-surface-2">
          Mostrar programas instalados
        </button>
      ) : (
        <>
          <div className="mb-3 flex flex-wrap items-center gap-3">
            <label className="relative min-w-[240px] flex-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar programa o editor" aria-label="Buscar programa" className="w-full rounded-xl border border-line bg-surface-2 py-2 pl-9 pr-3 text-sm" />
            </label>
            <span className="text-xs text-faint">{list.length} programas · también puede usar Configuración → Aplicaciones</span>
          </div>
          {banner}
          <div className="max-h-[420px] overflow-auto">
            <table className="w-full text-sm">
              <tbody>
                {shown.map((p) => (
                  <tr key={p.id} className="border-t border-line">
                    <td className="py-2 pr-3">
                      <div className="font-medium text-fg">{p.nombre}</div>
                      <div className="text-xs text-faint">{p.editor ?? 'Editor no indicado'}{p.version ? ` · ${p.version}` : ''}</div>
                    </td>
                    <td className="py-2 pr-3 text-right tabular text-xs text-muted">{p.tamano_kb ? bytes(p.tamano_kb * 1024) : ''}</td>
                    <td className="py-2 text-right">
                      {p.desinstalable && (
                        <button
                          onClick={() => request('/api/actions/programs/prepare', { id: p.id }, `¿Abrir el desinstalador de ${p.nombre}?`, 'Abrir desinstalador')}
                          className="flex items-center gap-1 rounded-lg border border-line px-2.5 py-1 text-xs text-muted hover:text-fg"
                        >
                          <Settings2 size={13} /> Desinstalar…
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {dialog}
    </Card>
  )
}
