import { Power, ShieldCheck, XCircle } from 'lucide-react'
import type { ProcessDetail } from '../lib/api'
import { useSupervised } from '../lib/supervised'

/** Acciones supervisadas sobre un proceso: primero la opción menos invasiva. */
export function ProcessActions({ detail, onDone }: { detail: ProcessDetail; onDone: () => void }) {
  const { request, dialog, banner } = useSupervised((r) => r.resultado === 'completada' && setTimeout(onDone, 1500))
  if (!detail.can_terminate)
    return (
      <div className="flex items-start gap-2.5 rounded-xl border border-line bg-surface-2 p-3 text-[13px] text-muted">
        <ShieldCheck size={17} className="mt-0.5 shrink-0 text-ok" />
        {detail.terminate_reason}
      </div>
    )
  const ident = { pid: detail.pid, create_time: detail.create_time, nombre: detail.name }
  const service = detail.category === 'servicio'
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {detail.category === 'aplicacion' && (
          <button
            onClick={() => request('/api/actions/process/prepare', { accion: 'cerrar', ...ident }, `¿Solicitar el cierre de ${detail.name}?`, 'Solicitar cierre')}
            className="flex items-center gap-1.5 rounded-xl bg-accent px-3.5 py-2 text-sm font-medium text-white hover:bg-accent-strong"
          >
            <Power size={15} /> Solicitar cierre
          </button>
        )}
        {!service && (
          <button
            onClick={() => request('/api/actions/process/prepare', { accion: 'finalizar', ...ident }, `¿Finalizar ${detail.name}?`, 'Finalizar proceso', true)}
            className="flex items-center gap-1.5 rounded-xl border border-line px-3.5 py-2 text-sm text-muted hover:border-danger hover:text-danger"
          >
            <XCircle size={15} /> Finalizar
          </button>
        )}
      </div>
      {service && <p className="text-xs text-faint">Los servicios de Windows no se detienen desde ScriptLens. Use la consola «Servicios» si es necesario.</p>}
      {banner}
      {dialog}
    </div>
  )
}
