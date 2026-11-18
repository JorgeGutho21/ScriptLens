import { Activity, AlertTriangle, Clock, Download, MonitorCheck, Power, Timer, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Confirm } from '../components/Confirm'
import { Button, Notice, Row, Toggle } from '../components/controls'
import { TimeChart } from '../components/TimeChart'
import { Card, Stat } from '../components/ui'
import { api, apiDelete, apiPost } from '../lib/api'
import { bytes, duration, pct } from '../lib/format'
import { usePolling } from '../lib/usePolling'

type Period = 'dia' | 'semana' | 'mes'

interface Summary {
  periodo: Period
  ajustes: { activadas: boolean; retencion_dias: number; aplicaciones: boolean }
  tiempos: { desde_ultimo_arranque_s: number; ultimo_arranque: number; registrado_s: number; sesion_s: number; activo_s: number; inactivo_s: number }
  promedios: { cpu: number | null; ram: number | null }
  serie: { ts: number; minutos_registrados: number; cpu_prom: number | null; ram_prom: number | null; red_enviados: number; red_recibidos: number; activo_s: number }[]
  sesiones: { inicio: number; fin: number; activo_s: number }[]
  horario: number[][]
  procesos_cpu: { name: string; cpu_prom: number; ram_max: number; minutos: number }[]
  procesos_ram: { name: string; cpu_prom: number; ram_max: number; minutos: number }[]
  aplicaciones: { app: string; segundos: number }[]
  alertas: { created_at: number; kind: string; detail: string }[]
  arranques: { boot_time: number; source: string; shutdown_time: number | null }[]
  comparacion_dias: { dia: number; minutos_registrados: number; cpu_prom: number | null; ram_prom: number | null; activo_s: number; red_bytes: number }[]
}

const DAYS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
const fmt = (ts: number, o: Intl.DateTimeFormatOptions) => new Date(ts * 1000).toLocaleString('es-CO', o)
const SOURCE: Record<string, string> = { inicio: 'Encendido', reanudacion: 'Reanudación', arranque_actual: 'Arranque actual' }

export function StatsPage() {
  const [period, setPeriod] = useState<Period>('dia')
  const [tick, setTick] = useState(0)
  const q = usePolling(() => api<Summary>('/api/stats/summary', { period }), 60000, [period, tick])
  const [msg, setMsg] = useState<string | null>(null)
  const [askDelete, setAskDelete] = useState(false)
  const [askApps, setAskApps] = useState(false)
  const s = q.data
  const refresh = () => setTick((t) => t + 1)

  const save = async (patch: Partial<Summary['ajustes']>) => {
    if (!s) return
    await apiPost('/api/stats/settings', { ...s.ajustes, ...patch })
    refresh()
  }
  const exportAs = async (formato: 'csv' | 'html') => {
    const r = await apiPost<{ archivo: string; ruta: string }>('/api/stats/export', { formato, periodo: period })
    setMsg(`Informe guardado en ${r.ruta}`)
    try {
      await apiPost(`/api/reports/open/${encodeURIComponent(r.archivo)}`)
    } catch {
      /* se puede abrir desde Informes */
    }
  }

  if (!s) return <Card>{q.error ? `No se pudieron cargar las estadísticas: ${q.error}` : 'Cargando estadísticas…'}</Card>
  const t = s.tiempos
  const maxCell = Math.max(1, ...s.horario.flat())

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3">
        <div role="radiogroup" aria-label="Periodo" className="flex rounded-xl border border-line bg-surface-2 p-0.5 text-sm">
          {(['dia', 'semana', 'mes'] as const).map((p) => (
            <button key={p} role="radio" aria-checked={period === p} type="button" onClick={() => setPeriod(p)} className={`rounded-[10px] px-4 py-1.5 ${period === p ? 'bg-accent text-white' : 'text-muted hover:text-fg'}`}>
              {{ dia: 'Hoy', semana: '7 días', mes: '30 días' }[p]}
            </button>
          ))}
        </div>
        <div className="ml-auto flex gap-2">
          <Button icon={<Download size={15} />} onClick={() => exportAs('html')}>
            Informe HTML
          </Button>
          <Button icon={<Download size={15} />} onClick={() => exportAs('csv')}>
            CSV (Excel)
          </Button>
        </div>
      </div>
      {msg && <Notice tone="ok">{msg}</Notice>}
      {!s.ajustes.activadas && <Notice tone="warn">Las estadísticas están en pausa: no se registran datos nuevos.</Notice>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat icon={<Power size={18} />} label="Desde el último arranque" value={duration(t.desde_ultimo_arranque_s)} hint={`Windows arrancó el ${fmt(t.ultimo_arranque, { dateStyle: 'short', timeStyle: 'short' })}`} />
        <Stat icon={<MonitorCheck size={18} />} label="Sesión registrada" value={duration(t.sesion_s)} hint="Sesión abierta mientras ScriptLens medía" />
        <Stat icon={<Activity size={18} />} label="Uso activo" value={duration(t.activo_s)} hint={`Inactivo: ${duration(t.inactivo_s)}`} />
        <Stat icon={<Timer size={18} />} label="Tiempo medido" value={duration(t.registrado_s)} hint={`CPU prom. ${pct(s.promedios.cpu)} · RAM prom. ${pct(s.promedios.ram)}`} />
      </div>
      <p className="-mt-2 text-xs text-faint">
        Son tres tiempos distintos: lo que Windows cuenta desde que arrancó (puede incluir suspensión), el tiempo con una sesión abierta y el tiempo con teclado o ratón en uso. ScriptLens solo mide mientras está
        abierto.
      </p>

      <Card title={period === 'dia' ? 'CPU y RAM por hora' : 'CPU y RAM por día'}>
        {s.serie.length < 2 ? (
          <p className="text-sm text-muted">Aún no hay suficientes datos para este periodo. Las estadísticas se guardan cada minuto mientras ScriptLens está abierto.</p>
        ) : (
          <TimeChart
            times={s.serie.map((x) => x.ts)}
            series={[
              { key: 'cpu', label: 'CPU', color: 'var(--chart-cpu)', values: s.serie.map((x) => x.cpu_prom) },
              { key: 'ram', label: 'RAM', color: 'var(--chart-ram)', values: s.serie.map((x) => x.ram_prom) },
            ]}
          />
        )}
      </Card>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Horarios de actividad">
          <div className="overflow-x-auto">
            <div className="grid min-w-[520px] grid-cols-[36px_repeat(24,1fr)] gap-[3px] text-[10px] text-faint">
              <span />
              {Array.from({ length: 24 }, (_, h) => (
                <span key={h} className="text-center">
                  {h % 3 === 0 ? h : ''}
                </span>
              ))}
              {s.horario.map((row, d) => (
                <div key={d} className="contents">
                  <span>{DAYS[d]}</span>
                  {row.map((v, h) => (
                    <span key={h} title={`${DAYS[d]} ${h}:00 — ${duration(v)} de uso activo`} className="h-4 rounded-[3px] bg-accent" style={{ opacity: v ? 0.15 + 0.85 * (v / maxCell) : 0.06 }} />
                  ))}
                </div>
              ))}
            </div>
          </div>
          <p className="mt-2 text-xs text-faint">Cada casilla es una hora; más intensa = más uso activo.</p>
        </Card>
        <Card title="Sesiones de uso">
          {s.sesiones.length === 0 ? (
            <p className="text-sm text-muted">Sin sesiones de uso activo registradas en este periodo.</p>
          ) : (
            <ul className="max-h-64 divide-y divide-line overflow-y-auto text-sm">
              {[...s.sesiones].reverse().map((x) => (
                <li key={x.inicio} className="flex justify-between py-1.5">
                  <span>
                    {fmt(x.inicio, { weekday: 'short', hour: '2-digit', minute: '2-digit' })} – {fmt(x.fin, { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <span className="tabular text-muted">{duration(x.activo_s)} activo</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Procesos con mayor consumo">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-faint">
                <th className="py-1 font-medium">Proceso</th>
                <th className="py-1 text-right font-medium">CPU prom.</th>
                <th className="py-1 text-right font-medium">RAM máx.</th>
              </tr>
            </thead>
            <tbody className="tabular">
              {s.procesos_cpu.map((p) => (
                <tr key={p.name} className="border-t border-line">
                  <td className="truncate py-1.5">{p.name}</td>
                  <td className="py-1.5 text-right">{pct(p.cpu_prom, 1)}</td>
                  <td className="py-1.5 text-right">{bytes(p.ram_max)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {s.procesos_cpu.length === 0 && <p className="text-sm text-muted">Sin datos todavía.</p>}
        </Card>
        <Card title="Aplicaciones más utilizadas">
          {!s.ajustes.aplicaciones ? (
            <div className="flex flex-col gap-3 text-sm text-muted">
              <p>Opcional. Si lo activa, ScriptLens anota cada 10 segundos el nombre del programa en primer plano (por ejemplo «chrome.exe»). No guarda títulos de ventanas, páginas visitadas, textos ni teclas.</p>
              <div>
                <Button tone="primary" onClick={() => setAskApps(true)}>
                  Activar con mi consentimiento
                </Button>
              </div>
            </div>
          ) : s.aplicaciones.length === 0 ? (
            <p className="text-sm text-muted">Activado. Aún no hay datos en este periodo.</p>
          ) : (
            <ul className="divide-y divide-line text-sm">
              {s.aplicaciones.map((a) => (
                <li key={a.app} className="flex justify-between py-1.5">
                  <span className="truncate">{a.app}</span>
                  <span className="tabular text-muted">{duration(a.segundos)}</span>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-3 text-xs text-faint">Los dominios web no se registran: requerirían una extensión voluntaria del navegador, que ScriptLens no instala.</p>
        </Card>
      </div>

      <Card title="Comparación entre días">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-faint">
                <th className="py-1 font-medium">Día</th>
                <th className="py-1 text-right font-medium">CPU prom.</th>
                <th className="py-1 text-right font-medium">RAM prom.</th>
                <th className="py-1 text-right font-medium">Uso activo</th>
                <th className="py-1 text-right font-medium">Red</th>
                <th className="py-1 text-right font-medium">Tiempo medido</th>
              </tr>
            </thead>
            <tbody className="tabular">
              {s.comparacion_dias.map((d) => (
                <tr key={d.dia} className={`border-t border-line ${d.minutos_registrados ? '' : 'text-faint'}`}>
                  <td className="py-1.5">{fmt(d.dia, { weekday: 'long', day: 'numeric', month: 'short' })}</td>
                  <td className="py-1.5 text-right">{pct(d.cpu_prom, 1)}</td>
                  <td className="py-1.5 text-right">{pct(d.ram_prom, 1)}</td>
                  <td className="py-1.5 text-right">{duration(d.activo_s)}</td>
                  <td className="py-1.5 text-right">{bytes(d.red_bytes)}</td>
                  <td className="py-1.5 text-right">{d.minutos_registrados ? duration(d.minutos_registrados * 60) : 'sin datos'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Alertas por consumo sostenido">
          {s.alertas.length === 0 ? (
            <p className="text-sm text-muted">Sin alertas: no hubo 5 minutos seguidos de CPU ≥ 85 % ni de RAM ≥ 90 %.</p>
          ) : (
            <ul className="flex flex-col gap-2 text-sm">
              {s.alertas.map((a) => (
                <li key={a.created_at + a.kind} className="flex gap-2 rounded-xl bg-warn-soft px-3 py-2">
                  <AlertTriangle size={15} className="mt-0.5 shrink-0 text-warn" />
                  <span>
                    <span className="text-muted">{fmt(a.created_at, { dateStyle: 'short', timeStyle: 'short' })}:</span> {a.detail}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card title="Encendidos registrados por Windows">
          {s.arranques.length === 0 ? (
            <p className="text-sm text-muted">Sin datos del registro de eventos.</p>
          ) : (
            <ul className="max-h-64 divide-y divide-line overflow-y-auto text-sm">
              {s.arranques.map((b) => (
                <li key={b.boot_time + b.source} className="flex justify-between gap-3 py-1.5">
                  <span>
                    <Clock size={13} className="mr-1.5 inline text-faint" />
                    {fmt(b.boot_time, { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <span className="text-muted">
                    {SOURCE[b.source] ?? b.source}
                    {b.shutdown_time ? ` → apagado ${fmt(b.shutdown_time, { hour: '2-digit', minute: '2-digit' })}` : ''}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card title="Privacidad de las estadísticas">
        <Row label="Registrar estadísticas" hint="Si lo pausa, no se guardan datos nuevos; los existentes se conservan.">
          <Toggle label="Registrar estadísticas" checked={s.ajustes.activadas} onChange={(v) => save({ activadas: v })} />
        </Row>
        <Row label="Aplicaciones más utilizadas" hint="Solo nombres de programas en primer plano.">
          <Toggle label="Aplicaciones más utilizadas" checked={s.ajustes.aplicaciones} onChange={(v) => (v ? setAskApps(true) : save({ aplicaciones: false }))} />
        </Row>
        <Row label="Conservar el historial" hint="El detalle por minuto se guarda 7 días; los resúmenes por hora, este número de días.">
          <select value={s.ajustes.retencion_dias} onChange={(e) => save({ retencion_dias: Number(e.target.value) })} className="rounded-xl border border-line bg-surface-2 px-3 py-1.5 text-sm" aria-label="Días de historial">
            {[7, 30, 90, 180, 365].map((d) => (
              <option key={d} value={d}>
                {d} días
              </option>
            ))}
          </select>
        </Row>
        <Row label="Borrar estadísticas" hint="Elimina de este equipo todo el historial de estadísticas.">
          <Button tone="danger" icon={<Trash2 size={15} />} onClick={() => setAskDelete(true)}>
            Borrar todo
          </Button>
        </Row>
      </Card>

      {askApps && (
        <Confirm
          title="¿Registrar las aplicaciones que usa?"
          confirmLabel="Sí, activar"
          onCancel={() => setAskApps(false)}
          onConfirm={async () => {
            await save({ aplicaciones: true })
            setAskApps(false)
          }}
        >
          <p>ScriptLens anotará cada 10 segundos el nombre del programa que está en primer plano mientras usa el equipo. Los datos se quedan en esta PC.</p>
          <p>No se guardan títulos de ventanas, direcciones web, textos ni pulsaciones de teclas. Puede pausarlo o borrarlo cuando quiera.</p>
        </Confirm>
      )}
      {askDelete && (
        <Confirm
          title="¿Borrar todas las estadísticas?"
          confirmLabel="Borrar"
          danger
          onCancel={() => setAskDelete(false)}
          onConfirm={async () => {
            await apiDelete('/api/stats/data/todo')
            setAskDelete(false)
            refresh()
          }}
        >
          <p>Se eliminará el historial de rendimiento, procesos, aplicaciones, alertas y encendidos. No se puede deshacer.</p>
        </Confirm>
      )}
    </div>
  )
}
