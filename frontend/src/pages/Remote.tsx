import { Check, Copy, Laptop, MonitorSmartphone, Pause, Play, Power, RefreshCcw, ShieldCheck, Smartphone, Wifi, WifiOff, X } from 'lucide-react'
import { useState } from 'react'
import { Confirm } from '../components/Confirm'
import { Button, Notice, Row, Toggle } from '../components/controls'
import { Card } from '../components/ui'
import { api, apiDelete, apiPost } from '../lib/api'
import { usePolling } from '../lib/usePolling'
import { type Invitation, InviteCard } from './RemoteInvite'

interface RemoteStatus {
  estado: 'apagado' | 'activo' | 'pausado'
  error: string | null
  equipo: string
  puerto: number
  urls: string[]
  interfaces: { interfaz: string; ip: string; virtual: boolean; enlace_local: boolean }[]
  hay_red_local: boolean
  huella: string | null
  huella_corta: string | null
  codigo: { codigo: string | null; caduca_en: number }
  solicitudes: { id: string; nombre: string; tipo: 'navegador' | 'consola'; ip: string; frase: string; creado: number }[]
  sesiones: { id: string; nombre: string; tipo: 'navegador' | 'consola'; ip: string; created_at: number; expires_at: number; last_seen: number | null; last_ip: string | null; activa_ahora: boolean; correo: string | null }[]
  comparte: { procesos: boolean; seguridad: boolean; estadisticas: boolean }
  invitaciones: Invitation[]
  correo: { modo: 'local' | 'smtp'; error: string | null; salida: string | null }
}

const STATE_LABEL = { apagado: 'Apagado', activo: 'Activo', pausado: 'En pausa' }
const when = (ts: number | null) => (ts ? new Date(ts * 1000).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : 'Nunca')

export function RemotePage() {
  const [tick, setTick] = useState(0)
  const st = usePolling(() => api<RemoteStatus>('/api/remote/status'), 2000, [tick])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [confirmOff, setConfirmOff] = useState(false)
  const [copied, setCopied] = useState<string | null>(null)
  const s = st.data
  const refresh = () => setTick((t) => t + 1)

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setErr(null)
    try {
      await fn()
      refresh()
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(text)
      window.setTimeout(() => setCopied(null), 1500)
    } catch {
      /* portapapeles no disponible */
    }
  }

  if (!s) return <Card>Cargando el estado del acceso remoto…</Card>
  const on = s.estado === 'activo'

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5">
      <Card>
        <div className="flex flex-wrap items-start gap-4">
          <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-accent-soft text-accent">
            <MonitorSmartphone size={24} />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="font-display text-xl font-semibold">Ver mi PC desde otro dispositivo</h2>
            <p className="mt-1 text-sm leading-relaxed text-muted">
              Permite abrir ScriptLens en un celular, una tablet u otra laptop conectados a la <b className="text-fg">misma red</b> y ver en vivo el procesador, la memoria, los discos y los
              programas de <b className="text-fg">{s.equipo}</b>. Es solo de consulta: desde el otro dispositivo no se puede cerrar programas ni cambiar nada.
            </p>
          </div>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${on ? 'bg-ok-soft text-ok' : s.estado === 'pausado' ? 'bg-warn-soft text-warn' : 'bg-surface-3 text-muted'}`}>{STATE_LABEL[s.estado]}</span>
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          {s.estado === 'apagado' && (
            <Button tone="primary" icon={<Power size={16} />} disabled={busy} onClick={() => run(() => apiPost('/api/remote/enable'))}>
              Activar acceso remoto
            </Button>
          )}
          {s.estado === 'pausado' && (
            <Button tone="primary" icon={<Play size={16} />} disabled={busy} onClick={() => run(() => apiPost('/api/remote/enable'))}>
              Reanudar
            </Button>
          )}
          {on && (
            <Button icon={<Pause size={16} />} disabled={busy} onClick={() => run(() => apiPost('/api/remote/pause'))}>
              Pausar (conserva los dispositivos)
            </Button>
          )}
          {s.estado !== 'apagado' && (
            <Button tone="danger" icon={<Power size={16} />} disabled={busy} onClick={() => setConfirmOff(true)}>
              Desactivar y desconectar todo
            </Button>
          )}
        </div>
        {!s.hay_red_local && (
          <div className="mt-4">
            <Notice tone="warn">
              <WifiOff size={15} className="mr-1.5 inline" /> No se detecta una red WiFi o de cable. Conecte la PC a la misma red que el otro dispositivo o active el punto de acceso (hotspot) del
              celular.
            </Notice>
          </div>
        )}
        {(err || s.error) && (
          <div className="mt-4">
            <Notice tone="danger">{err || s.error}</Notice>
          </div>
        )}
      </Card>

      {on && (
        <div className="grid gap-5 md:grid-cols-2">
          <Card title="1. Abra esta dirección en el otro dispositivo">
            <div className="flex flex-col gap-2">
              {s.urls.map((u) => (
                <div key={u} className="flex items-center gap-2 rounded-xl border border-line bg-surface-2 px-3 py-2">
                  <Wifi size={15} className="shrink-0 text-accent" />
                  <span className="tabular min-w-0 flex-1 break-all font-mono text-[15px] font-semibold text-fg">{u}</span>
                  <button type="button" onClick={() => copy(u)} className="text-muted hover:text-fg" aria-label="Copiar dirección">
                    {copied === u ? <Check size={16} /> : <Copy size={16} />}
                  </button>
                </div>
              ))}
            </div>
            <p className="mt-3 text-[13px] leading-relaxed text-muted">
              El navegador mostrará un aviso de certificado porque ScriptLens usa un certificado propio de este equipo. Compruebe que la huella coincida y continúe.
            </p>
            <details className="mt-2 text-[13px] text-muted">
              <summary className="cursor-pointer text-fg">Huella del certificado: {s.huella_corta}</summary>
              <p className="mt-1 break-all font-mono text-xs">{s.huella}</p>
            </details>
          </Card>

          <Card title="2. Escriba este código en el otro dispositivo">
            {s.codigo.codigo ? (
              <>
                <div className="tabular font-display text-5xl font-semibold tracking-[0.3em] text-fg" aria-label={`Código ${s.codigo.codigo.split('').join(' ')}`}>
                  {s.codigo.codigo}
                </div>
                <p className="mt-2 text-sm text-muted">Caduca en {Math.floor(s.codigo.caduca_en / 60)}:{String(s.codigo.caduca_en % 60).padStart(2, '0')} · sirve para un solo dispositivo</p>
              </>
            ) : (
              <p className="text-sm text-muted">No hay un código vigente.</p>
            )}
            <div className="mt-4">
              <Button icon={<RefreshCcw size={15} />} disabled={busy} onClick={() => run(() => apiPost('/api/remote/code'))}>
                Generar otro código
              </Button>
            </div>
          </Card>
        </div>
      )}

      {on && s.solicitudes.length > 0 && (
        <Card title="3. Autorice la solicitud">
          <div className="flex flex-col gap-3">
            {s.solicitudes.map((r) => (
              <div key={r.id} className="flex flex-wrap items-center gap-4 rounded-xl border border-accent/40 bg-accent-soft px-4 py-3">
                {r.tipo === 'consola' ? <Laptop size={22} className="text-accent" /> : <Smartphone size={22} className="text-accent" />}
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-fg">{r.nombre}</div>
                  <div className="text-xs text-muted">
                    {r.tipo === 'consola' ? 'Consola ScriptLens (Mis computadoras)' : 'Navegador'} · desde {r.ip}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-[11px] uppercase tracking-wide text-faint">Frase</div>
                  <div className="font-display text-2xl font-semibold tracking-widest text-accent">{r.frase}</div>
                </div>
                <div className="flex gap-2">
                  <Button tone="primary" icon={<Check size={15} />} disabled={busy} onClick={() => run(() => apiPost(`/api/remote/requests/${r.id}`, { autorizar: true }))}>
                    Autorizar
                  </Button>
                  <Button icon={<X size={15} />} disabled={busy} onClick={() => run(() => apiPost(`/api/remote/requests/${r.id}`, { autorizar: false }))}>
                    Rechazar
                  </Button>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[13px] text-muted">Autorice solo si la frase coincide con la que muestra el otro dispositivo.</p>
        </Card>
      )}

      <InviteCard active={on} mode={s.correo.modo} outbox={s.correo.salida} invitations={s.invitaciones} onChange={refresh} />

      <Card title="Dispositivos vinculados">
        {s.sesiones.length === 0 ? (
          <p className="text-sm text-muted">Ningún dispositivo tiene acceso.</p>
        ) : (
          <ul className="flex flex-col divide-y divide-line">
            {s.sesiones.map((x) => (
              <li key={x.id} className="flex flex-wrap items-center gap-3 py-3">
                {x.tipo === 'consola' ? <Laptop size={18} className="text-muted" /> : <Smartphone size={18} className="text-muted" />}
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-fg">
                    {x.nombre} {x.correo && <span className="ml-1 rounded-full bg-accent-soft px-2 py-0.5 text-[11px] text-accent">por invitación</span>}
                    {x.activa_ahora && <span className="ml-1 rounded-full bg-ok-soft px-2 py-0.5 text-[11px] text-ok">consultando ahora</span>}
                  </div>
                  <div className="text-xs text-muted">
                    {x.last_ip ?? x.ip} · última consulta: {when(x.last_seen)} · caduca: {when(x.expires_at)}
                  </div>
                </div>
                <Button tone="danger" disabled={busy} onClick={() => run(() => apiDelete(`/api/remote/sessions/${x.id}`))}>
                  Revocar
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card title="Qué puede ver el otro dispositivo">
        <Row label="Rendimiento y equipo" hint="CPU, RAM, discos, red, tiempo encendido y sistema operativo. Siempre incluido.">
          <ShieldCheck size={18} className="text-ok" />
        </Row>
        <Row label="Programas con mayor consumo" hint="Nombre, CPU y RAM agrupados por programa. Nunca rutas, usuarios ni líneas de comando.">
          <Toggle label="Compartir programas" checked={s.comparte.procesos} onChange={(v) => run(() => apiPost('/api/remote/sharing', { ...s.comparte, procesos: v }))} />
        </Row>
        <Row label="Resumen de seguridad" hint="Estado de Defender y del firewall de la última revisión hecha en esta PC.">
          <Toggle label="Compartir seguridad" checked={s.comparte.seguridad} onChange={(v) => run(() => apiPost('/api/remote/sharing', { ...s.comparte, seguridad: v }))} />
        </Row>
        <Row label="Estadísticas resumidas" hint="Tiempo encendido, uso activo y promedios del día.">
          <Toggle label="Compartir estadísticas" checked={s.comparte.estadisticas} onChange={(v) => run(() => apiPost('/api/remote/sharing', { ...s.comparte, estadisticas: v }))} />
        </Row>
      </Card>

      <Card title="Si no logra conectarse">
        <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-muted">
          <li>Ambos dispositivos deben estar en la misma red WiFi o en el hotspot del celular.</li>
          <li>
            Si Windows pregunta si permite a ScriptLens comunicarse, marque solo <b className="text-fg">Redes privadas</b>. ScriptLens no modifica el firewall por su cuenta.
          </li>
          <li>Muchas redes universitarias o públicas aíslan a los dispositivos entre sí: use el punto de acceso (hotspot) de un celular.</li>
          <li>Escriba la dirección completa, empezando por https://, incluido el número de puerto ({s.puerto}).</li>
        </ul>
      </Card>

      {confirmOff && (
        <Confirm
          title="¿Desactivar el acceso remoto?"
          confirmLabel="Desactivar"
          danger
          busy={busy}
          onCancel={() => setConfirmOff(false)}
          onConfirm={() => run(() => apiPost('/api/remote/disable')).then(() => setConfirmOff(false))}
        >
          <p>Se cerrará el servidor de red y se revocará el acceso de todos los dispositivos vinculados ({s.sesiones.length}). Tendrán que vincularse de nuevo.</p>
        </Confirm>
      )}
    </div>
  )
}
