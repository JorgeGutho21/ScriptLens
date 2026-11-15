import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

/** Preferencias de interfaz guardadas solo en este equipo. */
export interface Prefs {
  theme: 'dark' | 'light'
  fontScale: number
  reducedMotion: boolean
  mode: 'sencillo' | 'avanzado'
  onboarded: boolean
}

const DEFAULTS: Prefs = { theme: 'dark', fontScale: 1, reducedMotion: false, mode: 'sencillo', onboarded: false }
const KEY = 'scriptlens.prefs.v1'

function load(): Prefs {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? { ...DEFAULTS, ...JSON.parse(raw) } : DEFAULTS
  } catch {
    return DEFAULTS
  }
}

interface Ctx {
  prefs: Prefs
  update: (patch: Partial<Prefs>) => void
}

const PrefsContext = createContext<Ctx | null>(null)

export function PrefsProvider({ children }: { children: ReactNode }) {
  const [prefs, setPrefs] = useState<Prefs>(load)

  useEffect(() => {
    const root = document.documentElement
    root.dataset.theme = prefs.theme
    root.dataset.motion = prefs.reducedMotion ? 'reduced' : 'full'
    root.style.setProperty('--font-scale', String(prefs.fontScale))
    try {
      localStorage.setItem(KEY, JSON.stringify(prefs))
    } catch {
      /* almacenamiento no disponible: las preferencias duran la sesión */
    }
  }, [prefs])

  return <PrefsContext.Provider value={{ prefs, update: (p) => setPrefs((s) => ({ ...s, ...p })) }}>{children}</PrefsContext.Provider>
}

export function usePrefs(): Ctx {
  const ctx = useContext(PrefsContext)
  if (!ctx) throw new Error('usePrefs fuera de PrefsProvider')
  return ctx
}
