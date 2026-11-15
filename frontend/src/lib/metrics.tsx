import { createContext, useContext, type ReactNode } from 'react'
import { api, type Summary, type SystemInfo } from './api'
import { usePolling } from './usePolling'

interface MetricsCtx {
  summary: Summary | null
  info: SystemInfo | null
  error: string | null
}

const Ctx = createContext<MetricsCtx>({ summary: null, info: null, error: null })

/** Fuente compartida de métricas para la barra superior y las páginas. */
export function MetricsProvider({ children }: { children: ReactNode }) {
  const summary = usePolling(() => api<Summary>('/api/metrics/summary'), 1500)
  const info = usePolling(() => api<SystemInfo>('/api/system/info'), 30000)
  return <Ctx.Provider value={{ summary: summary.data, info: info.data, error: summary.error ?? info.error }}>{children}</Ctx.Provider>
}

export const useMetrics = () => useContext(Ctx)
