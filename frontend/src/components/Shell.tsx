import {
  Bot,
  FileCode2,
  FileText,
  GitCompareArrows,
  Info,
  LayoutDashboard,
  ListTree,
  Moon,
  Settings,
  ShieldCheck,
  Sun,
} from 'lucide-react'
import type { ReactNode } from 'react'
import { pct } from '../lib/format'
import { useMetrics } from '../lib/metrics'
import { usePrefs } from '../lib/prefs'
import { APP_VERSION } from '../version'
import { Logo } from './Logo'

export type PageId = 'panel' | 'procesos' | 'seguridad' | 'scripts' | 'asistente' | 'comparar' | 'informes' | 'ajustes' | 'acerca'

export const NAV: { id: PageId; label: string; icon: ReactNode; ready: boolean }[] = [
  { id: 'panel', label: 'Panel general', icon: <LayoutDashboard size={18} />, ready: true },
  { id: 'procesos', label: 'Procesos', icon: <ListTree size={18} />, ready: true },
  { id: 'seguridad', label: 'Seguridad', icon: <ShieldCheck size={18} />, ready: true },
  { id: 'scripts', label: 'Analizar scripts', icon: <FileCode2 size={18} />, ready: false },
  { id: 'asistente', label: 'Asistente IA', icon: <Bot size={18} />, ready: false },
  { id: 'comparar', label: 'Comparar mi PC', icon: <GitCompareArrows size={18} />, ready: true },
  { id: 'informes', label: 'Informes', icon: <FileText size={18} />, ready: false },
]

const BOTTOM: typeof NAV = [
  { id: 'ajustes', label: 'Ajustes', icon: <Settings size={18} />, ready: true },
  { id: 'acerca', label: 'Acerca de', icon: <Info size={18} />, ready: true },
]

export function Sidebar({ page, onNavigate }: { page: PageId; onNavigate: (p: PageId) => void }) {
  const item = (n: (typeof NAV)[number]) => {
    const active = n.id === page
    return (
      <li key={n.id}>
        <button
          type="button"
          onClick={() => onNavigate(n.id)}
          aria-current={active ? 'page' : undefined}
          className={`group relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition-colors ${
            active ? 'bg-accent-soft font-medium text-fg' : 'text-muted hover:bg-surface-2 hover:text-fg'
          }`}
        >
          {active && <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-full bg-accent" />}
          <span className={active ? 'text-accent' : 'text-faint group-hover:text-muted'}>{n.icon}</span>
          <span className="hidden truncate lg:inline">{n.label}</span>
          {!n.ready && <span className="ml-auto hidden rounded-md bg-surface-3 px-1.5 py-0.5 text-[10px] text-faint lg:inline">Próximo</span>}
        </button>
      </li>
    )
  }
  return (
    <nav aria-label="Navegación principal" className="flex w-[68px] shrink-0 flex-col border-r border-line bg-surface/60 px-2.5 py-4 backdrop-blur lg:w-[244px] lg:px-3.5">
      <div className="mb-6 px-1.5">
        <div className="hidden lg:block">
          <Logo />
        </div>
        <div className="lg:hidden">
          <Logo compact />
        </div>
      </div>
      <ul className="flex flex-col gap-1">{NAV.map(item)}</ul>
      <ul className="mt-auto flex flex-col gap-1 border-t border-line pt-3">{BOTTOM.map(item)}</ul>
    </nav>
  )
}

export function TopBar({ title }: { title: string }) {
  const { summary, error } = useMetrics()
  const { prefs, update } = usePrefs()
  const cur = summary?.current
  const connected = !!summary && !error

  return (
    <header className="flex h-16 shrink-0 items-center gap-4 border-b border-line bg-surface/40 px-6 backdrop-blur">
      <h1 className="font-display text-lg font-semibold tracking-tight">{title}</h1>
      <div className="ml-auto flex items-center gap-3">
        <div className="hidden items-center gap-4 rounded-xl border border-line bg-surface-2 px-3.5 py-1.5 text-xs tabular md:flex" aria-live="polite">
          <span className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${connected ? 'pulse-dot bg-ok' : 'bg-danger'}`} />
            <span className="text-muted">{connected ? 'Midiendo en tiempo real' : 'Motor desconectado'}</span>
          </span>
          {cur && (
            <>
              <span className="text-faint">CPU <span className="font-semibold text-fg">{pct(cur.cpu_percent)}</span></span>
              <span className="text-faint">RAM <span className="font-semibold text-fg">{pct(cur.mem_percent)}</span></span>
            </>
          )}
        </div>
        <div role="radiogroup" aria-label="Modo de visualización" className="flex rounded-xl border border-line bg-surface-2 p-0.5 text-xs">
          {(['sencillo', 'avanzado'] as const).map((m) => (
            <button
              key={m}
              role="radio"
              aria-checked={prefs.mode === m}
              onClick={() => update({ mode: m })}
              className={`rounded-[10px] px-3 py-1.5 capitalize transition-colors ${prefs.mode === m ? 'bg-accent text-white' : 'text-muted hover:text-fg'}`}
            >
              {m}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={() => update({ theme: prefs.theme === 'dark' ? 'light' : 'dark' })}
          className="grid h-9 w-9 place-items-center rounded-xl border border-line bg-surface-2 text-muted hover:text-fg"
          aria-label={prefs.theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
        >
          {prefs.theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        </button>
      </div>
    </header>
  )
}

export function Footer() {
  return (
    <footer className="flex h-9 shrink-0 items-center justify-between border-t border-line px-6 text-[11.5px] text-faint">
      <span>
        ScriptLens IA v{APP_VERSION} · Desarrollado por <span className="text-muted">Jorge Gutiérrez</span> · GitHub: @JorgeGutho21
      </span>
      <span>Análisis local · sus datos no salen de este equipo</span>
    </footer>
  )
}
