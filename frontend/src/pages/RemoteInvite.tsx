import { Check, Copy, Mail, Send } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { Button, Notice } from '../components/controls'
import { Card } from '../components/ui'
import { apiDelete, apiPost } from '../lib/api'

export interface Invitation {
  id: string
  correo: string
  permisos: { procesos: boolean; seguridad: boolean; estadisticas: boolean }
  horas: number
  creada: number
  caduca: number
  usada: number | null
  estado: 'pendiente' | 'usada' | 'caducada' | 'revocada' | 'bloqueada'
  sesion_activa: boolean
}

interface InviteResult {
  invitacion: Invitation
  envio: { modo: 'local' | 'smtp'; archivo?: string; servidor?: string }
  enlace?: string
}

const ESTADO: Record<Invitation['estado'], { text: string; cls: string }> = {
  pendiente: { text: 'Pendiente', cls: 'bg-accent-soft text-accent' },
  usada: { text: 'Usada', cls: 'bg-ok-soft text-ok' },
  caducada: { text: 'Caducada', cls: 'bg-surface-3 text-muted' },
  revocada: { text: 'Revocada', cls: 'bg-surface-3 text-muted' },
  bloqueada: { text: 'Bloqueada', cls: 'bg-danger-soft text-danger' },
}
const PERM_LABEL = { procesos: 'Programas', seguridad: 'Seguridad', estadisticas: 'Estadísticas' } as const
const when = (ts: number | null) => (ts ? new Date(ts * 1000).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : '—')

export function InviteCard({ active, mode, outbox, invitations, onChange }: { active: boolean; mode: 'local' | 'smtp'; outbox: string | null; invitations: Invitation[]; onChange: () => void }) {
  const [correo, setCorreo] = useState('')
  const [perm, setPerm] = useState({ procesos: true, seguridad: false, estadisticas: true })
  const [horas, setHoras] = useState(2)
  const [validez, setValidez] = useState(60)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [result, setResult] = useState<InviteResult | null>(null)
  const [copied, setCopied] = useState(false)

  const submit = async (ev: FormEvent) => {
    ev.preventDefault()
    setBusy(true)
    setErr(null)
    setResult(null)
    try {
      const r = await apiPost<InviteResult>('/api/remote/invites', { correo, ...perm, horas, validez_min: validez })
      setResult(r)
      setCorreo('')
      onChange()
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  const revoke = async (id: string) => {
    setErr(null)
    try {
      await apiDelete(`/api/remote/invites/${id}`)
      onChange()
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      /* portapapeles no disponible */
    }
  }

  return (
    <Card title="Invitar por correo">
      <p className="mb-4 text-sm leading-relaxed text-muted">
        Envíe a una persona un enlace de <b className="text-fg">un solo uso</b>. Al abrirlo debe escribir su correo para confirmar que es ella, y solo verá lo que usted marque aquí, en modo de
        solo lectura. Funciona en la misma red que esta PC.
      </p>
      {!active ? (
        <Notice tone="info">Active el acceso remoto para poder invitar: el enlace apunta a la dirección local de esta PC.</Notice>
      ) : (
        <form onSubmit={submit} className="flex flex-col gap-4">
          <label className="text-xs text-muted">
            Correo de la persona invitada
            <input
              type="email"
              required
              maxLength={254}
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              placeholder="nombre@ejemplo.com"
              className="mt-1 w-full rounded-xl border border-line bg-surface-2 px-3 py-2 text-sm text-fg"
            />
          </label>
          <fieldset>
            <legend className="mb-2 text-xs text-muted">Además de CPU, RAM, discos y red, podrá ver:</legend>
            <div className="flex flex-wrap gap-2">
              {(Object.keys(PERM_LABEL) as (keyof typeof PERM_LABEL)[]).map((k) => (
                <label key={k} className={`flex cursor-pointer items-center gap-2 rounded-xl border px-3 py-1.5 text-sm ${perm[k] ? 'border-accent/60 bg-accent-soft text-fg' : 'border-line text-muted'}`}>
                  <input type="checkbox" className="accent-accent" checked={perm[k]} onChange={(e) => setPerm({ ...perm, [k]: e.target.checked })} />
                  {PERM_LABEL[k]}
                </label>
              ))}
            </div>
          </fieldset>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-xs text-muted">
              El enlace caduca si no se abre en
              <select value={validez} onChange={(e) => setValidez(Number(e.target.value))} className="mt-1 w-full rounded-xl border border-line bg-surface-2 px-3 py-2 text-sm text-fg">
                <option value={15}>15 minutos</option>
                <option value={60}>1 hora</option>
                <option value={240}>4 horas</option>
                <option value={1440}>24 horas</option>
              </select>
            </label>
            <label className="text-xs text-muted">
              Duración del acceso una vez abierto
              <select value={horas} onChange={(e) => setHoras(Number(e.target.value))} className="mt-1 w-full rounded-xl border border-line bg-surface-2 px-3 py-2 text-sm text-fg">
                <option value={1}>1 hora</option>
                <option value={2}>2 horas</option>
                <option value={8}>8 horas</option>
                <option value={12}>12 horas</option>
              </select>
            </label>
          </div>
          <div>
            <Button type="submit" tone="primary" icon={<Send size={15} />} disabled={busy || !correo.trim()}>
              Enviar invitación
            </Button>
          </div>
        </form>
      )}

      {mode === 'local' && (
        <p className="mt-4 text-xs leading-relaxed text-muted">
          Modo de prueba: el correo no sale de este equipo. Se guarda como archivo .eml en <span className="break-all font-mono">{outbox}</span> para que lo abra con su programa de correo y lo
          reenvíe, o copie el enlace.
        </p>
      )}
      {err && (
        <div className="mt-3">
          <Notice tone="danger">{err}</Notice>
        </div>
      )}
      {result && (
        <div className="mt-3">
          <Notice tone="ok">
            <span className="flex flex-col gap-2">
              <span>
                <Mail size={14} className="mr-1 inline" />
                Invitación para <b>{result.invitacion.correo}</b> {result.envio.modo === 'local' ? 'guardada en la bandeja de salida local' : 'enviada'}. Caduca: {when(result.invitacion.caduca)}
              </span>
              {result.enlace && (
                <span className="flex items-center gap-2">
                  <span className="min-w-0 flex-1 truncate font-mono text-xs">{result.enlace.replace(/#invitacion=.*/, '#invitacion=…')}</span>
                  <Button icon={copied ? <Check size={14} /> : <Copy size={14} />} onClick={() => copy(result.enlace ?? '')}>
                    {copied ? 'Copiado' : 'Copiar enlace'}
                  </Button>
                </span>
              )}
            </span>
          </Notice>
        </div>
      )}

      {invitations.length > 0 && (
        <ul className="mt-5 flex flex-col divide-y divide-line border-t border-line">
          {invitations.map((i) => (
            <li key={i.id} className="flex flex-wrap items-center gap-3 py-3">
              <Mail size={17} className="text-muted" />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 text-sm font-medium text-fg">
                  <span className="truncate">{i.correo}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[11px] ${ESTADO[i.estado].cls}`}>{ESTADO[i.estado].text}</span>
                </div>
                <div className="text-xs text-muted">
                  {(Object.keys(PERM_LABEL) as (keyof typeof PERM_LABEL)[])
                    .filter((k) => i.permisos[k])
                    .map((k) => PERM_LABEL[k])
                    .join(', ') || 'Solo rendimiento'}{' '}
                  · {i.horas} h · {i.usada ? `usada: ${when(i.usada)}` : `caduca: ${when(i.caduca)}`}
                </div>
              </div>
              {(i.estado === 'pendiente' || i.sesion_activa) && (
                <Button tone="danger" onClick={() => revoke(i.id)}>
                  {i.sesion_activa ? 'Quitar acceso' : 'Anular'}
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
