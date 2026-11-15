import { useEffect, useId, useRef, useState, type ReactNode } from 'react'
import { GLOSSARY } from '../lib/glossary'

/** Término del glosario: al pulsarlo muestra una explicación sencilla. */
export function Term({ id, children }: { id: keyof typeof GLOSSARY; children?: ReactNode }) {
  const entry = GLOSSARY[id]
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLSpanElement>(null)
  const tipId = useId()

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    const onClick = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false)
    window.addEventListener('keydown', onKey)
    window.addEventListener('mousedown', onClick)
    return () => {
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('mousedown', onClick)
    }
  }, [open])

  return (
    <span ref={ref} className="relative inline-block">
      <button
        type="button"
        className="cursor-help rounded-sm underline decoration-dotted decoration-faint underline-offset-4 hover:decoration-accent"
        aria-expanded={open}
        aria-describedby={open ? tipId : undefined}
        onClick={() => setOpen((v) => !v)}
      >
        {children ?? entry.term}
      </button>
      {open && (
        <span
          id={tipId}
          role="tooltip"
          className="animate-rise absolute left-0 top-full z-50 mt-2 block w-72 rounded-xl border border-line-strong bg-surface-2 p-3.5 text-left text-[13px] font-normal normal-case leading-relaxed tracking-normal text-muted shadow-2xl"
        >
          <span className="mb-1 block font-semibold text-fg">{entry.term}</span>
          {entry.text}
        </span>
      )}
    </span>
  )
}
