import { useState } from 'react'
import { Confirm } from '../components/Confirm'
import { apiPost } from './api'

export interface Prepared {
  token: string
  resumen: string
  advertencias: string[]
  expira_en: number
}

export interface Executed {
  resultado: 'completada' | 'solicitada' | 'fallida' | 'cancelada'
  detalle: string
  accion_id: number
}

/**
 * Flujo de acción supervisada: preparar (resumen) → confirmación explícita → ejecutar.
 * El botón con foco inicial del diálogo es «Cancelar».
 */
export function useSupervised(onDone?: (r: Executed) => void) {
  const [prepared, setPrepared] = useState<(Prepared & { title: string; label: string; danger: boolean }) | null>(null)
  const [busy, setBusy] = useState(false)
  const [preparing, setPreparing] = useState(false)
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null)

  const request = async (path: string, body: unknown, title: string, label: string, danger = false) => {
    if (preparing) return // evita solicitudes duplicadas mientras se prepara el resumen
    setMessage(null)
    setPreparing(true)
    try {
      const p = await apiPost<Prepared>(path, body)
      setPrepared({ ...p, title, label, danger })
    } catch (e) {
      setMessage({ ok: false, text: (e as Error).message })
    } finally {
      setPreparing(false)
    }
  }

  const confirm = async () => {
    if (!prepared) return
    setBusy(true)
    try {
      const r = await apiPost<Executed>('/api/actions/execute', { token: prepared.token })
      setMessage({ ok: r.resultado !== 'fallida', text: r.detalle })
      onDone?.(r)
    } catch (e) {
      setMessage({ ok: false, text: (e as Error).message })
    } finally {
      setBusy(false)
      setPrepared(null)
    }
  }

  const dialog = prepared ? (
    <Confirm title={prepared.title} confirmLabel={prepared.label} danger={prepared.danger} busy={busy} onConfirm={confirm} onCancel={() => setPrepared(null)}>
      <p>{prepared.resumen}</p>
      {prepared.advertencias.length > 0 && (
        <ul className="list-disc space-y-0.5 pl-5 text-warn">
          {prepared.advertencias.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      )}
      <p className="text-xs text-faint">Esta confirmación caduca en {prepared.expira_en} segundos. La acción quedará registrada.</p>
    </Confirm>
  ) : null

  const banner = preparing ? (
    <p role="status" aria-live="polite" className="flex items-center gap-2 rounded-xl bg-surface-2 px-3.5 py-2.5 text-sm text-muted">
      <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-accent border-t-transparent" aria-hidden="true" />
      Preparando el resumen de la acción… Nada se modifica hasta que usted confirme.
    </p>
  ) : message ? (
    <p role="status" className={`rounded-xl px-3.5 py-2.5 text-sm ${message.ok ? 'bg-ok-soft text-ok' : 'bg-danger-soft text-danger'}`}>
      {message.text}
    </p>
  ) : null

  return { request, dialog, banner, preparing }
}
