import { ArrowLeft, Check, Clock, Cpu, HardDrive, Laptop, Link2, MemoryStick, Plus, Trash2, Unplug, WifiOff } from 'lucide-react'
import { useState } from 'react'
import { Confirm } from '../components/Confirm'
import { Button, Notice } from '../components/controls'
import { TimeChart } from '../components/TimeChart'
import { Bar, Card } from '../components/ui'
import { api, apiDelete, apiPost } from '../lib/api'
import { bytes, duration, levelFor, pct } from '../lib/format'
import { useMetrics } from '../lib/metrics'
import { usePolling } from '../lib/usePolling'

interface Device {
  id: string
  nombre: string
  direccion: string
  huella_corta: string
  conectado: boolean
  ultima_lectura: number | null
  medido_en: number | null
  error: string | null
  so: string | null
  cpu: number | null
  ram: number | null
  ram_usada: number | null
  ram_total: number | null
  disco: { unidad: string; porcentaje: number; libre: number } | null
  tiempo_encendido_s: number | null
  alertas: string[]
}

interface Proc {
  nombre: string
  instancias: number
  ram_mb: number
  cpu_prom_1min_pct: number
}

const TONE = { ok: 'var(--accent)', warn: 'var(--warn)', danger: 'var(--danger)' }
const hora = (ts: number | null) => (ts ? new Date(ts * 1000).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'medium' }) : 'nunca')

function Meter({ icon, label, value, detail, stale }: { icon: React.ReactNode; label: string; value: number | null; detail?: string; stale: boolean }) {
  return (
    <div className={stale ? 'opacity-45' : ''}>
      <div className="flex items-center justify-between text-xs text-muted">
        <span className="flex items-center gap-1.5">
          {icon}
          {label}
        </span>
        <span className="tabular font-semibold text-fg">{pct(value)}</span>
      </div>
      <div className="mt-1.5">
        <Bar value={value ?? 0} tone={TONE[levelFor(value)]} />
      </div>
      {detail && <div className="mt-1 text-[11.5px] text-faint">{detail}</div>}
    </div>
  )
}

function DeviceCard({ d, onOpen }: { d: Device; onOpen: () => void }) {
  const stale = !d.conectado
  return (
    <button type="button" onClick={onOpen} className="card animate-rise flex flex-col gap-3 p-4 text-left transition-colors hover:border-accent/50">
      <div className="flex items-start gap-3">
        <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${d.conectado ? 'bg-accent-soft text-accent' : 'bg-surface-3 text-faint'}`}>
          <Laptop size={20} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="truncate font-medium text-fg">{d.nombre}</div>
          <div className="truncate text-xs text-muted">{d.so ?? '—'} · {d.direccion}</div>
        </div>
        <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-medium ${d.conectado ? 'bg-ok-soft text-ok' : 'bg-danger-soft text-danger'}`}>{d.conectado ? 'Conectado' : 'Desconectado'}</span>
      </div>
      <Meter icon={<Cpu size={13} />} label="CPU" value={d.cpu} stale={stale} />
      <Meter icon={<MemoryStick size={13} />} label="RAM" value={d.ram} detail={d.ram_usada != null ? `${bytes(d.ram_usada)} de ${bytes(d.ram_total)}` : undefined} stale={stale} />
      <Meter icon={<HardDrive size={13} />} label={`Disco ${d.disco?.unidad ?? ''}`} value={d.disco?.porcentaje ?? null} detail={d.disco ? `${bytes(d.disco.libre)} libres` : undefined} stale={stale} />
      <div className="flex items-center justify-between text-[11.5px] text-faint">
        <span className="flex items-center gap-1">
          <Clock size={12} /> {d.tiempo_encendido_s != null ? `Encendida ${duration(d.tiempo_encendido_s)}` : '—'}
        </span>
        <span>{d.conectado ? 'En vivo' : `Última lectura: ${hora(d.ultima_lectura)}`}</span>
      </div>
      {stale && <div className="text-[11.5px] text-danger">Cifras de la última lectura, no actuales.{d.error ? ` ${d.error}` : ''}</div>}
      {d.alertas.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {d.alertas.map((a) => (
            <span key={a} className="rounded-full bg-warn-soft px-2 py-0.5 text-[11px] text-warn">
              {a}
            </span>
          ))}
        </div>
      )}
    </button>
  )
}

function PairForm({ onDone }: { onDone: () => void }) {
  const [direccion, setDireccion] = useState('')
  const [puerto, setPuerto] = useState(8765)
  const [codigo, setCodigo] = useState('')
  const [pending, setPending] = useState<{ id: string; frase: string; equipo: string; huella_corta: string } | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setMsg(null)
    try {
      const p = await apiPost<{ id: string; frase: string; equipo: string; huella_corta: string }>('/api/fleet/pair', { direccion, puerto, codigo })
      setPending(p)
      // Espera a que el propietario de la otra PC autorice la vinculación.
      for (let i = 0; i < 150; i++) {
        await new Promise((r) => setTimeout(r, 2000))
        const s = await api<{ estado: string }>(`/api/fleet/pair/${p.id}`)
        if (s.estado === 'autorizada') {
          onDone()
          return
        }
        if (s.estado === 'rechazada' || s.estado === 'caducada') {
          setMsg(s.estado === 'rechazada' ? 'La otra PC rechazó la solicitud.' : 'La solicitud caducó.')
          setPending(null)
          return
        }
      }
    } catch (err) {
      setMsg(err instanceof Error ? err.message : String(err))
      setPending(null)
    } finally {
      setBusy(false)
    }
  }

  if (pending)
    return (
      <Card title="Esperando autorización en la otra PC">
        <p className="text-sm text-muted">
          En <b className="text-fg">{pending.equipo}</b> abra ScriptLens → Acceso remoto y autorice la solicitud solo si muestra esta frase:
        </p>
        <div className="my-4 text-center font-display text-4xl font-semibold tracking-widest text-accent">{pending.frase}</div>
        <p className="text-xs text-muted">Huella del certificado recibido: {pending.huella_corta}. Debe coincidir con la que muestra la otra PC.</p>
      </Card>
    )

  return (
    <Card title="Vincular computadora">
      <ol className="mb-4 list-decimal space-y-1 pl-5 text-sm text-muted">
        <li>En la otra PC instale ScriptLens, abra «Acceso remoto» y pulse «Activar».</li>
        <li>Copie aquí la dirección IP y el código de 6 cifras que aparecen allí.</li>
        <li>Autorice la solicitud en esa PC cuando vea la misma frase.</li>
      </ol>
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-[1fr_110px_150px_auto] sm:items-end">
        <label className="text-xs text-muted">
          Dirección IP
          <input value={direccion} onChange={(e) => setDireccion(e.target.value)} required placeholder="192.168.1.25" className="mt-1 w-full rounded-xl border border-line bg-surface-2 px-3 py-2 text-sm text-fg" />
        </label>
        <label className="text-xs text-muted">
          Puerto
          <input type="number" value={puerto} onChange={(e) => setPuerto(Number(e.target.value))} min={1024} max={65535} className="mt-1 w-full rounded-xl border border-line bg-surface-2 px-3 py-2 text-sm text-fg" />
        </label>
        <label className="text-xs text-muted">
          Código
          <input value={codigo} onChange={(e) => setCodigo(e.target.value.replace(/\D/g, '').slice(0, 6))} required inputMode="numeric" placeholder="000000" className="tabular mt-1 w-full rounded-xl border border-line bg-surface-2 px-3 py-2 text-sm tracking-[0.25em] text-fg" />
        </label>
        <Button type="submit" tone="primary" icon={<Link2 size={15} />} disabled={busy || codigo.length !== 6}>
          Vincular
        </Button>
      </form>
      {msg && (
        <div className="mt-3">
          <Notice tone="danger">{msg}</Notice>
        </div>
      )}
    </Card>
  )
}

function Detail({ id, onBack }: { id: string; onBack: () => void }) {
  const dev = usePolling(() => api<Device>(`/api/fleet/devices/${id}`), 3000)
  const hist = usePolling(() => api<{ muestras: { ts: number; cpu: number | null; ram: number | null }[] }>(`/api/fleet/devices/${id}/history`, { hours: 24 }), 20000)
  const [by, setBy] = useState<'cpu' | 'memory'>('cpu')
  const procs = usePolling(() => api<{ programas: Proc[]; medido_en: number }>(`/api/fleet/devices/${id}/processes`, { by }), 6000, [by])
  const [confirm, setConfirm] = useState(false)
  const d = dev.data
  if (!d) return <Card>Cargando…</Card>
  const m = hist.data?.muestras ?? []

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3">
        <Button icon={<ArrowLeft size={15} />} onClick={onBack}>
          Mis computadoras
        </Button>
        <div className="min-w-0 flex-1">
          <h2 className="truncate font-display text-xl font-semibold">{d.nombre}</h2>
          <div className="text-xs text-muted">
            Otra PC · {d.direccion} · {d.so ?? '—'} · huella {d.huella_corta}
          </div>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${d.conectado ? 'bg-ok-soft text-ok' : 'bg-danger-soft text-danger'}`}>{d.conectado ? 'Conectado' : `Desconectado · última lectura ${hora(d.ultima_lectura)}`}</span>
      </div>
      <Notice tone={d.conectado ? 'info' : 'warn'}>
        Está viendo <b>{d.nombre}</b>, no esta PC. {d.conectado ? 'Los datos se actualizan cada 5 segundos.' : 'No responde: las cifras son de la última lectura y no se presentan como actuales.'}
      </Notice>
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <Meter icon={<Cpu size={14} />} label="Procesador" value={d.cpu} stale={!d.conectado} />
        </Card>
        <Card>
          <Meter icon={<MemoryStick size={14} />} label="Memoria RAM" value={d.ram} detail={d.ram_usada != null ? `${bytes(d.ram_usada)} de ${bytes(d.ram_total)}` : undefined} stale={!d.conectado} />
        </Card>
        <Card>
          <Meter icon={<HardDrive size={14} />} label={`Disco ${d.disco?.unidad ?? ''}`} value={d.disco?.porcentaje ?? null} detail={d.disco ? `${bytes(d.disco.libre)} libres` : undefined} stale={!d.conectado} />
        </Card>
      </div>
      <Card title="Historial de las últimas 24 horas (guardado en esta consola)">
        {m.length < 2 ? (
          <p className="text-sm text-muted">Todavía no hay suficientes lecturas guardadas.</p>
        ) : (
          <TimeChart
            times={m.map((x) => x.ts)}
            series={[
              { key: 'cpu', label: 'CPU', color: 'var(--chart-cpu)', values: m.map((x) => x.cpu) },
              { key: 'ram', label: 'RAM', color: 'var(--chart-ram)', values: m.map((x) => x.ram) },
            ]}
          />
        )}
      </Card>
      <Card
        title="Programas con mayor consumo"
        action={
          <div className="flex rounded-xl border border-line bg-surface-2 p-0.5 text-xs">
            {(['cpu', 'memory'] as const).map((k) => (
              <button key={k} type="button" onClick={() => setBy(k)} className={`rounded-[10px] px-3 py-1 ${by === k ? 'bg-accent text-white' : 'text-muted'}`}>
                {k === 'cpu' ? 'CPU' : 'RAM'}
              </button>
            ))}
          </div>
        }
      >
        {procs.error ? (
          <p className="text-sm text-muted">{procs.error}</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-faint">
                <th className="py-1.5 font-medium">Programa</th>
                <th className="py-1.5 text-right font-medium">CPU (1 min)</th>
                <th className="py-1.5 text-right font-medium">RAM</th>
              </tr>
            </thead>
            <tbody className="tabular">
              {(procs.data?.programas ?? []).map((p) => (
                <tr key={p.nombre} className="border-t border-line">
                  <td className="py-1.5">
                    {p.nombre}
                    {p.instancias > 1 && <span className="text-faint"> ×{p.instancias}</span>}
                  </td>
                  <td className="py-1.5 text-right">{p.cpu_prom_1min_pct.toFixed(1)} %</td>
                  <td className="py-1.5 text-right">{p.ram_mb.toFixed(0)} MB</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="mt-2 text-xs text-faint">Vista de solo lectura: desde aquí no se puede cerrar programas en la otra PC.</p>
      </Card>
      <div>
        <Button tone="danger" icon={<Unplug size={15} />} onClick={() => setConfirm(true)}>
          Desvincular esta computadora
        </Button>
      </div>
      {confirm && (
        <Confirm
          title={`¿Desvincular ${d.nombre}?`}
          confirmLabel="Desvincular"
          danger
          onCancel={() => setConfirm(false)}
          onConfirm={async () => {
            await apiDelete(`/api/fleet/devices/${id}`)
            setConfirm(false)
            onBack()
          }}
        >
          <p>Se borrará su historial de esta consola y la otra PC dejará de aceptar consultas de esta consola.</p>
        </Confirm>
      )}
    </div>
  )
}

export function FleetPage() {
  const [tick, setTick] = useState(0)
  const list = usePolling(() => api<{ equipos: Device[]; esta_pc: { nombre: string } }>('/api/fleet/devices'), 3000, [tick])
  const { summary, info } = useMetrics()
  const [open, setOpen] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)

  if (open) return <Detail id={open} onBack={() => setOpen(null)} />
  const devs = list.data?.equipos ?? []
  const cur = summary?.current
  const online = devs.filter((d) => d.conectado).length

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5">
      <Card>
        <div className="flex flex-wrap items-center gap-4">
          <div className="min-w-0 flex-1">
            <h2 className="font-display text-xl font-semibold">Supervise varias computadoras desde aquí</h2>
            <p className="mt-1 text-sm text-muted">
              Vincule otras PC que tengan ScriptLens con el acceso remoto activado. Cada una decide si participa y puede revocar el acceso cuando quiera. {devs.length > 0 && `${online} de ${devs.length} conectadas.`}
            </p>
          </div>
          <Button tone="primary" icon={adding ? <Check size={15} /> : <Plus size={15} />} onClick={() => setAdding(!adding)}>
            {adding ? 'Cerrar' : 'Vincular computadora'}
          </Button>
        </div>
      </Card>
      {adding && (
        <PairForm
          onDone={() => {
            setAdding(false)
            setTick((t) => t + 1)
          }}
        />
      )}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <div className="card flex flex-col gap-3 border-accent/40 p-4">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-accent text-white">
              <Laptop size={20} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate font-medium text-fg">{list.data?.esta_pc.nombre ?? 'Esta PC'}</div>
              <div className="text-xs text-muted">Esta PC (principal) · {info?.os}</div>
            </div>
          </div>
          <Meter icon={<Cpu size={13} />} label="CPU" value={cur?.cpu_percent ?? null} stale={false} />
          <Meter icon={<MemoryStick size={13} />} label="RAM" value={cur?.mem_percent ?? null} stale={false} />
        </div>
        {devs.map((d) => (
          <DeviceCard key={d.id} d={d} onOpen={() => setOpen(d.id)} />
        ))}
      </div>
      {devs.length === 0 && !adding && (
        <Card>
          <div className="flex items-center gap-3 text-sm text-muted">
            <WifiOff size={18} /> Aún no hay otras computadoras vinculadas. Pulse «Vincular computadora».
          </div>
        </Card>
      )}
      {devs.length > 1 && (
        <Card title="Comparación entre computadoras">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-faint">
                  <th className="py-1.5 font-medium">Equipo</th>
                  <th className="py-1.5 font-medium">Estado</th>
                  <th className="py-1.5 text-right font-medium">CPU</th>
                  <th className="py-1.5 text-right font-medium">RAM</th>
                  <th className="py-1.5 text-right font-medium">Disco</th>
                  <th className="py-1.5 text-right font-medium">Encendida</th>
                </tr>
              </thead>
              <tbody className="tabular">
                {devs.map((d) => (
                  <tr key={d.id} className={`border-t border-line ${d.conectado ? '' : 'text-faint'}`}>
                    <td className="py-1.5">{d.nombre}</td>
                    <td className="py-1.5">{d.conectado ? 'Conectado' : `Sin conexión desde ${hora(d.ultima_lectura)}`}</td>
                    <td className="py-1.5 text-right">{pct(d.cpu)}</td>
                    <td className="py-1.5 text-right">{pct(d.ram)}</td>
                    <td className="py-1.5 text-right">{d.disco ? pct(d.disco.porcentaje) : '—'}</td>
                    <td className="py-1.5 text-right">{d.tiempo_encendido_s != null ? duration(d.tiempo_encendido_s) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
      <p className="flex items-center gap-1.5 text-xs text-faint">
        <Trash2 size={12} /> El historial de cada equipo se guarda solo en esta consola durante 7 días.
      </p>
    </div>
  )
}
