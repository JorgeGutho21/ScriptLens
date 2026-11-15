import { ExternalLink, Hammer } from 'lucide-react'
import type { ReactNode } from 'react'
import { LogoMark } from '../components/Logo'
import { Card } from '../components/ui'
import { usePrefs } from '../lib/prefs'
import { APP_VERSION, REPOSITORY_URL } from '../version'
import { PrivacyCard } from './Privacy'

/** Módulo aún no implementado: se indica con honestidad, sin datos simulados. */
export function Planned({ title, description }: { title: string; description: string }) {
  return (
    <div className="mx-auto max-w-2xl pt-10">
      <Card>
        <div className="flex flex-col items-center gap-4 py-8 text-center">
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-accent-soft text-accent">
            <Hammer size={26} />
          </div>
          <h2 className="font-display text-xl font-semibold">{title}</h2>
          <p className="max-w-md leading-relaxed text-muted">{description}</p>
          <p className="text-xs text-faint">Este módulo está en desarrollo. No se muestran datos de ejemplo para evitar confusiones.</p>
        </div>
      </Card>
    </div>
  )
}

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
      <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-5' : 'translate-x-0.5'}`} />
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

export function AboutPage() {
  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <div className="flex items-center gap-4">
          <LogoMark size={64} />
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
            <a href={REPOSITORY_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-accent hover:underline">
              github.com/JorgeGutho21/ScriptLens <ExternalLink size={13} />
            </a>
          </dd>
          <dt className="text-faint">Licencia</dt>
          <dd className="text-fg">MIT. Componentes de terceros: ver THIRD_PARTY_NOTICES.md</dd>
        </dl>
        <p className="mt-5 border-t border-line pt-4 text-xs leading-relaxed text-faint">
          Privacidad: todo el análisis se realiza en este equipo. ScriptLens no envía listas de procesos, registros ni datos personales a ningún servidor.
        </p>
      </Card>
    </div>
  )
}
