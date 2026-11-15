import { AlertTriangle } from 'lucide-react'
import { useEffect, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'

/**
 * Diálogo de confirmación explícita para acciones importantes.
 * El botón por defecto (foco inicial) es «Cancelar», nunca la acción.
 * Se dibuja en un portal sobre <body>: si se renderizara dentro de una tarjeta con
 * transform (animación de entrada), «fixed» quedaría limitado a esa tarjeta.
 */
export function Confirm({
  title,
  children,
  confirmLabel,
  danger = false,
  busy = false,
  onConfirm,
  onCancel,
}: {
  title: string
  children: ReactNode
  confirmLabel: string
  danger?: boolean
  busy?: boolean
  onConfirm: () => void
  onCancel: () => void
}) {
  const cancelRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    cancelRef.current?.focus()
  }, [])
  return createPortal(
    <div className="fixed inset-0 z-[90] grid place-items-center bg-black/55 p-6 backdrop-blur-sm" onKeyDown={(e) => e.key === 'Escape' && !busy && onCancel()}>
      <div role="alertdialog" aria-modal="true" aria-labelledby="confirm-title" className="card animate-rise w-full max-w-md p-6">
        <div className="flex items-start gap-3">
          <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${danger ? 'bg-danger-soft text-danger' : 'bg-warn-soft text-warn'}`}>
            <AlertTriangle size={20} />
          </div>
          <div className="min-w-0">
            <h2 id="confirm-title" className="font-display text-lg font-semibold">
              {title}
            </h2>
            <div className="mt-2 space-y-2 text-sm leading-relaxed text-muted">{children}</div>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <button ref={cancelRef} type="button" disabled={busy} onClick={onCancel} className="rounded-xl border border-line px-4 py-2 text-sm hover:bg-surface-2">
            Cancelar
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={onConfirm}
            className={`rounded-xl px-4 py-2 text-sm font-medium text-white disabled:opacity-60 ${danger ? 'bg-danger hover:opacity-90' : 'bg-accent hover:bg-accent-strong'}`}
          >
            {busy ? 'Procesando…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
