import type { StartupItem } from './Security'

/** Estado de una entrada de inicio. La activación/desactivación supervisada se habilita en la fase 6. */
export function StartupActions({ item }: { item: StartupItem; onChanged: () => void }) {
  return <span className={`text-xs ${item.habilitado ? 'text-ok' : 'text-faint'}`}>{item.habilitado ? 'Habilitado' : 'Deshabilitado'}</span>
}
