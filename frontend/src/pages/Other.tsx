import { ExternalLink, RefreshCcw } from 'lucide-react'
import { useState } from 'react'
import { Lens3D } from '../components/Lens3D'
import { api, openLink } from '../lib/api'
import type { ReactNode } from 'react'
import { LogoMark } from '../components/Logo'
import { Card } from '../components/ui'
import { usePrefs } from '../lib/prefs'
import { APP_VERSION, REPOSITORY_URL } from '../version'
import { PrivacyCard } from './Privacy'

function Row({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-6 border-t border-line py-4 first:border-t-0 first:pt-0">
      <div>
        <div className="text-sm font-medium text-fg">{label}</div>
        {hint && <div className="mt-0.5 text-[13px] text-muted">{hint}</div>}
      </div>
      {children}
    </div>
  )
}

function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${checked ? 'bg-accent' : 'bg-surface-3'}`}
    >
      <span className={`absolute left-0 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-5' : 'translate-x-0.5'}`} />
    </button>
  )
}

export function SettingsPage() {
  const { prefs, update } = usePrefs()
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-5">
      <Card title="Apariencia y accesibilidad">
        <Row label="Modo oscuro" hint="Colores oscuros, más cómodos con poca luz.">
          <Toggle label="Modo oscuro" checked={prefs.theme === 'dark'} onChange={(v) => update({ theme: v ? 'dark' : 'light' })} />
        </Row>
        <Row label="Tamaño del texto" hint={`${Math.round(prefs.fontScale * 100)} %`}>
          <input
            type="range"
            min={0.9}
            max={1.3}
            step={0.05}
            value={prefs.fontScale}
            onChange={(e) => update({ fontScale: Number(e.target.value) })}
            aria-label="Tamaño del texto"
            className="w-44 accent-[var(--accent)]"
          />
        </Row>
        <Row label="Reducir animaciones" hint="Desactiva transiciones y movimientos.">
          <Toggle label="Reducir animaciones" checked={prefs.reducedMotion} onChange={(v) => update({ reducedMotion: v })} />
        </Row>
        <Row label="Modo avanzado" hint="Muestra núcleos, consumo sostenido y datos técnicos.">
          <Toggle label="Modo avanzado" checked={prefs.mode === 'avanzado'} onChange={(v) => update({ mode: v ? 'avanzado' : 'sencillo' })} />
        </Row>
        <Row label="Guía de bienvenida" hint="Vuelva a ver la explicación inicial.">
          <button type="button" onClick={() => update({ onboarded: false })} className="rounded-xl border border-line px-3.5 py-2 text-sm text-fg hover:bg-surface-2">
            Mostrar
          </button>
        </Row>
      </Card>
      <PrivacyCard Row={Row} Toggle={Toggle} />
    </div>
  )
}

interface UpdateInfo {
  actual: string
  ultima: string | null
  hay_nueva: boolean
  url?: string
  mensaje: string
}

export function AboutPage() {
  const [upd, setUpd] = useState<UpdateInfo | null>(null)
  const [checking, setChecking] = useState(false)
  const check = async () => {
    setChecking(true)
    try {
      setUpd(await api<UpdateInfo>('/api/updates/check'))
    } finally {
      setChecking(false)
    }
  }
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-5">
      <Card>
        <div className="flex items-center gap-4">
          <div className="relative">
            <LogoMark size={64} />
          </div>
          <div className="ml-auto order-last hidden sm:block">
            <Lens3D size={120} />
          </div>
          <div>
            <h2 className="font-display text-2xl font-semibold">
              ScriptLens <span className="text-accent">IA</span>
            </h2>
            <p className="text-sm text-muted">Versión {APP_VERSION}</p>
          </div>
        </div>
        <p className="mt-5 leading-relaxed text-muted">
          Sistema inteligente de diagnóstico, seguridad, auditoría y optimización del sistema operativo Windows. Proyecto académico del programa de
          Ingeniería de Sistemas de la Universidad Popular del Cesar, presentado en ExpoSoftware 2026-II.
        </p>
        <dl className="mt-5 grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
          <dt className="text-faint">Desarrollado por</dt>
          <dd className="text-fg">Jorge Gutiérrez</dd>
          <dt className="text-faint">GitHub</dt>
          <dd className="text-fg">@JorgeGutho21</dd>
          <dt className="text-faint">Repositorio</dt>
          <dd>
            <button onClick={() => openLink(REPOSITORY_URL)} className="inline-flex items-center gap-1 text-accent hover:underline">
              github.com/JorgeGutho21/ScriptLens <ExternalLink size={13} />
            </button>
          </dd>
          <dt className="text-faint">Licencia</dt>
          <dd className="text-fg">MIT. Componentes de terceros: ver THIRD_PARTY_NOTICES.md</dd>
        </dl>
        <p className="mt-5 border-t border-line pt-4 text-xs leading-relaxed text-faint">
          Privacidad: todo el análisis se realiza en este equipo. ScriptLens no envía listas de procesos, registros ni datos personales a ningún servidor.
        </p>
      </Card>
      <Card title="Actualizaciones">
        <p className="mb-3 text-sm text-muted">ScriptLens solo consulta GitHub cuando usted pulsa el botón, no envía datos del equipo y nunca instala actualizaciones por sí misma.</p>
        <button onClick={check} disabled={checking} className="flex items-center gap-2 rounded-xl border border-line px-4 py-2 text-sm hover:bg-surface-2 disabled:opacity-60">
          <RefreshCcw size={15} className={checking ? 'animate-spin' : ''} /> Buscar actualizaciones
        </button>
        {upd && (
          <div className="mt-3 text-sm" role="status">
            <p className={upd.hay_nueva ? 'text-warn' : 'text-muted'}>{upd.mensaje}</p>
            <p className="text-xs text-faint">Versión instalada: {upd.actual}{upd.ultima ? ` · Última publicada: ${upd.ultima}` : ''}</p>
            {upd.hay_nueva && upd.url && (
              <button onClick={() => openLink(upd.url!)} className="mt-2 text-accent hover:underline">
                Abrir la página de la versión
              </button>
            )}
          </div>
        )}
      </Card>
    </div>
  )
}
