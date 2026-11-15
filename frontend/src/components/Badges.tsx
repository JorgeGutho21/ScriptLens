import { AlertTriangle, BadgeCheck, CheckCircle2, HelpCircle, Info, ShieldAlert, ShieldX, SearchCheck, Loader2, ShieldQuestion } from 'lucide-react'
import type { ReactNode } from 'react'
import type { EstadoProceso } from '../lib/api'

const ESTADOS: Record<EstadoProceso, { label: string; cls: string; icon: ReactNode }> = {
  normal: { label: 'Normal según la evidencia', cls: 'bg-ok-soft text-ok', icon: <CheckCircle2 size={14} /> },
  informativo: { label: 'Informativo', cls: 'bg-accent-soft text-info', icon: <Info size={14} /> },
  consumo_elevado: { label: 'Consumo elevado', cls: 'bg-warn-soft text-warn', icon: <AlertTriangle size={14} /> },
  requiere_revision: { label: 'Requiere revisión', cls: 'bg-warn-soft text-warn', icon: <SearchCheck size={14} /> },
  actividad_sospechosa: { label: 'Actividad sospechosa', cls: 'bg-danger-soft text-danger', icon: <ShieldAlert size={14} /> },
  amenaza_detectada: { label: 'Amenaza detectada', cls: 'bg-danger text-white', icon: <ShieldX size={14} /> },
  info_insuficiente: { label: 'Información insuficiente', cls: 'bg-surface-3 text-muted', icon: <HelpCircle size={14} /> },
}

export function EstadoPill({ estado, compact = false }: { estado: EstadoProceso; compact?: boolean }) {
  const e = ESTADOS[estado] ?? ESTADOS.info_insuficiente
  return (
    <span title={e.label} className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-[11.5px] font-medium ${e.cls}`}>
      {e.icon}
      {!compact && e.label}
    </span>
  )
}

const FIRMAS: Record<string, { label: string; cls: string; icon: ReactNode }> = {
  valida: { label: 'Firma válida', cls: 'text-ok', icon: <BadgeCheck size={14} /> },
  sin_firma: { label: 'Sin firma', cls: 'text-muted', icon: <ShieldQuestion size={14} /> },
  alterada: { label: 'Firma alterada', cls: 'text-danger', icon: <ShieldX size={14} /> },
  no_confiable: { label: 'No confiable', cls: 'text-danger', icon: <ShieldAlert size={14} /> },
  desconocido: { label: 'No verificable', cls: 'text-faint', icon: <HelpCircle size={14} /> },
  no_aplica: { label: 'No aplica', cls: 'text-faint', icon: <HelpCircle size={14} /> },
  pendiente: { label: 'Verificando…', cls: 'text-faint', icon: <Loader2 size={14} className="animate-spin" /> },
}

export function FirmaTag({ estado }: { estado: string | null }) {
  if (!estado) return <span className="text-xs text-faint">—</span>
  const f = FIRMAS[estado] ?? FIRMAS.desconocido
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap text-xs ${f.cls}`}>
      {f.icon}
      {f.label}
    </span>
  )
}

export function TipoTag({ tipo }: { tipo: 'comprobado' | 'estimado' }) {
  return tipo === 'comprobado' ? (
    <span className="rounded-md bg-ok-soft px-1.5 py-0.5 text-[10.5px] font-medium uppercase tracking-wide text-ok">Comprobado</span>
  ) : (
    <span className="rounded-md bg-surface-3 px-1.5 py-0.5 text-[10.5px] font-medium uppercase tracking-wide text-muted">Estimado</span>
  )
}
