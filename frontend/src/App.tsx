import { useState } from 'react'
import { ErrorBoundary } from './components/ErrorBoundary'
import { Lens3D } from './components/Lens3D'
import { LogoMark } from './components/Logo'
import { Onboarding } from './components/Onboarding'
import { Footer, Sidebar, TopBar, type PageId } from './components/Shell'
import { MetricsProvider, useMetrics } from './lib/metrics'
import { PrefsProvider, usePrefs } from './lib/prefs'
import { Dashboard } from './pages/Dashboard'
import { ProcessesPage } from './pages/Processes'
import { ComparePage } from './pages/Compare'
import { SecurityPage } from './pages/Security'
import { ScriptsPage } from './pages/Scripts'
import { OptimizePage } from './pages/Optimize'
import { AssistantPage } from './pages/Assistant'
import { ReportsPage } from './pages/Reports'
import { AboutPage, SettingsPage } from './pages/Other'
import { RemotePage } from './pages/Remote'
import { FleetPage } from './pages/Fleet'
import { StatsPage } from './pages/Stats'
import { Audit30Page } from './pages/Audit30'

const TITLES: Record<PageId, string> = {
  panel: 'Panel general',
  procesos: 'Procesos',
  optimizar: 'Optimizar con supervisión',
  seguridad: 'Centro de seguridad',
  scripts: 'Analizador de scripts',
  asistente: 'Asistente inteligente',
  comparar: 'Historial y comparación',
  informes: 'Informes',
  estadisticas: 'Estadísticas de mi PC',
  auditoria: 'Auditoría de Windows — 30 controles',
  equipos: 'Mis computadoras',
  remoto: 'Acceso remoto',
  ajustes: 'Configuración',
  acerca: 'Acerca de ScriptLens',
}

function Splash({ error }: { error: string | null }) {
  return (
    <div className="grid h-full place-items-center">
      <div className="flex flex-col items-center gap-5 text-center">
        <div className="animate-rise grid place-items-center">
          <Lens3D size={150} />
          <LogoMark size={44} />
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

  return (
    <div className="flex h-full">
      <Sidebar page={page} onNavigate={setPage} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={TITLES[page]} />
        <main className="flex-1 overflow-y-auto px-6 py-6" key={page}>
          <ErrorBoundary resetKey={page}>
          {page === 'panel' && <Dashboard />}
          {page === 'procesos' && <ProcessesPage />}
          {page === 'comparar' && <ComparePage />}
          {page === 'seguridad' && <SecurityPage />}
          {page === 'scripts' && <ScriptsPage />}
          {page === 'asistente' && <AssistantPage />}
          {page === 'informes' && <ReportsPage />}
          {page === 'optimizar' && <OptimizePage goProcesses={() => setPage('procesos')} />}
          {page === 'ajustes' && <SettingsPage />}
          {page === 'acerca' && <AboutPage />}
          {page === 'remoto' && <RemotePage />}
          {page === 'equipos' && <FleetPage />}
          {page === 'estadisticas' && <StatsPage />}
          {page === 'auditoria' && <Audit30Page />}
          </ErrorBoundary>
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
