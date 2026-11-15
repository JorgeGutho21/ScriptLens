import { ChevronDown, ChevronRight, FolderTree, List, Search, X } from 'lucide-react'
import { useMemo, useState, type ReactNode } from 'react'
import { EstadoPill, FirmaTag, TipoTag } from '../components/Badges'
import { Term } from '../components/Term'
import { Card, Skeleton } from '../components/ui'
import { api, type Categoria, type ProcessDetail, type ProcessListRow } from '../lib/api'
import { bytes, pct } from '../lib/format'
import { usePrefs } from '../lib/prefs'
import { usePolling } from '../lib/usePolling'
import { ProcessActions } from './ProcessActions'

type SortKey = 'name' | 'cpu' | 'memory' | 'pid'
type Filter = 'todos' | Categoria | 'elevado' | 'revisar'

const FILTERS: { id: Filter; label: string }[] = [
  { id: 'todos', label: 'Todos' },
  { id: 'aplicacion', label: 'Aplicaciones abiertas' },
  { id: 'segundo_plano', label: 'En segundo plano' },
  { id: 'servicio', label: 'Servicios' },
  { id: 'sistema', label: 'Windows' },
  { id: 'elevado', label: 'Consumo elevado' },
  { id: 'revisar', label: 'Requieren revisión' },
]

const REVISAR = new Set(['requiere_revision', 'actividad_sospechosa', 'amenaza_detectada'])

export function ProcessesPage() {
  const { prefs } = usePrefs()
  const advanced = prefs.mode === 'avanzado'
  const { data, error } = usePolling(() => api<{ processes: ProcessListRow[]; measured_at: number }>('/api/processes'), 3000)
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<Filter>('todos')
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({ key: 'memory', dir: -1 })
  const [view, setView] = useState<'tabla' | 'arbol'>('tabla')
  const [selected, setSelected] = useState<{ pid: number; create_time: number | null } | null>(null)

  const rows = useMemo(() => {
    let r = (data?.processes ?? []).filter((p) => p.pid !== 0)
    const q = query.trim().toLowerCase()
    if (q) r = r.filter((p) => p.name.toLowerCase().includes(q) || String(p.pid) === q || (p.publisher ?? '').toLowerCase().includes(q) || (p.description ?? '').toLowerCase().includes(q))
    if (filter === 'elevado') r = r.filter((p) => p.estado === 'consumo_elevado' || (p.cpu_avg_60s ?? 0) >= 10)
    else if (filter === 'revisar') r = r.filter((p) => REVISAR.has(p.estado))
    else if (filter !== 'todos') r = r.filter((p) => p.category === filter)
    const val = (p: ProcessListRow) => (sort.key === 'name' ? p.name.toLowerCase() : sort.key === 'cpu' ? (p.cpu_percent ?? -1) : sort.key === 'pid' ? p.pid : (p.memory_rss ?? -1))
    return [...r].sort((a, b) => (val(a) > val(b) ? 1 : val(a) < val(b) ? -1 : 0) * sort.dir)
  }, [data, query, filter, sort])

  const counts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const p of data?.processes ?? []) {
      c[p.category] = (c[p.category] ?? 0) + 1
      if (REVISAR.has(p.estado)) c.revisar = (c.revisar ?? 0) + 1
    }
    return c
  }, [data])

  const toggleSort = (key: SortKey) => setSort((s) => (s.key === key ? { key, dir: (s.dir * -1) as 1 | -1 } : { key, dir: key === 'name' ? 1 : -1 }))

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <CountCard label="Aplicaciones abiertas" value={counts.aplicacion} hint="Programas con ventana" />
        <CountCard label="En segundo plano" value={counts.segundo_plano} hint="Sin ventana, en su sesión" />
        <CountCard label="Servicios de Windows" value={counts.servicio} hint="Inician con el sistema" />
        <CountCard label="Requieren revisión" value={counts.revisar ?? 0} hint="Según la evidencia disponible" tone={(counts.revisar ?? 0) > 0 ? 'warn' : undefined} />
      </div>

      <Card className="!p-0">
        <div className="flex flex-wrap items-center gap-3 border-b border-line p-4">
          <label className="relative min-w-[220px] flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar por nombre, PID, editor o descripción"
              aria-label="Buscar procesos"
              className="w-full rounded-xl border border-line bg-surface-2 py-2 pl-9 pr-3 text-sm text-fg placeholder:text-faint"
            />
          </label>
          <div role="radiogroup" aria-label="Vista" className="flex rounded-xl border border-line bg-surface-2 p-0.5">
            <ViewBtn active={view === 'tabla'} onClick={() => setView('tabla')} icon={<List size={15} />} label="Tabla" />
            <ViewBtn active={view === 'arbol'} onClick={() => setView('arbol')} icon={<FolderTree size={15} />} label="Árbol" />
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5 border-b border-line px-4 py-3" role="radiogroup" aria-label="Filtro">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              role="radio"
              aria-checked={filter === f.id}
              onClick={() => setFilter(f.id)}
              className={`rounded-full px-3 py-1 text-xs transition-colors ${filter === f.id ? 'bg-accent text-white' : 'bg-surface-2 text-muted hover:text-fg'}`}
            >
              {f.label}
            </button>
          ))}
          <span className="ml-auto self-center text-xs text-faint tabular">{rows.length} procesos</span>
        </div>

        {!data ? (
          <div className="p-4">{error ? <p className="text-sm text-danger">{error}</p> : <Skeleton className="h-96 w-full" />}</div>
        ) : view === 'tabla' ? (
          <ProcessTable rows={rows} sort={sort} onSort={toggleSort} advanced={advanced} onSelect={setSelected} selectedPid={selected?.pid} />
        ) : (
          <ProcessTree all={data.processes} visible={rows} onSelect={setSelected} />
        )}
      </Card>

      {selected && <ProcessDrawer target={selected} onClose={() => setSelected(null)} advanced={advanced} />}
    </div>
  )
}

function CountCard({ label, value, hint, tone }: { label: string; value?: number; hint: string; tone?: 'warn' }) {
  return (
    <div className="card animate-rise p-4">
      <div className="text-[12.5px] text-muted">{label}</div>
      <div className={`tabular font-display text-2xl font-semibold ${tone === 'warn' ? 'text-warn' : 'text-fg'}`}>{value ?? '—'}</div>
      <div className="text-xs text-faint">{hint}</div>
    </div>
  )
}

function ViewBtn({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: ReactNode; label: string }) {
  return (
    <button role="radio" aria-checked={active} onClick={onClick} className={`flex items-center gap-1.5 rounded-[10px] px-3 py-1.5 text-xs ${active ? 'bg-accent text-white' : 'text-muted hover:text-fg'}`}>
      {icon}
      {label}
    </button>
  )
}

function Th({ children, k, sort, onSort, className = '' }: { children: ReactNode; k?: SortKey; sort?: { key: SortKey; dir: number }; onSort?: (k: SortKey) => void; className?: string }) {
  const active = k && sort?.key === k
  return (
    <th scope="col" className={`sticky top-0 z-10 bg-surface px-3 py-2.5 text-left text-[11.5px] font-medium uppercase tracking-wide text-faint ${className}`} aria-sort={active ? (sort!.dir === 1 ? 'ascending' : 'descending') : undefined}>
      {k ? (
        <button onClick={() => onSort?.(k)} className={`inline-flex items-center gap-1 uppercase tracking-wide hover:text-fg ${active ? 'text-fg' : ''}`}>
          {children}
          {active && (sort!.dir === 1 ? '↑' : '↓')}
        </button>
      ) : (
        children
      )}
    </th>
  )
}

function ProcessTable({
  rows,
  sort,
  onSort,
  advanced,
  onSelect,
  selectedPid,
}: {
  rows: ProcessListRow[]
  sort: { key: SortKey; dir: number }
  onSort: (k: SortKey) => void
  advanced: boolean
  onSelect: (s: { pid: number; create_time: number | null }) => void
  selectedPid?: number
}) {
  return (
    <div className="max-h-[calc(100vh-330px)] overflow-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line">
            <Th k="name" sort={sort} onSort={onSort}>Nombre</Th>
            {advanced && <Th k="pid" sort={sort} onSort={onSort} className="hidden xl:table-cell">PID</Th>}
            <Th>Tipo</Th>
            <Th k="cpu" sort={sort} onSort={onSort} className="text-right"><Term id="cpu">CPU</Term></Th>
            <Th k="memory" sort={sort} onSort={onSort} className="text-right"><Term id="ram">RAM</Term></Th>
            <Th className="hidden xl:table-cell">Editor</Th>
            {advanced && <Th>Firma</Th>}
            <Th>Estado</Th>
          </tr>
        </thead>
        <tbody>
          {rows.map((p) => (
            <tr
              key={`${p.pid}-${p.create_time}`}
              onClick={() => onSelect({ pid: p.pid, create_time: p.create_time })}
              onKeyDown={(e) => e.key === 'Enter' && onSelect({ pid: p.pid, create_time: p.create_time })}
              tabIndex={0}
              className={`cursor-pointer border-b border-line/60 transition-colors hover:bg-surface-2 focus-visible:bg-surface-2 ${selectedPid === p.pid ? 'bg-accent-soft' : ''}`}
            >
              <td className="max-w-[260px] px-3 py-2">
                <div className="truncate font-medium text-fg">{p.name}</div>
                {p.description && p.description.toLowerCase() !== p.name.toLowerCase() && <div className="truncate text-xs text-faint">{p.description}</div>}
              </td>
              {advanced && <td className="hidden px-3 py-2 tabular text-muted xl:table-cell">{p.pid}</td>}
              <td className="min-w-[110px] max-w-[170px] px-3 py-2 text-xs leading-snug text-muted">{p.category_label}</td>
              <td className="whitespace-nowrap px-3 py-2 text-right tabular">{pct(p.cpu_percent, 1)}</td>
              <td className="whitespace-nowrap px-3 py-2 text-right tabular">{bytes(p.memory_rss)}</td>
              <td className="hidden max-w-[200px] truncate px-3 py-2 text-xs text-muted xl:table-cell">{p.publisher ?? '—'}</td>
              {advanced && (
                <td className="px-3 py-2">
                  <FirmaTag estado={p.signature} />
                </td>
              )}
              <td className="px-3 py-2">
                <EstadoPill estado={p.estado} compact={p.estado === 'normal'} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && <p className="p-6 text-center text-sm text-muted">Ningún proceso coincide con la búsqueda.</p>}
    </div>
  )
}

interface Node {
  p: ProcessListRow
  children: Node[]
}

function buildTree(all: ProcessListRow[]): Node[] {
  const byPid = new Map(all.map((p) => [p.pid, p]))
  const nodes = new Map<number, Node>(all.map((p) => [p.pid, { p, children: [] }]))
  const roots: Node[] = []
  for (const p of all) {
    if (p.pid === 0) continue
    const parent = p.ppid != null ? byPid.get(p.ppid) : undefined
    // Un padre solo es válido si existía antes que el hijo (Windows reutiliza los PID).
    const valid = parent && parent.pid !== p.pid && parent.pid !== 0 && (!parent.create_time || !p.create_time || parent.create_time <= p.create_time)
    if (valid) nodes.get(parent.pid)!.children.push(nodes.get(p.pid)!)
    else roots.push(nodes.get(p.pid)!)
  }
  const sortRec = (list: Node[]) => {
    list.sort((a, b) => (b.p.memory_rss ?? 0) - (a.p.memory_rss ?? 0))
    list.forEach((n) => sortRec(n.children))
  }
  sortRec(roots)
  return roots
}

function ProcessTree({ all, visible, onSelect }: { all: ProcessListRow[]; visible: ProcessListRow[]; onSelect: (s: { pid: number; create_time: number | null }) => void }) {
  const tree = useMemo(() => buildTree(all), [all])
  const show = useMemo(() => new Set(visible.map((p) => p.pid)), [visible])
  const [collapsed, setCollapsed] = useState<Set<number>>(new Set())

  const hasVisible = (n: Node): boolean => show.has(n.p.pid) || n.children.some(hasVisible)
  const render = (n: Node, depth: number): ReactNode => {
    if (!hasVisible(n)) return null
    const open = !collapsed.has(n.p.pid)
    return (
      <div key={`${n.p.pid}-${n.p.create_time}`}>
        <div className={`flex items-center gap-2 border-b border-line/50 py-1.5 pr-3 text-sm hover:bg-surface-2 ${show.has(n.p.pid) ? '' : 'opacity-50'}`} style={{ paddingLeft: 12 + depth * 18 }}>
          {n.children.length > 0 ? (
            <button
              aria-label={open ? `Contraer ${n.p.name}` : `Expandir ${n.p.name}`}
              aria-expanded={open}
              onClick={() => setCollapsed((s) => { const c = new Set(s); if (open) c.add(n.p.pid); else c.delete(n.p.pid); return c })}
              className="text-faint hover:text-fg"
            >
              {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
            </button>
          ) : (
            <span className="w-[15px]" />
          )}
          <button onClick={() => onSelect({ pid: n.p.pid, create_time: n.p.create_time })} className="min-w-0 flex-1 truncate text-left font-medium text-fg hover:text-accent">
            {n.p.name}
            <span className="ml-2 text-xs font-normal text-faint tabular">PID {n.p.pid}{n.children.length > 0 ? ` · ${n.children.length} hijo${n.children.length > 1 ? 's' : ''}` : ''}</span>
          </button>
          <span className="w-16 text-right text-xs tabular text-muted">{pct(n.p.cpu_percent, 1)}</span>
          <span className="w-20 text-right text-xs tabular text-muted">{bytes(n.p.memory_rss)}</span>
          <span className="w-8"><EstadoPill estado={n.p.estado} compact /></span>
        </div>
        {open && n.children.map((c) => render(c, depth + 1))}
      </div>
    )
  }
  return <div className="max-h-[calc(100vh-330px)] overflow-auto">{tree.map((n) => render(n, 0))}</div>
}

function ProcessDrawer({ target, onClose, advanced }: { target: { pid: number; create_time: number | null }; onClose: () => void; advanced: boolean }) {
  const { data, error } = usePolling(
    () => api<ProcessDetail>(`/api/processes/${target.pid}`, target.create_time != null ? { create_time: target.create_time } : undefined),
    5000,
    [target.pid, target.create_time],
  )
  const d = data
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/30 backdrop-blur-[2px]" onClick={onClose}>
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={`Detalle del proceso ${d?.name ?? target.pid}`}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.key === 'Escape' && onClose()}
        className="animate-rise flex h-full w-full max-w-[560px] flex-col border-l border-line bg-surface shadow-2xl"
      >
        <header className="flex items-start gap-3 border-b border-line p-5">
          <div className="min-w-0 flex-1">
            <h2 className="truncate font-display text-xl font-semibold">{d?.name ?? `PID ${target.pid}`}</h2>
            {d && (
              <div className="mt-1.5 flex flex-wrap items-center gap-2">
                <EstadoPill estado={d.estado} />
                <span className="text-xs text-muted">{d.category_label}</span>
                <span className="text-xs text-faint tabular">PID {d.pid}</span>
              </div>
            )}
          </div>
          <button autoFocus onClick={onClose} aria-label="Cerrar detalle" className="grid h-9 w-9 place-items-center rounded-xl border border-line text-muted hover:text-fg">
            <X size={17} />
          </button>
        </header>
        <div className="flex-1 space-y-5 overflow-y-auto p-5">
          {error && !d && <p className="rounded-xl bg-surface-2 p-4 text-sm text-muted">{error.includes('404') ? 'Este proceso ya terminó.' : error}</p>}
          {!d && !error && <Skeleton className="h-64 w-full" />}
          {d && (
            <>
              <ProcessActions detail={d} onDone={onClose} />

              {d.signals.filter((s) => s.estado !== 'normal').length > 0 && (
                <section>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-faint">Señales observadas</h3>
                  <ul className="space-y-2">
                    {d.signals.map((s) => (
                      <li key={s.code} className="rounded-xl border border-line bg-surface-2 p-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <EstadoPill estado={s.estado} />
                          <TipoTag tipo={s.tipo} />
                        </div>
                        <div className="mt-1.5 text-sm font-medium text-fg">{s.titulo}</div>
                        <div className="mt-0.5 break-all text-xs text-muted">{s.evidencia}</div>
                        <div className="mt-1 text-[11px] text-faint">Fuente: {s.fuente}</div>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              <section>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-faint">Preguntas frecuentes</h3>
                <div className="divide-y divide-line rounded-xl border border-line">
                  {d.explicacion.map((q) => (
                    <details key={q.pregunta} className="group p-3.5" open={q.pregunta.startsWith('¿Qué hace')}>
                      <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-medium text-fg">
                        <ChevronRight size={15} className="text-faint transition-transform group-open:rotate-90" />
                        {q.pregunta}
                        <span className="ml-auto"><TipoTag tipo={q.tipo} /></span>
                      </summary>
                      <p className="mt-2 pl-6 text-[13.5px] leading-relaxed text-muted">{q.respuesta}</p>
                    </details>
                  ))}
                </div>
              </section>

              <section>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-faint">Datos medidos</h3>
                <dl className="grid grid-cols-[auto_1fr] gap-x-5 gap-y-2 text-sm">
                  <Dt>CPU ahora</Dt>
                  <Dd>{pct(d.cpu_percent, 1)}</Dd>
                  <Dt>CPU promedio 1 min</Dt>
                  <Dd>{d.stats?.cpu_avg != null ? `${pct(d.stats.cpu_avg, 1)} (máx. ${pct(d.stats.cpu_max, 1)})` : '—'}</Dd>
                  <Dt>Memoria (working set)</Dt>
                  <Dd>{bytes(d.memory_rss)}</Dd>
                  {advanced && (
                    <>
                      <Dt>Memoria privada</Dt>
                      <Dd>{bytes(d.private_bytes)}</Dd>
                      <Dt>Hilos · identificadores</Dt>
                      <Dd>{d.threads ?? '—'} · {d.handles ?? '—'}</Dd>
                    </>
                  )}
                  <Dt>Iniciado</Dt>
                  <Dd>{d.create_time ? new Date(d.create_time * 1000).toLocaleString('es-CO') : '—'}</Dd>
                  <Dt>Usuario</Dt>
                  <Dd>{d.user ?? 'No disponible sin permisos de administrador'}</Dd>
                  <Dt>Ubicación</Dt>
                  <Dd className="break-all font-mono text-xs">{d.path ?? 'No disponible'}</Dd>
                  <Dt>Firma digital</Dt>
                  <Dd>{d.signature ? <><FirmaTag estado={d.signature.estado} />{d.signature.firmante && <span className="ml-2 text-xs text-muted">{d.signature.firmante}</span>}</> : '—'}</Dd>
                  <Dt>Editor</Dt>
                  <Dd>{d.signature?.editor ?? '—'}</Dd>
                  {d.signature?.version && advanced && (
                    <>
                      <Dt>Versión</Dt>
                      <Dd>{d.signature.version}</Dd>
                    </>
                  )}
                  <Dt>Proceso padre</Dt>
                  <Dd>{d.parent ? `${d.parent.name} (PID ${d.parent.pid})` : 'Sin padre activo'}</Dd>
                  <Dt>Procesos hijos</Dt>
                  <Dd>{d.children.length ? d.children.map((c) => `${c.name} (${c.pid})`).join(', ') : 'Ninguno'}</Dd>
                  <Dt>Conexiones de red</Dt>
                  <Dd>{d.connections ? `${d.connections.total} (${d.connections.establecidas} establecidas${d.connections.escuchando.length ? `, escucha en ${d.connections.escuchando.join(', ')}` : ''})` : 'No accesible'}</Dd>
                  {advanced && d.connections && d.connections.remotas.length > 0 && (
                    <>
                      <Dt>Destinos remotos</Dt>
                      <Dd className="font-mono text-xs">{d.connections.remotas.join(' · ')}</Dd>
                    </>
                  )}
                  {advanced && d.cmdline && (
                    <>
                      <Dt>Línea de comandos</Dt>
                      <Dd className="break-all font-mono text-xs">{d.cmdline}</Dd>
                    </>
                  )}
                </dl>
                <p className="mt-3 text-[11px] text-faint">Medido: {new Date(d.measured_at * 1000).toLocaleTimeString('es-CO')}. Los datos de ubicación, firma y consumo son comprobados; las explicaciones marcadas como «Estimado» son conclusiones de ScriptLens.</p>
              </section>
            </>
          )}
        </div>
      </aside>
    </div>
  )
}

const Dt = ({ children }: { children: ReactNode }) => <dt className="text-faint">{children}</dt>
const Dd = ({ children, className = '' }: { children: ReactNode; className?: string }) => <dd className={`min-w-0 text-fg ${className}`}>{children}</dd>
