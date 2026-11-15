import { useState } from 'react'
import { LogoMark } from './components/Logo'
import { Onboarding } from './components/Onboarding'
import { Footer, NAV, Sidebar, TopBar, type PageId } from './components/Shell'
import { MetricsProvider, useMetrics } from './lib/metrics'
import { PrefsProvider, usePrefs } from './lib/prefs'
import { Dashboard } from './pages/Dashboard'
import { ProcessesPage } from './pages/Processes'
import { ComparePage } from './pages/Compare'
import { SecurityPage } from './pages/Security'
import { AboutPage, Planned, SettingsPage } from './pages/Other'

const TITLES: Record<PageId, string> = {
  panel: 'Panel general',
  procesos: 'Procesos',
  seguridad: 'Centro de seguridad',
  scripts: 'Analizador de scripts',
  asistente: 'Asistente inteligente',
  comparar: 'Comparar mi computador',
  informes: 'Informes',
  ajustes: 'Ajustes',
  acerca: 'Acerca de ScriptLens',
}

const PLANNED: Partial<Record<PageId, string>> = {
  scripts: 'Análisis sin ejecución de archivos BAT, CMD y PowerShell con reglas, técnicas MITRE ATT&CK y regresión logística balanceada.',
  asistente: 'Asistente local con Ollama y Qwen3 que responde con base en las mediciones reales de este equipo.',
  informes: 'Informes PDF y HTML con métricas, hallazgos, recomendaciones y limitaciones.',
}

function Splash({ error }: { error: string | null }) {
  return (
    <div className="grid h-full place-items-center">
      <div className="flex flex-col items-center gap-5 text-center">
        <div className="animate-rise">
          <LogoMark size={76} />
        </div>
        <div>
          <div className="font-display text-2xl font-semibold">
            ScriptLens <span className="text-accent">IA</span>
          </div>
          <div className="mt-1 text-sm text-faint">Desarrollado por Jorge Gutiérrez · @JorgeGutho21</div>
        </div>
        {error ? (
          <p className="max-w-sm text-sm text-danger" role="alert">
            No fue posible iniciar el motor de análisis: {error}
          </p>
        ) : (
          <div className="flex items-center gap-2 text-sm text-muted" role="status">
            <span className="pulse-dot h-2 w-2 rounded-full bg-accent" />
            Iniciando el motor de análisis…
          </div>
        )}
      </div>
    </div>
  )
}

function Main() {
  const [page, setPage] = useState<PageId>('panel')
  const { summary, error } = useMetrics()
  const { prefs } = usePrefs()

  if (!summary) return <Splash error={error} />

  const label = NAV.find((n) => n.id === page)?.label
  return (
    <div className="flex h-full">
      <Sidebar page={page} onNavigate={setPage} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={TITLES[page]} />
        <main className="flex-1 overflow-y-auto px-6 py-6" key={page}>
          {page === 'panel' && <Dashboard />}
          {page === 'procesos' && <ProcessesPage />}
          {page === 'comparar' && <ComparePage />}
          {page === 'seguridad' && <SecurityPage />}
          {page === 'ajustes' && <SettingsPage />}
          {page === 'acerca' && <AboutPage />}
          {PLANNED[page] && <Planned title={label ?? TITLES[page]} description={PLANNED[page]!} />}
        </main>
        <Footer />
      </div>
      {!prefs.onboarded && <Onboarding />}
    </div>
  )
}

export default function App() {
  return (
    <PrefsProvider>
      <MetricsProvider>
        <Main />
      </MetricsProvider>
    </PrefsProvider>
  )
}
