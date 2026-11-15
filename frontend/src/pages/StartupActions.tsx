import { useSupervised } from '../lib/supervised'
import type { StartupItem } from './Security'

/** Activar o desactivar un inicio automático del usuario (reversible, con confirmación). */
export function StartupActions({ item, onChanged }: { item: StartupItem; onChanged: () => void }) {
  const { request, dialog, banner } = useSupervised((r) => r.resultado === 'completada' && onChanged())
  if (!item.modificable_sin_admin)
    return (
      <span className={`text-xs ${item.habilitado ? 'text-ok' : 'text-faint'}`} title="Requiere permisos de administrador">
        {item.habilitado ? 'Habilitado' : 'Deshabilitado'} · todos los usuarios
      </span>
    )
  return (
    <div className="flex flex-col items-end gap-1">
      <button
        role="switch"
        aria-checked={item.habilitado}
        aria-label={`${item.habilitado ? 'Desactivar' : 'Activar'} inicio automático de ${item.nombre}`}
        onClick={() =>
          request(
            '/api/actions/startup/prepare',
            { id: item.id, habilitar: !item.habilitado },
            `¿${item.habilitado ? 'Desactivar' : 'Activar'} el inicio automático de «${item.nombre}»?`,
            item.habilitado ? 'Desactivar' : 'Activar',
          )
        }
        className={`relative h-6 w-11 rounded-full transition-colors ${item.habilitado ? 'bg-accent' : 'bg-surface-3'}`}
      >
        <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${item.habilitado ? 'translate-x-5' : 'translate-x-0.5'}`} />
      </button>
      {banner}
      {dialog}
    </div>
  )
}
