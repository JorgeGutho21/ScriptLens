import { ArrowLeft, ArrowRight, Bot, Eye, Gauge, Lock, MousePointerClick, ShieldCheck, Sparkles, Zap } from 'lucide-react'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { usePrefs } from '../lib/prefs'
import { LogoMark } from './Logo'

const STEPS: { icon: ReactNode; title: string; text: string }[] = [
  { icon: <Sparkles size={22} />, title: 'Qué hace ScriptLens', text: 'Le ayuda a entender por qué su computador va lento, qué programas están funcionando y si hay algo que merezca revisión, explicado en palabras sencillas.' },
  { icon: <Eye size={22} />, title: 'Qué información analiza', text: 'Uso del procesador y la memoria, espacio en disco, actividad de red y los programas en ejecución. Más adelante también programas de inicio y el estado de seguridad de Windows.' },
  { icon: <Lock size={22} />, title: 'Sus datos se quedan aquí', text: 'Todo se analiza en este equipo. ScriptLens no envía sus procesos, archivos ni registros a Internet.' },
  { icon: <Zap size={22} />, title: 'Cómo se activa el análisis', text: 'El análisis empieza solo al abrir la aplicación y se pausa cuando la ventana está minimizada, para no gastar recursos.' },
  { icon: <Gauge size={22} />, title: 'Cómo leer los resultados', text: 'Verde o azul significa normal. Amarillo indica consumo elevado. Rojo indica algo que conviene revisar. Pulse cualquier palabra subrayada para ver qué significa.' },
  { icon: <MousePointerClick size={22} />, title: 'Qué puede hacer usted', text: 'Ver qué programas consumen más, comparar mediciones y, en próximas versiones, cerrar programas o desactivar inicios automáticos con su autorización.' },
  { icon: <ShieldCheck size={22} />, title: 'Nada sin su permiso', text: 'Ninguna acción que cambie su equipo se ejecuta sin una confirmación explícita. ScriptLens nunca desactiva el antivirus, el firewall ni las actualizaciones.' },
  { icon: <Bot size={22} />, title: 'Asistente con IA local', text: 'Puede activar un asistente que responde preguntas usando las mediciones reales. Funciona con Ollama en su propio equipo; le explicaremos cómo instalarlo cuando quiera usarlo.' },
]

export function Onboarding() {
  const { update } = usePrefs()
  const [step, setStep] = useState(0)
  const dialog = useRef<HTMLDivElement>(null)
  const last = step === STEPS.length - 1
  const s = STEPS[step]

  useEffect(() => dialog.current?.focus(), [step])

  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-black/55 p-6 backdrop-blur-sm">
      <div ref={dialog} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby="ob-title" className="card animate-rise w-full max-w-lg p-7 outline-none">
        <div className="flex items-center gap-3">
          <LogoMark size={36} />
          <div className="text-sm text-muted">Bienvenido a ScriptLens IA</div>
          <div className="ml-auto text-xs text-faint tabular">
            {step + 1} / {STEPS.length}
          </div>
        </div>
        <div key={step} className="animate-rise mt-7">
          <div className="grid h-12 w-12 place-items-center rounded-2xl bg-accent-soft text-accent">{s.icon}</div>
          <h2 id="ob-title" className="mt-4 font-display text-xl font-semibold">
            {s.title}
          </h2>
          <p className="mt-2 leading-relaxed text-muted">{s.text}</p>
        </div>
        <div className="mt-6 flex gap-1.5" aria-hidden="true">
          {STEPS.map((_, i) => (
            <span key={i} className={`h-1 flex-1 rounded-full transition-colors ${i <= step ? 'bg-accent' : 'bg-surface-3'}`} />
          ))}
        </div>
        <div className="mt-6 flex items-center gap-3">
          <button type="button" onClick={() => update({ onboarded: true })} className="text-sm text-faint hover:text-muted">
            Omitir
          </button>
          <div className="ml-auto flex gap-2">
            {step > 0 && (
              <button type="button" onClick={() => setStep(step - 1)} className="flex items-center gap-1.5 rounded-xl border border-line px-4 py-2 text-sm hover:bg-surface-2">
                <ArrowLeft size={15} /> Atrás
              </button>
            )}
            <button
              type="button"
              onClick={() => (last ? update({ onboarded: true }) : setStep(step + 1))}
              className="flex items-center gap-1.5 rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-strong"
            >
              {last ? 'Comenzar' : 'Siguiente'} {!last && <ArrowRight size={15} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
