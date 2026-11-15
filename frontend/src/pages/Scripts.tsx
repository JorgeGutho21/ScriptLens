import { AlertTriangle, BookOpen, FileCode2, GitBranch, Info, Lock, Upload } from 'lucide-react'
import { useRef, useState, type ReactNode } from 'react'
import { Card } from '../components/ui'
import { apiPost } from '../lib/api'

interface Hallazgo {
  linea: number
  regla: string
  categoria: string
  categoria_es: string
  attack: string
  explicacion: string
  codigo: string
  operacion: 'consulta' | 'modificacion' | 'sensible'
  ampliacion: boolean
  decodificado?: boolean
}

interface LineaExp {
  linea: number
  codigo: string
  tipo: 'comentario' | 'regla' | 'comun' | 'no_catalogado'
  operacion: 'consulta' | 'modificacion' | 'sensible' | null
  explicacion: string
  reglas?: string[]
}

export interface ScriptResult {
  archivo: string
  tipo: string
  codificacion: string
  bytes: number
  lineas_total: number
  clasificacion: {
    estadistica: { clase: string | null; probabilidades: Record<string, number> | null; rasgos_relevantes: { rasgo: string; aporte: number }[] }
    reglas: string
    hibrida: string
    umbral_sensible: number
    nota: string
  }
  hallazgos: Hallazgo[]
  operaciones: Record<string, number>
  tecnicas: { id: string; nombre: string; tacticas: string[]; url: string | null; lineas: number[] }[]
  severidad: { nivel: 'baja' | 'media' | 'alta' | 'critica'; puntos: number; motivos: string[] }
  flujo: { etiquetas: Record<string, number>; saltos: { linea: number; tipo: string; destino: string; existe: boolean }[]; ciclos: { linea: number; destino: string; desde: number; con_salida: boolean }[]; posible_ciclo_infinito: boolean; saltos_rotos: unknown[] }
  estructuras: { conteo: Record<string, number>; funciones: { nombre: string; linea: number }[] }
  ofuscacion: string[]
  decodificado: { linea: number; origen: string; texto: string }[]
  explicacion_lineas: LineaExp[]
  limitaciones: string[]
  attack_version: string
  tiempo_ms: number
}

const CLASE_ES: Record<string, string> = { consulta: 'Consulta', modifica: 'Modifica', sensible: 'Sensible' }
const CLASE_DESC: Record<string, string> = {
  consulta: 'Solo lee información del equipo.',
  modifica: 'Crea o cambia archivos o configuración del usuario.',
  sensible: 'Persistencia, borrado, ocultamiento, red automática, cuentas, procesos o protecciones.',
}
const OP_COLOR: Record<string, string> = { consulta: 'var(--ok)', modificacion: 'var(--warn)', sensible: 'var(--danger)' }
const SEV: Record<string, { label: string; cls: string }> = {
  baja: { label: 'Baja', cls: 'bg-ok-soft text-ok' },
  media: { label: 'Media', cls: 'bg-warn-soft text-warn' },
  alta: { label: 'Alta', cls: 'bg-danger-soft text-danger' },
  critica: { label: 'Crítica', cls: 'bg-danger text-white' },
}

const EJEMPLOS: { nombre: string; texto: string }[] = [
  { nombre: 'ejemplo_auditoria_segura.bat', texto: '@echo off\nrem Auditoria de solo consulta (ejemplo)\nsysteminfo\ntasklist\nipconfig /all\nwhoami\npause\n' },
  {
    nombre: 'ejemplo_persistencia.bat',
    texto: '@echo off\nrem EJEMPLO DE DEMOSTRACION: no ejecutar\n:INICIO\nreg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v Demo /d "C:\\Lab\\demo.bat" /f\nattrib +h +s "C:\\Lab\\demo.bat"\nrmdir /s /q "C:\\Lab\\Temporal"\ntimeout /t 10 >nul\ngoto INICIO\n',
  },
]

function toBase64(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf)
  let s = ''
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000))
  return btoa(s)
}

export function ScriptsPage() {
  const [result, setResult] = useState<ScriptResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [drag, setDrag] = useState(false)
  const input = useRef<HTMLInputElement>(null)

  const send = async (nombre: string, buf: ArrayBuffer) => {
    setBusy(true)
    setError(null)
    try {
      setResult(await apiPost<ScriptResult>('/api/scripts/analyze', { nombre, contenido_b64: toBase64(buf) }))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const onFile = async (f: File | undefined) => {
    if (!f) return
    // Se lee como bytes en la interfaz y se envía como texto: el archivo nunca se abre con un intérprete.
    await send(f.name, await f.slice(0, 1_000_000).arrayBuffer())
  }

  return (
    <div className="mx-auto flex max-w-[1300px] flex-col gap-5">
      <section
        onDragOver={(e) => {
          e.preventDefault()
          setDrag(true)
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDrag(false)
          onFile(e.dataTransfer.files[0])
        }}
        className={`card animate-rise flex flex-col items-center gap-3 border-2 border-dashed p-8 text-center transition-colors ${drag ? 'border-accent bg-accent-soft' : 'border-line'}`}
      >
        <div className="grid h-14 w-14 place-items-center rounded-2xl bg-accent-soft text-accent">
          <FileCode2 size={26} />
        </div>
        <h2 className="font-display text-lg font-semibold">Analice un script antes de ejecutarlo</h2>
        <p className="max-w-xl text-sm text-muted">Arrastre aquí un archivo .bat, .cmd o .ps1, o selecciónelo. ScriptLens lo lee como texto: <strong className="text-fg">nunca lo ejecuta</strong>.</p>
        <div className="flex flex-wrap justify-center gap-2">
          <button onClick={() => input.current?.click()} disabled={busy} className="flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-strong disabled:opacity-60">
            <Upload size={16} /> {busy ? 'Analizando…' : 'Seleccionar archivo'}
          </button>
          {EJEMPLOS.map((e) => (
            <button key={e.nombre} onClick={() => send(e.nombre, new TextEncoder().encode(e.texto).buffer as ArrayBuffer)} className="rounded-xl border border-line px-3 py-2 text-sm text-muted hover:text-fg">
              Ejemplo: {e.nombre.replace('ejemplo_', '').replace('.bat', '').replace('_', ' ')}
            </button>
          ))}
        </div>
        <input ref={input} type="file" accept=".bat,.cmd,.ps1,.psm1,.txt" className="hidden" onChange={(e) => onFile(e.target.files?.[0])} />
        <p className="flex items-center gap-1.5 text-xs text-faint"><Lock size={12} /> El análisis ocurre en este equipo. Límite: 1 MB.</p>
      </section>

      {error && <p className="rounded-xl bg-danger-soft p-4 text-sm text-danger">{error}</p>}
      {result && <ScriptReport r={result} />}
    </div>
  )
}

export function ScriptReport({ r }: { r: ScriptResult }) {
  const c = r.clasificacion
  const proba = c.estadistica.probabilidades
  const sev = SEV[r.severidad.nivel]
  return (
    <>
      <div className="flex flex-wrap items-center gap-3 text-sm text-muted">
        <span className="font-medium text-fg">{r.archivo || 'Script'}</span>
        <span>· {r.tipo === 'powershell' ? 'PowerShell' : r.tipo.toUpperCase()}</span>
        <span>· {r.lineas_total} líneas</span>
        <span>· {r.codificacion}</span>
        <span>· {r.tiempo_ms} ms</span>
        <span className="ml-auto rounded-full bg-ok-soft px-2.5 py-1 text-xs text-ok">No se ejecutó</span>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="1 · Clasificación estadística">
          <div className="font-display text-2xl font-semibold">{c.estadistica.clase ? CLASE_ES[c.estadistica.clase] : 'No disponible'}</div>
          <p className="mb-3 text-xs text-faint">Regresión logística con clases balanceadas</p>
          {proba &&
            ['consulta', 'modifica', 'sensible'].map((k) => (
              <div key={k} className="mb-2">
                <div className="mb-1 flex justify-between text-xs tabular">
                  <span className="text-muted">{CLASE_ES[k]}</span>
                  <span className="text-fg">{((proba[k] ?? 0) * 100).toFixed(1)} %</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-surface-3">
                  <div className="h-full rounded-full" style={{ width: `${(proba[k] ?? 0) * 100}%`, background: k === 'sensible' ? 'var(--danger)' : k === 'modifica' ? 'var(--warn)' : 'var(--ok)' }} />
                </div>
              </div>
            ))}
          <p className="mt-3 flex gap-1.5 rounded-lg bg-surface-2 p-2.5 text-[11.5px] leading-relaxed text-muted">
            <Info size={14} className="mt-0.5 shrink-0" /> Estas cifras indican el parecido con los ejemplos de entrenamiento de cada clase. No son la probabilidad de que el script sea malicioso.
          </p>
        </Card>
        <Card title="2 · Reglas y decisión">
          <div className="space-y-3">
            <div>
              <div className="text-xs text-faint">Clasificación por reglas (sin IA)</div>
              <div className="font-display text-xl font-semibold">{CLASE_ES[c.reglas]}</div>
            </div>
            <div className="rounded-xl border border-line bg-surface-2 p-3">
              <div className="text-xs text-faint">Decisión final (híbrida)</div>
              <div className="font-display text-2xl font-semibold" style={{ color: c.hibrida === 'sensible' ? 'var(--danger)' : c.hibrida === 'modifica' ? 'var(--warn)' : 'var(--ok)' }}>
                {CLASE_ES[c.hibrida]}
              </div>
              <div className="text-xs text-muted">{CLASE_DESC[c.hibrida]}</div>
            </div>
            <p className="text-[11.5px] text-faint">{c.nota}</p>
          </div>
        </Card>
        <Card title="3 · Severidad contextual">
          <span className={`inline-block rounded-full px-3 py-1 text-sm font-semibold ${sev.cls}`}>{sev.label}</span>
          <ul className="mt-3 space-y-1.5 text-[13px] text-muted">
            {r.severidad.motivos.map((m) => (
              <li key={m} className="flex gap-2"><span className="text-faint">•</span>{m}</li>
            ))}
          </ul>
          <div className="mt-3 flex gap-3 text-xs tabular">
            <span style={{ color: OP_COLOR.consulta }}>{r.operaciones.consulta} consulta</span>
            <span style={{ color: OP_COLOR.modificacion }}>{r.operaciones.modificacion} modificación</span>
            <span style={{ color: OP_COLOR.sensible }}>{r.operaciones.sensible} sensibles</span>
          </div>
        </Card>
      </div>

      {r.tecnicas.length > 0 && (
        <Card title={`Técnicas MITRE ATT&CK® (versión ${r.attack_version})`}>
          <div className="grid gap-2 md:grid-cols-2">
            {r.tecnicas.map((t) => (
              <div key={t.id} className="flex items-start gap-3 rounded-xl border border-line bg-surface-2 p-3">
                <span className="rounded-md bg-accent-soft px-2 py-0.5 font-mono text-xs text-accent">{t.id}</span>
                <div className="min-w-0">
                  <div className="text-sm font-medium text-fg">{t.nombre}</div>
                  <div className="text-xs text-faint">{t.tacticas.join(', ')} · líneas {t.lineas.join(', ')}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card title="Explicación línea por línea">
        <div className="max-h-[520px] overflow-auto rounded-xl border border-line bg-surface-2 font-mono text-[12.5px]">
          {r.explicacion_lineas.map((l) => (
            <div key={l.linea} className="grid grid-cols-[48px_minmax(0,1fr)_minmax(0,1fr)] border-b border-line/60">
              <span className="border-r border-line/60 px-2 py-1.5 text-right text-faint" style={{ boxShadow: l.operacion ? `inset 3px 0 0 ${OP_COLOR[l.operacion]}` : undefined }}>
                {l.linea}
              </span>
              <code className={`whitespace-pre-wrap break-all px-3 py-1.5 ${l.tipo === 'comentario' ? 'text-faint' : 'text-fg'}`}>{l.codigo}</code>
              <span className={`border-l border-line/60 px-3 py-1.5 font-sans text-[12.5px] ${l.tipo === 'no_catalogado' ? 'text-faint italic' : 'text-muted'}`}>
                {l.explicacion}
                {l.reglas && <span className="ml-1 text-[11px] text-faint">({l.reglas.join(', ')})</span>}
              </span>
            </div>
          ))}
        </div>
        <div className="mt-2 flex gap-4 text-xs text-faint">
          <Legend color={OP_COLOR.consulta} label="Consulta" />
          <Legend color={OP_COLOR.modificacion} label="Modificación" />
          <Legend color={OP_COLOR.sensible} label="Sensible" />
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title={<span className="flex items-center gap-2"><GitBranch size={14} /> Flujo y estructuras</span>}>
          {r.flujo.posible_ciclo_infinito && (
            <p className="mb-3 flex gap-2 rounded-lg bg-warn-soft p-2.5 text-sm text-warn">
              <AlertTriangle size={16} className="mt-0.5 shrink-0" /> Posible ciclo infinito: hay un salto hacia atrás (o un bucle) sin condición de salida.
            </p>
          )}
          <dl className="grid grid-cols-[auto_1fr] gap-x-5 gap-y-1.5 text-sm">
            <Row k="Etiquetas">{Object.entries(r.flujo.etiquetas).map(([k, v]) => `:${k} (l. ${v})`).join(', ') || 'Ninguna'}</Row>
            <Row k="Saltos">{r.flujo.saltos.map((s) => `${s.tipo} ${s.destino} (l. ${s.linea})${s.existe ? '' : ' ⚠ destino inexistente'}`).join(', ') || 'Ninguno'}</Row>
            <Row k="Ciclos">{r.flujo.ciclos.map((c) => `l. ${c.desde}→${c.linea} ${c.con_salida ? '(con salida)' : '(sin salida)'}`).join(', ') || 'Ninguno'}</Row>
            <Row k="Estructuras">{Object.entries(r.estructuras.conteo).map(([k, v]) => `${k.replace('_', ' ')}: ${v}`).join(' · ') || 'Ninguna'}</Row>
            {r.estructuras.funciones.length > 0 && <Row k="Funciones">{r.estructuras.funciones.map((f) => f.nombre).join(', ')}</Row>}
          </dl>
        </Card>
        <Card title={<span className="flex items-center gap-2"><BookOpen size={14} /> Evidencia y limitaciones</span>}>
          {r.ofuscacion.length > 0 && (
            <div className="mb-3">
              <div className="mb-1 text-xs font-medium text-warn">Ofuscación detectada</div>
              <ul className="space-y-0.5 text-[13px] text-muted">{r.ofuscacion.map((o) => <li key={o}>• {o}</li>)}</ul>
            </div>
          )}
          {r.decodificado.map((d) => (
            <div key={d.linea + d.origen} className="mb-3 rounded-lg bg-surface-2 p-2.5">
              <div className="text-xs text-faint">Contenido decodificado ({d.origen}, línea {d.linea}) — solo lectura</div>
              <code className="block whitespace-pre-wrap break-all text-[12px] text-fg">{d.texto.slice(0, 600)}</code>
            </div>
          ))}
          {c.estadistica.rasgos_relevantes.length > 0 && (
            <div className="mb-3 text-[12.5px] text-muted">
              <span className="text-xs text-faint">Fragmentos que más acercan el script a «sensible»: </span>
              {c.estadistica.rasgos_relevantes.map((f) => `«${f.rasgo}»`).join(', ')}
            </div>
          )}
          <ul className="space-y-1.5 text-[13px] text-muted">{r.limitaciones.map((l) => <li key={l} className="flex gap-2"><Info size={13} className="mt-0.5 shrink-0 text-faint" />{l}</li>)}</ul>
        </Card>
      </div>
    </>
  )
}

const Row = ({ k, children }: { k: string; children: ReactNode }) => (
  <>
    <dt className="text-faint">{k}</dt>
    <dd className="break-words text-fg">{children}</dd>
  </>
)

const Legend = ({ color, label }: { color: string; label: string }) => (
  <span className="flex items-center gap-1.5">
    <span className="h-2.5 w-1 rounded" style={{ background: color }} />
    {label}
  </span>
)
