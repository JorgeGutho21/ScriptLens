import { ArrowLeft, ArrowRight, BarChart3, Bot, ClipboardCheck, Eye, Gauge, Lock, MonitorSmartphone, MousePointerClick, ShieldCheck, Sparkles, Zap } from 'lucide-react'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { usePrefs } from '../lib/prefs'
import { LogoMark } from './Logo'

const STEPS: { icon: ReactNode; title: string; text: string }[] = [
  { icon: <Sparkles size={22} />, title: 'Qué hace ScriptLens', text: 'Le ayuda a entender por qué su computador va lento, qué programas están funcionando y si hay algo que merezca revisión, explicado en palabras sencillas.' },
  { icon: <Eye size={22} />, title: 'Qué información analiza', text: 'Uso del procesador y la memoria, espacio en disco, actividad de red y los programas en ejecución. Más adelante también programas de inicio y el estado de seguridad de Windows.' },
  { icon: <Lock size={22} />, title: 'Sus datos se quedan aquí', text: 'Todo se analiza en este equipo. ScriptLens no envía sus procesos, archivos ni registros a Internet.' },
  { icon: <Zap size={22} />, title: 'Cómo se activa el análisis', text: 'El análisis empieza solo al abrir la aplicación y se pausa cuando la ventana está minimizada, para no gastar recursos.' },
  { icon: <Gauge size={22} />, title: 'Cómo leer los resultados', text: 'Verde o azul significa normal. Amarillo indica consumo elevado. Rojo indica algo que conviene revisar. Pulse cualquier palabra subrayada para ver qué significa.' },
  { icon: <MousePointerClick size={22} />, title: 'Qué puede hacer usted', text: 'Ver qué programas consumen más, comparar mediciones, cerrar programas o desactivar inicios automáticos (siempre con su confirmación) y generar informes en PDF.' },
  { icon: <BarChart3 size={22} />, title: 'Estadísticas de su PC', text: 'En «Estadísticas» verá el consumo por hora, día y semana, cuándo se encendió el equipo y cuánto tiempo lo usó de forma activa. Puede pausarlas o borrarlas cuando quiera.' },
  { icon: <ClipboardCheck size={22} />, title: 'Auditoría de 30 controles', text: 'Revisa 30 configuraciones de seguridad de Windows (firewall, Defender, BitLocker, cuentas…) y explica cada resultado. Solo lee la configuración: no cambia nada.' },
  { icon: <MonitorSmartphone size={22} />, title: 'Ver su PC desde el celular', text: 'En «Acceso remoto» puede permitir que su celular u otra PC de la misma red vean estos datos. Está apagado hasta que usted lo active, es solo de consulta y usted autoriza cada dispositivo.' },
  { icon: <ShieldCheck size={22} />, title: 'Nada sin su permiso', text: 'Ninguna acción que cambie su equipo se ejecuta sin una confirmación explícita. ScriptLens nunca desactiva el antivirus, el firewall ni las actualizaciones.' },
  { icon: <Bot size={22} />, title: 'Asistente con IA local', text: 'Puede activar un asistente que responde preguntas usando las mediciones reales. Las preguntas sencillas se responden al instante; para explicaciones usa Ollama en su propio equipo, sin enviar datos a Internet.' },
]

export function Onboarding() {
  const { update } = usePrefs()
  const [step, setStep] = useState(0)
  const dialog = useRef<HTMLDivElement>(null)
  const last = step === STEPS.length - 1
  const s = STEPS[step]

  useEffect(() => {
    dialog.current?.focus()
  }, [step])

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
