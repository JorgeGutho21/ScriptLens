import { useEffect, useRef, useState } from 'react'

/**
 * Consulta periódica que se pausa cuando la ventana no está visible,
 * para que ScriptLens no consuma recursos mientras está minimizado.
 */
export function usePolling<T>(fn: () => Promise<T>, intervalMs: number, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fnRef = useRef(fn)
  fnRef.current = fn

  useEffect(() => {
    let cancelled = false
    let timer: number | undefined

    const tick = async () => {
      let failed = false
      if (document.visibilityState === 'visible') {
        try {
          const result = await fnRef.current()
          if (!cancelled) {
            setData(result)
            setError(null)
          }
        } catch (e) {
          failed = true
          if (!cancelled) setError(e instanceof Error ? e.message : String(e))
        }
      }
      // Tras un fallo se reintenta pronto, aunque el intervalo normal sea largo.
      if (!cancelled) timer = window.setTimeout(tick, failed ? Math.min(intervalMs, 2000) : intervalMs)
    }
    tick()
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, ...deps])

  return { data, error }
}
