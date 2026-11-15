import { Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Confirm } from '../components/Confirm'
import { Card } from '../components/ui'
import { api, apiDelete, apiPost } from '../lib/api'

type Settings = { history_enabled: boolean; conversations_enabled: boolean }
type What = 'diagnostics' | 'conversations' | 'actions'

const LABELS: Record<What, string> = {
  diagnostics: 'todos los diagnósticos guardados',
  conversations: 'todas las conversaciones con el asistente',
  actions: 'el registro de acciones realizadas',
}

/** Controles de privacidad: qué se guarda en este equipo y cómo borrarlo. */
export function PrivacyCard({ Row, Toggle }: { Row: React.FC<{ label: string; hint?: string; children: React.ReactNode }>; Toggle: React.FC<{ checked: boolean; onChange: (v: boolean) => void; label: string }> }) {
  const [s, setS] = useState<Settings | null>(null)
  const [pending, setPending] = useState<What | null>(null)
  const [msg, setMsg] = useState<string | null>(null)

  const [info, setInfo] = useState<{ carpeta_datos: string; carpeta_informes: string } | null>(null)
  useEffect(() => {
    api<Settings>('/api/settings').then(setS).catch(() => setS(null))
    api<{ carpeta_datos: string; carpeta_informes: string }>('/api/privacy/info').then(setInfo).catch(() => setInfo(null))
  }, [])

  const set = async (key: keyof Settings, value: boolean) => setS(await apiPost<Settings>('/api/settings', { key, value }))
  const clear = async () => {
    if (!pending) return
    const r = await apiDelete<{ deleted: number }>(`/api/privacy/${pending}`)
    setMsg(`Se eliminaron ${r.deleted} elementos (${LABELS[pending]}).`)
    setPending(null)
  }

  return (
    <Card title="Privacidad y datos guardados">
      <p className="mb-4 text-[13px] leading-relaxed text-muted">
        ScriptLens guarda la información únicamente en este equipo. Nada se envía a Internet. Las mediciones en tiempo real solo se conservan en memoria durante 10 minutos.
      </p>
      {info && (
        <dl className="mb-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-xs">
          <dt className="text-faint">Datos e historial</dt>
          <dd className="break-all font-mono text-muted">{info.carpeta_datos}</dd>
          <dt className="text-faint">Informes</dt>
          <dd className="break-all font-mono text-muted">{info.carpeta_informes}</dd>
        </dl>
      )}
      {s && (
        <>
          <Row label="Guardar diagnósticos" hint="Permite usar «Comparar mi PC». Si lo desactiva, no se guardan nuevos diagnósticos.">
            <Toggle label="Guardar diagnósticos" checked={s.history_enabled} onChange={(v) => set('history_enabled', v)} />
          </Row>
          <Row label="Guardar conversaciones del asistente" hint="Si lo desactiva, las conversaciones solo duran mientras la ventana está abierta.">
            <Toggle label="Guardar conversaciones" checked={s.conversations_enabled} onChange={(v) => set('conversations_enabled', v)} />
          </Row>
        </>
      )}
      <div className="flex flex-wrap gap-2 border-t border-line pt-4">
        {(Object.keys(LABELS) as What[]).map((w) => (
          <button key={w} onClick={() => setPending(w)} className="flex items-center gap-1.5 rounded-xl border border-line px-3 py-2 text-sm text-muted hover:border-danger hover:text-danger">
            <Trash2 size={14} /> Borrar {w === 'diagnostics' ? 'diagnósticos' : w === 'conversations' ? 'conversaciones' : 'registro de acciones'}
          </button>
        ))}
      </div>
      {msg && <p className="mt-3 text-sm text-muted" role="status">{msg}</p>}
      {pending && (
        <Confirm title="¿Borrar estos datos?" confirmLabel="Borrar" danger onConfirm={clear} onCancel={() => setPending(null)}>
          <p>Se eliminará {LABELS[pending]} de este equipo. No se puede deshacer.</p>
        </Confirm>
      )}
    </Card>
  )
}
