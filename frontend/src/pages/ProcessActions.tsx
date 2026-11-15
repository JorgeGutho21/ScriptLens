import { ShieldCheck } from 'lucide-react'
import type { ProcessDetail } from '../lib/api'

/** Acciones sobre un proceso. Las acciones supervisadas se habilitan en la fase 6. */
export function ProcessActions({ detail }: { detail: ProcessDetail; onDone: () => void }) {
  if (detail.can_terminate) return null
  return (
    <div className="flex items-start gap-2.5 rounded-xl border border-line bg-surface-2 p-3 text-[13px] text-muted">
      <ShieldCheck size={17} className="mt-0.5 shrink-0 text-ok" />
      {detail.terminate_reason}
    </div>
  )
}
