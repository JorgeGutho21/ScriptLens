import { Activity, Clock, Cpu, HardDrive, Layers, Network } from 'lucide-react'
import { Gauge } from '../components/Gauge'
import { Term } from '../components/Term'
import { TimeChart } from '../components/TimeChart'
import { Bar, Card, EstadoBadge, Skeleton, Stat } from '../components/ui'
import { api, type ProcessRow, type Sample, type SustainedRow } from '../lib/api'
import { bytes, duration, levelFor, pct, rate } from '../lib/format'
import { useMetrics } from '../lib/metrics'
import { usePrefs } from '../lib/prefs'
import { usePolling } from '../lib/usePolling'

const TONE = { ok: 'var(--accent)', warn: 'var(--warn)', danger: 'var(--danger)' }

export function Dashboard() {
  const { summary, info } = useMetrics()
  const { prefs } = usePrefs()
  const advanced = prefs.mode === 'avanzado'
  const history = usePolling(() => api<{ samples: Sample[] }>('/api/metrics/history', { seconds: 300 }), 2000)
  const topCpu = usePolling(() => api<{ processes: ProcessRow[] }>('/api/processes/top', { by: 'cpu', limit: 6 }), 3000)
  const topMem = usePolling(() => api<{ processes: ProcessRow[] }>('/api/processes/top', { by: 'memory', limit: 6 }), 3000)
  const sustained = usePolling(() => api<{ processes: SustainedRow[] }>('/api/processes/sustained', { seconds: 60, limit: 5 }), 5000)

  const cur = summary?.current ?? null
  const samples = history.data?.samples ?? []
  const avg = summary?.averages
  // Se calcula con la hora de la medición (no con el reloj del navegador) para que sea reproducible.
  const uptime = info && cur ? cur.ts - info.boot_time : null
  const mainDisk = info?.disks.find((d) => d.mountpoint.toUpperCase().startsWith('C')) ?? info?.disks[0]
  const headline = summary?.findings[0]

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-5">
      {/* Resumen en lenguaje sencillo */}
      <section className="card animate-rise relative overflow-hidden p-6">
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-accent opacity-[0.07] blur-3xl" />
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center">
          <div className="flex justify-center gap-8">
            <Gauge value={cur?.cpu_percent ?? null} label={<Term id="cpu">Procesador</Term>} sublabel={avg?.cpu_1m != null ? `prom. 1 min ${pct(avg.cpu_1m)}` : undefined} />
            <Gauge
              value={cur?.mem_percent ?? null}
              color="var(--chart-ram)"
              label={<Term id="ram">Memoria RAM</Term>}
              sublabel={cur ? `${bytes(cur.mem_used)} de ${bytes(cur.mem_total)}` : undefined}
            />
          </div>
          <div className="min-w-0 flex-1 lg:border-l lg:border-line lg:pl-8">
            {headline ? (
              <>
                <EstadoBadge estado={headline.estado} />
                <h1 className="mt-3 font-display text-2xl font-semibold tracking-tight text-fg">{headline.titulo}</h1>
                <p className="mt-2 max-w-2xl leading-relaxed text-muted">{headline.explicacion}</p>
                <p className="mt-3 text-sm text-faint">
                  <span className="font-medium text-muted">Evidencia medida: </span>
                  {headline.evidencia}
                </p>
              </>
            ) : (
              <div className="space-y-3">
                <Skeleton className="h-6 w-40" />
                <Skeleton className="h-8 w-3/4" />
                <Skeleton className="h-4 w-full" />
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Tarjetas estadísticas */}
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <Stat icon={<HardDrive size={19} />} label={`Almacenamiento ${mainDisk?.mountpoint ?? ''}`} value={mainDisk ? pct(mainDisk.percent) : '—'} hint={mainDisk ? `${bytes(mainDisk.free)} libres de ${bytes(mainDisk.total)}` : undefined} />
        <Stat
          icon={<Activity size={19} />}
          label={<Term id="disco" />}
          value={cur ? rate((cur.disk_read_bps ?? 0) + (cur.disk_write_bps ?? 0)) : '—'}
          hint={cur ? `lectura ${rate(cur.disk_read_bps)} · escritura ${rate(cur.disk_write_bps)}` : undefined}
        />
        <Stat
          icon={<Network size={19} />}
          label={<Term id="red" />}
          value={cur ? rate((cur.net_recv_bps ?? 0) + (cur.net_sent_bps ?? 0)) : '—'}
          hint={cur ? `↓ ${rate(cur.net_recv_bps)} · ↑ ${rate(cur.net_sent_bps)}` : undefined}
        />
        <Stat icon={<Clock size={19} />} label={<Term id="uptime" />} value={uptime != null ? duration(uptime) : '—'} hint={cur ? `${cur.process_count} procesos activos` : undefined} />
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        <Card
          className="xl:col-span-2"
          title="Últimos 5 minutos"
          action={
            <div className="flex items-center gap-4 text-xs text-muted">
              <Legend color="var(--chart-cpu)" label="CPU" />
              <Legend color="var(--chart-ram)" label="RAM" />
            </div>
          }
        >
          {samples.length > 1 ? (
            <TimeChart
              times={samples.map((s) => s.ts)}
              series={[
                { key: 'cpu', label: 'CPU', color: 'var(--chart-cpu)', values: samples.map((s) => s.cpu_percent) },
                { key: 'ram', label: 'RAM', color: 'var(--chart-ram)', values: samples.map((s) => s.mem_percent) },
              ]}
            />
          ) : (
            <Skeleton className="h-[180px] w-full" />
          )}
          <Comparison avg={avg} cur={cur} />
        </Card>

        <Card title="Qué está pasando">
          <ul className="flex flex-col gap-3">
            {(summary?.findings ?? []).map((f) => (
              <li key={f.code} className="rounded-xl border border-line bg-surface-2 p-3.5">
                <EstadoBadge estado={f.estado} />
                <div className="mt-2 text-sm font-medium text-fg">{f.titulo}</div>
                <div className="mt-1 text-[13px] leading-relaxed text-muted">{f.recomendacion}</div>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card title={<>Programas que más usan el <Term id="cpu">procesador</Term></>}>
          <ProcessList rows={topCpu.data?.processes} metric="cpu" />
        </Card>
        <Card title={<>Programas que más usan la <Term id="ram">memoria</Term></>}>
          <ProcessList rows={topMem.data?.processes} metric="memory" total={cur?.mem_total} />
        </Card>
      </div>

      {advanced && (
        <div className="grid gap-5 lg:grid-cols-2">
          <Card title={<>Uso por <Term id="nucleo">núcleo</Term></>}>
            <div className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
              {(cur?.cpu_per_core ?? []).map((c, i) => (
                <div key={i}>
                  <div className="mb-1 flex justify-between text-xs tabular">
                    <span className="text-faint">Núcleo {i + 1}</span>
                    <span className="text-muted">{c.toFixed(0)} %</span>
                  </div>
                  <Bar value={c} tone={TONE[levelFor(c, 75, 92)]} />
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs text-faint">
              <Cpu size={12} className="mr-1 inline" />
              {info ? `${info.cpu_physical ?? '?'} núcleos físicos · ${info.cpu_logical} lógicos · ${info.processor}` : ''}
            </p>
          </Card>
          <Card title={<>Consumo <Term id="sostenido">sostenido</Term> (último minuto)</>}>
            <SustainedList rows={sustained.data?.processes} />
          </Card>
        </div>
      )}

      {advanced && summary && (
        <p className="text-xs text-faint">
          <Layers size={12} className="mr-1 inline" />
          Consumo de ScriptLens (motor de análisis): {bytes(summary.scriptlens.memory_rss)} de RAM · {pct(summary.scriptlens.cpu_percent, 1)} de CPU.
          {info && !info.temperature.available && ` Temperatura: no disponible — ${info.temperature.reason}`}
        </p>
      )}
    </div>
  )
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="h-2 w-2 rounded-full" style={{ background: color }} />
      {label}
    </span>
  )
}

function Comparison({ avg, cur }: { avg?: { cpu_1m: number | null; ram_1m: number | null; cpu_long: number | null; ram_long: number | null; long_samples: number }; cur: Sample | null }) {
  if (!avg || !cur) return null
  const minutes = Math.round(avg.long_samples / 60)
  const rows = [
    { label: 'CPU', now: cur.cpu_percent, m1: avg.cpu_1m, long: avg.cpu_long },
    { label: 'RAM', now: cur.mem_percent, m1: avg.ram_1m, long: avg.ram_long },
  ]
  return (
    <div className="mt-4 grid grid-cols-[auto_1fr_1fr_1fr] gap-x-6 gap-y-1.5 border-t border-line pt-4 text-sm tabular">
      <span />
      <span className="text-xs text-faint">Ahora</span>
      <span className="text-xs text-faint">Promedio 1 min</span>
      <span className="text-xs text-faint">{avg.long_samples >= 120 ? `Promedio ${minutes} min` : 'Promedio de la sesión'}</span>
      {rows.map((r) => (
        <div key={r.label} className="contents">
          <span className="text-muted">{r.label}</span>
          <span className="font-medium text-fg">{pct(r.now)}</span>
          <span className="text-muted">{pct(r.m1)}</span>
          <span className="text-muted">{pct(r.long)}</span>
        </div>
      ))}
    </div>
  )
}

function ProcessList({ rows, metric, total }: { rows?: ProcessRow[]; metric: 'cpu' | 'memory'; total?: number }) {
  if (!rows) return <Skeleton className="h-48 w-full" />
  const max = Math.max(1, ...rows.map((r) => (metric === 'cpu' ? (r.cpu_percent ?? 0) : (r.memory_rss ?? 0))))
  return (
    <ul className="flex flex-col gap-2.5">
      {rows.map((r) => {
        const v = metric === 'cpu' ? (r.cpu_percent ?? 0) : (r.memory_rss ?? 0)
        const share = metric === 'memory' && total ? ((r.memory_rss ?? 0) / total) * 100 : null
        return (
          <li key={`${r.pid}-${r.create_time}`} className="grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1">
            <div className="flex min-w-0 items-baseline gap-2">
              <span className="truncate text-sm font-medium text-fg">{r.name || 'Proceso protegido'}</span>
              <span className="tabular text-[11px] text-faint">PID {r.pid}</span>
            </div>
            <span className="tabular text-sm text-muted">{metric === 'cpu' ? pct(r.cpu_percent, 1) : `${bytes(r.memory_rss)}${share != null ? ` · ${share.toFixed(1)} %` : ''}`}</span>
            <div className="col-span-2">
              <Bar value={(v / max) * 100} tone={metric === 'cpu' ? 'var(--chart-cpu)' : 'var(--chart-ram)'} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

function SustainedList({ rows }: { rows?: SustainedRow[] }) {
  if (!rows) return <Skeleton className="h-40 w-full" />
  if (rows.length === 0) return <p className="text-sm text-muted">Aún no hay suficientes mediciones.</p>
  return (
    <table className="w-full text-sm tabular">
      <thead>
        <tr className="text-left text-xs text-faint">
          <th className="pb-2 font-normal">Proceso</th>
          <th className="pb-2 text-right font-normal">Promedio</th>
          <th className="pb-2 text-right font-normal">Máximo</th>
          <th className="pb-2 text-right font-normal">Mediciones</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.pid} className="border-t border-line">
            <td className="py-2 text-fg">{r.name}</td>
            <td className="py-2 text-right text-fg">{pct(r.cpu_avg, 1)}</td>
            <td className="py-2 text-right text-muted">{pct(r.cpu_max, 1)}</td>
            <td className="py-2 text-right text-faint">{r.samples}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
