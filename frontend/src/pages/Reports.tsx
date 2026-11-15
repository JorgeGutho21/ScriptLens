import { FileText, FolderOpen, Globe } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Card } from '../components/ui'
import { api, apiPost, type DiagnosticRow } from '../lib/api'
import { bytes } from '../lib/format'

interface Item {
  archivo: string
  bytes: number
  fecha: number
}

export function ReportsPage() {
  const [list, setList] = useState<{ carpeta: string; informes: Item[] } | null>(null)
  const [diags, setDiags] = useState<DiagnosticRow[]>([])
  const [security, setSecurity] = useState(true)
  const [compare, setCompare] = useState<string>('')
  const [busy, setBusy] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)

  const load = () => api<{ carpeta: string; informes: Item[] }>('/api/reports').then(setList)
  useEffect(() => {
    load()
    api<{ diagnostics: DiagnosticRow[] }>('/api/history/diagnostics').then((r) => setDiags(r.diagnostics))
  }, [])

  const generate = async (formato: 'pdf' | 'html') => {
    setBusy(formato)
    setMsg(null)
    try {
      const r = await apiPost<{ archivo: string; ruta: string; bytes: number }>('/api/reports', { formato, incluir_seguridad: security, comparar_con: compare ? Number(compare) : null })
      setMsg(`Informe creado: ${r.archivo} (${bytes(r.bytes)}).`)
      await load()
      await apiPost(`/api/reports/open/${encodeURIComponent(r.archivo)}`)
    } catch (e) {
      setMsg((e as Error).message)
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="mx-auto flex max-w-[1000px] flex-col gap-5">
      <Card title="Generar informe">
        <p className="mb-4 text-sm leading-relaxed text-muted">
          El informe reúne las mediciones del último minuto, los programas que más consumen, los hallazgos de seguridad, las recomendaciones, las acciones realizadas y las limitaciones del diagnóstico. Incluye la
          identidad de ScriptLens IA y una marca de agua discreta. Se guarda solo en este equipo.
        </p>
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm text-fg">
            <input type="checkbox" checked={security} onChange={(e) => setSecurity(e.target.checked)} className="accent-[var(--accent)]" /> Incluir auditoría de seguridad (tarda unos segundos)
          </label>
          <label className="flex flex-wrap items-center gap-2 text-sm text-fg">
            Comparar con un diagnóstico guardado:
            <select value={compare} onChange={(e) => setCompare(e.target.value)} className="rounded-lg border border-line bg-surface-2 px-2 py-1 text-sm">
              <option value="">No incluir comparación</option>
              {diags.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.label} — {new Date(d.created_at * 1000).toLocaleString('es-CO')}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          <button onClick={() => generate('pdf')} disabled={!!busy} className="flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-strong disabled:opacity-60">
            <FileText size={16} /> {busy === 'pdf' ? 'Generando…' : 'Crear PDF'}
          </button>
          <button onClick={() => generate('html')} disabled={!!busy} className="flex items-center gap-2 rounded-xl border border-line px-4 py-2 text-sm hover:bg-surface-2 disabled:opacity-60">
            <Globe size={16} /> {busy === 'html' ? 'Generando…' : 'Crear HTML'}
          </button>
        </div>
        {msg && <p className="mt-3 text-sm text-muted" role="status">{msg}</p>}
      </Card>

      <Card title="Informes guardados" action={<button onClick={() => apiPost('/api/reports/open-folder')} className="flex items-center gap-1.5 text-xs text-accent hover:underline"><FolderOpen size={14} /> Abrir carpeta</button>}>
        {list && <p className="mb-3 break-all font-mono text-[11px] text-faint">{list.carpeta}</p>}
        {!list || list.informes.length === 0 ? (
          <p className="text-sm text-muted">Todavía no hay informes.</p>
        ) : (
          <ul className="divide-y divide-line">
            {list.informes.map((i) => (
              <li key={i.archivo} className="flex items-center gap-3 py-2 text-sm">
                <FileText size={15} className="text-faint" />
                <span className="min-w-0 flex-1 truncate text-fg">{i.archivo}</span>
                <span className="text-xs tabular text-faint">{new Date(i.fecha * 1000).toLocaleString('es-CO')} · {bytes(i.bytes)}</span>
                <button onClick={() => apiPost(`/api/reports/open/${encodeURIComponent(i.archivo)}`)} className="rounded-lg border border-line px-2.5 py-1 text-xs text-muted hover:text-fg">
                  Abrir
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
