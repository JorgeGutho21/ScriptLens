import { useLayoutEffect, useMemo, useRef, useState } from 'react'
import { clock } from '../lib/format'

export interface Series {
  key: string
  label: string
  color: string
  values: (number | null)[]
}

/**
 * Gráfico temporal ligero en SVG (sin librerías): 0–100 %, ventana fija.
 * Se redibuja solo cuando cambian los datos, para no consumir recursos.
 */
export function TimeChart({ times, series, height = 180 }: { times: number[]; series: Series[]; height?: number }) {
  const wrap = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(600)
  const [hover, setHover] = useState<number | null>(null)

  useLayoutEffect(() => {
    if (!wrap.current) return
    const ro = new ResizeObserver(([e]) => setWidth(Math.max(200, e.contentRect.width)))
    ro.observe(wrap.current)
    return () => ro.disconnect()
  }, [])

  const padL = 34
  const padB = 22
  const padT = 8
  const w = width - padL
  const h = height - padB
  const n = times.length
  const x = (i: number) => padL + (n <= 1 ? w : (i / (n - 1)) * w)
  const y = (v: number) => h - (Math.max(0, Math.min(100, v)) / 100) * (h - padT)

  const paths = useMemo(
    () =>
      series.map((s) => {
        let line = ''
        s.values.forEach((v, i) => {
          if (v == null) return
          line += `${line ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`
        })
        const area = line ? `${line}L${x(n - 1).toFixed(1)},${h}L${x(0).toFixed(1)},${h}Z` : ''
        return { ...s, line, area }
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [series, width, n],
  )

  const onMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (n < 2) return
    const rect = e.currentTarget.getBoundingClientRect()
    const rel = (e.clientX - rect.left - padL) / w
    setHover(Math.max(0, Math.min(n - 1, Math.round(rel * (n - 1)))))
  }

  return (
    <div ref={wrap} className="relative w-full select-none">
      <svg width={width} height={height} onMouseMove={onMove} onMouseLeave={() => setHover(null)} role="img" aria-label="Gráfico de uso en el tiempo">
        <defs>
          {series.map((s) => (
            <linearGradient key={s.key} id={`g-${s.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor={s.color} stopOpacity="0.28" />
              <stop offset="1" stopColor={s.color} stopOpacity="0" />
            </linearGradient>
          ))}
        </defs>
        {[0, 25, 50, 75, 100].map((t) => (
          <g key={t}>
            <line x1={padL} x2={width} y1={y(t)} y2={y(t)} stroke="var(--chart-grid)" strokeDasharray={t === 0 ? undefined : '3 4'} />
            <text x={padL - 8} y={y(t) + 4} textAnchor="end" fontSize="10.5" fill="var(--text-faint)" className="tabular">
              {t}
            </text>
          </g>
        ))}
        {paths.map((p) => (
          <g key={p.key}>
            <path d={p.area} fill={`url(#g-${p.key})`} />
            <path d={p.line} fill="none" stroke={p.color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
          </g>
        ))}
        {n > 1 && (
          <>
            <text x={padL} y={height - 6} fontSize="10.5" fill="var(--text-faint)">
              {clock(times[0])}
            </text>
            <text x={width - 2} y={height - 6} fontSize="10.5" fill="var(--text-faint)" textAnchor="end">
              ahora
            </text>
          </>
        )}
        {hover != null && (
          <g>
            <line x1={x(hover)} x2={x(hover)} y1={0} y2={h} stroke="var(--border-strong)" />
            {series.map((s) =>
              s.values[hover] == null ? null : (
                <circle key={s.key} cx={x(hover)} cy={y(s.values[hover]!)} r="4" fill="var(--surface)" stroke={s.color} strokeWidth="2" />
              ),
            )}
          </g>
        )}
      </svg>
      {hover != null && (
        <div
          className="pointer-events-none absolute top-1 rounded-lg border border-line-strong bg-surface-2 px-3 py-2 text-xs shadow-xl"
          style={{ left: Math.min(x(hover) + 10, width - 150) }}
        >
          <div className="mb-1 text-faint tabular">{clock(times[hover])}</div>
          {series.map((s) => (
            <div key={s.key} className="flex items-center gap-2 tabular">
              <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
              <span className="text-muted">{s.label}</span>
              <span className="ml-auto font-semibold text-fg">{s.values[hover]?.toFixed(1) ?? '—'} %</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
