import { Bot, CheckCircle2, ChevronRight, Cpu, Download, HardDrive, History, Lock, MessageSquarePlus, Send, ShieldCheck, Trash2, TriangleAlert, User } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Confirm } from '../components/Confirm'
import { Card } from '../components/ui'
import { api, apiDelete, apiStream, openLink } from '../lib/api'

interface Status {
  instalado_o_activo: boolean
  version: string | null
  modelos: string[]
  modelo_predeterminado: string
  modelos_sugeridos: { id: string; nombre: string; descarga_gb: number; ram_gb: number; nota: string }[]
}

interface Msg {
  role: 'user' | 'assistant'
  content: string
  meta?: { modo?: 'ia' | 'sin_ia'; motivo?: string | null; modelo?: string | null; verificacion?: { cifras: number; no_verificadas: string[]; verificada: boolean }; evidencia?: Record<string, unknown>; segundos?: number; herramientas?: string[] }
}

const SUGERENCIAS = [
  '¿Por qué mi computador está lento?',
  '¿Qué programa consume más RAM?',
  '¿Qué proceso consume más CPU?',
  '¿Qué tareas se ejecutan en segundo plano?',
  '¿Qué aplicaciones puedo cerrar sin afectar Windows?',
  '¿Hay programas sospechosos?',
  '¿Qué programas inician con Windows?',
  '¿Qué está ocupando el disco?',
  '¿Qué cambios hubo desde el último análisis?',
  'Explícame este script línea por línea',
]

const TOOL_ES: Record<string, string> = {
  resumen_rendimiento: 'Rendimiento del último minuto',
  procesos_top_memoria: 'Programas por memoria',
  procesos_top_cpu: 'Programas por CPU',
  segundo_plano: 'Procesos en segundo plano',
  cerrables: 'Aplicaciones no esenciales',
  en_revision: 'Procesos con señales',
  seguridad: 'Auditoría de seguridad',
  inicio_automatico: 'Inicio automático',
  tareas: 'Tareas programadas',
  disco: 'Almacenamiento',
  cambios: 'Comparación con el último diagnóstico',
  ultimo_script: 'Último script analizado',
  proceso: 'Detalle del proceso',
  efecto_desactivar_inicio: 'Efecto de desactivar un inicio',
}

export function AssistantPage() {
  const [status, setStatus] = useState<Status | null>(null)
  const [model, setModel] = useState<string>('')
  const [useAi, setUseAi] = useState(true)
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [conv, setConv] = useState<number | null>(null)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [history, setHistory] = useState<{ id: number; created_at: number; title: string }[]>([])
  const [pullTarget, setPullTarget] = useState<Status['modelos_sugeridos'][number] | null>(null)
  const [pull, setPull] = useState<{ status: string; pct: number | null } | null>(null)
  const end = useRef<HTMLDivElement>(null)

  const loadStatus = () =>
    api<Status>('/api/assistant/status').then((s) => {
      setStatus(s)
      setModel((m) => m || (s.modelos.includes(s.modelo_predeterminado) ? s.modelo_predeterminado : s.modelos.find((x) => x.startsWith('qwen3')) ?? s.modelo_predeterminado))
    })
  const loadHistory = () => api<{ conversaciones: { id: number; created_at: number; title: string }[] }>('/api/assistant/conversations').then((r) => setHistory(r.conversaciones))

  useEffect(() => {
    loadStatus()
    loadHistory()
  }, [])
  useEffect(() => {
    // scrollIntoView puede devolver una Promise en Chromium reciente: no se devuelve al efecto.
    end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [msgs])

  const ready = !!status?.instalado_o_activo && status.modelos.includes(model)

  const send = async (q: string) => {
    if (!q.trim() || busy) return
    setInput('')
    setBusy(true)
    setMsgs((m) => [...m, { role: 'user', content: q }, { role: 'assistant', content: '' }])
    try {
      let tools: string[] = []
      for await (const ev of apiStream<Record<string, unknown>>('/api/assistant/ask', { pregunta: q, conversacion_id: conv, modelo: model || null, usar_ia: useAi })) {
        if (ev.type === 'conversation' && ev.id) setConv(ev.id as number)
        if (ev.type === 'route') tools = ev.herramientas as string[]
        if (ev.type === 'token') setMsgs((m) => m.map((x, i) => (i === m.length - 1 ? { ...x, content: x.content + (ev.text as string) } : x)))
        if (ev.type === 'done')
          setMsgs((m) => m.map((x, i) => (i === m.length - 1 ? { ...x, content: (ev.answer as string) || x.content, meta: { ...(ev as unknown as Msg['meta']), herramientas: tools } } : x)))
      }
    } catch (e) {
      setMsgs((m) => m.map((x, i) => (i === m.length - 1 ? { ...x, content: `No se pudo obtener respuesta: ${(e as Error).message}` } : x)))
    } finally {
      setBusy(false)
      loadHistory()
    }
  }

  const openConversation = async (id: number) => {
    const r = await api<{ mensajes: { role: 'user' | 'assistant'; content: string; meta: Msg['meta'] }[] }>(`/api/assistant/conversations/${id}`)
    setConv(id)
    setMsgs(r.mensajes.map((m) => ({ role: m.role, content: m.content, meta: m.meta ?? undefined })))
  }

  const doPull = async () => {
    if (!pullTarget) return
    const target = pullTarget
    setPullTarget(null)
    setPull({ status: 'Iniciando descarga…', pct: 0 })
    try {
      for await (const ev of apiStream<{ status?: string; total?: number; completed?: number; error?: string }>('/api/assistant/pull', { modelo: target.id, acepto_descarga: true })) {
        if (ev.error) throw new Error(ev.error)
        setPull({ status: ev.status ?? '', pct: ev.total ? Math.round(((ev.completed ?? 0) / ev.total) * 100) : null })
      }
      setPull(null)
      setModel(target.id)
      loadStatus()
    } catch (e) {
      setPull({ status: `Error: ${(e as Error).message}`, pct: null })
    }
  }

  return (
    <div className="mx-auto grid max-w-[1400px] gap-5 xl:grid-cols-[1fr_320px]">
      <div className="card flex h-[calc(100vh-170px)] min-h-[520px] flex-col">
        <div className="flex flex-wrap items-center gap-3 border-b border-line px-5 py-3">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-accent-soft text-accent">
            <Bot size={19} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-medium text-fg">Asistente de ScriptLens</div>
            <div className="text-xs text-faint">{ready && useAi ? `IA local: ${model}` : 'Modo sin IA: respuestas con plantillas a partir de los datos medidos'}</div>
          </div>
          <label className="flex items-center gap-2 text-xs text-muted">
            <input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} className="accent-[var(--accent)]" /> Usar IA local
          </label>
          {status && status.modelos.length > 0 && (
            <select value={model} onChange={(e) => setModel(e.target.value)} aria-label="Modelo" className="rounded-lg border border-line bg-surface-2 px-2 py-1 text-xs">
              {status.modelos.map((m) => (
                <option key={m}>{m}</option>
              ))}
            </select>
          )}
          <button
            onClick={() => {
              setMsgs([])
              setConv(null)
            }}
            className="flex items-center gap-1.5 rounded-lg border border-line px-2.5 py-1 text-xs text-muted hover:text-fg"
          >
            <MessageSquarePlus size={14} /> Nueva
          </button>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto p-5" aria-live="polite">
          {msgs.length === 0 && (
            <div className="mx-auto max-w-xl pt-6 text-center">
              <h2 className="font-display text-xl font-semibold">Pregunte sobre su computador</h2>
              <p className="mt-2 text-sm text-muted">El asistente consulta las mediciones reales de este equipo (solo lectura) y las explica. No ejecuta acciones: usted decide desde ScriptLens.</p>
              <div className="mt-5 flex flex-wrap justify-center gap-2">
                {SUGERENCIAS.map((s) => (
                  <button key={s} onClick={() => send(s)} className="rounded-full border border-line bg-surface-2 px-3 py-1.5 text-[13px] text-muted hover:border-accent hover:text-fg">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {msgs.map((m, i) => (
            <MessageView key={i} m={m} streaming={busy && i === msgs.length - 1} />
          ))}
          <div ref={end} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            send(input)
          }}
          className="flex gap-2 border-t border-line p-3"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            maxLength={1000}
            placeholder="Escriba su pregunta…"
            aria-label="Pregunta para el asistente"
            className="flex-1 rounded-xl border border-line bg-surface-2 px-3.5 py-2.5 text-sm placeholder:text-faint"
          />
          <button type="submit" disabled={busy || !input.trim()} aria-label="Enviar" className="grid w-11 place-items-center rounded-xl bg-accent text-white hover:bg-accent-strong disabled:opacity-50">
            <Send size={17} />
          </button>
        </form>
      </div>

      <div className="flex flex-col gap-4">
        <Card title="IA local">
          {!status ? null : status.instalado_o_activo ? (
            <p className="flex items-center gap-2 text-sm text-ok">
              <CheckCircle2 size={16} /> Ollama {status.version} activo
            </p>
          ) : (
            <p className="flex items-center gap-2 text-sm text-warn">
              <TriangleAlert size={16} /> Ollama no está instalado o no está abierto
            </p>
          )}
          <details className="mt-3 text-[13px] text-muted" open={!!status && !status.instalado_o_activo}>
            <summary className="cursor-pointer font-medium text-fg">¿Qué es y cómo activarla?</summary>
            <div className="mt-2 space-y-2 leading-relaxed">
              <p><strong className="text-fg">Ollama</strong> es un programa gratuito que ejecuta modelos de inteligencia artificial en su propio equipo.</p>
              <p className="flex gap-1.5"><Lock size={14} className="mt-0.5 shrink-0" /> Privacidad: las preguntas y los datos nunca salen del computador.</p>
              <p className="flex gap-1.5"><HardDrive size={14} className="mt-0.5 shrink-0" /> Modelo recomendado: Qwen3 4B Instruct (descarga ≈ 2,5 GB).</p>
              <p className="flex gap-1.5"><Cpu size={14} className="mt-0.5 shrink-0" /> Recursos: al menos 8 GB de RAM; con 4–5 GB libres responde en 10–30 s en un portátil sin tarjeta gráfica dedicada.</p>
              <ol className="list-decimal space-y-1 pl-5">
                <li>Descargue Ollama desde su sitio oficial: <button onClick={() => openLink('https://ollama.com/download')} className="text-accent hover:underline">ollama.com/download</button>.</li>
                <li>Instálelo y ábralo (queda en la bandeja del sistema).</li>
                <li>Vuelva aquí y descargue el modelo con el botón de abajo.</li>
                <li>Verifique: el indicador superior debe decir «Ollama activo».</li>
              </ol>
              <p>Sin Ollama, el asistente igualmente responde con los datos medidos usando plantillas.</p>
            </div>
          </details>
          {status?.instalado_o_activo && (
            <div className="mt-3 space-y-2">
              {status.modelos_sugeridos.map((m) => {
                const have = status.modelos.includes(m.id)
                return (
                  <div key={m.id} className="rounded-xl border border-line bg-surface-2 p-2.5 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-fg">{m.nombre}</span>
                      {have ? <span className="ml-auto text-ok">Descargado</span> : (
                        <button onClick={() => setPullTarget(m)} disabled={!!pull} className="ml-auto flex items-center gap-1 rounded-lg bg-accent px-2 py-1 text-white disabled:opacity-50">
                          <Download size={12} /> {m.descarga_gb} GB
                        </button>
                      )}
                    </div>
                    <div className="mt-0.5 text-faint">{m.nota}</div>
                  </div>
                )
              })}
              {pull && (
                <div className="text-xs text-muted" role="status">
                  {pull.status} {pull.pct != null && `${pull.pct} %`}
                  {pull.pct != null && (
                    <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-3">
                      <div className="h-full bg-accent" style={{ width: `${pull.pct}%` }} />
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </Card>

        <Card title={<span className="flex items-center gap-2"><History size={14} /> Conversaciones</span>}>
          {history.length === 0 ? (
            <p className="text-sm text-muted">Sin conversaciones guardadas.</p>
          ) : (
            <ul className="space-y-1">
              {history.slice(0, 12).map((h) => (
                <li key={h.id} className="group flex items-center gap-2">
                  <button onClick={() => openConversation(h.id)} className={`min-w-0 flex-1 truncate rounded-lg px-2 py-1.5 text-left text-[13px] hover:bg-surface-2 ${conv === h.id ? 'bg-accent-soft text-fg' : 'text-muted'}`}>
                    {h.title}
                  </button>
                  <button
                    aria-label={`Borrar conversación ${h.title}`}
                    onClick={async () => {
                      await apiDelete(`/api/assistant/conversations/${h.id}`)
                      if (conv === h.id) {
                        setMsgs([])
                        setConv(null)
                      }
                      loadHistory()
                    }}
                    className="text-faint opacity-0 hover:text-danger group-hover:opacity-100"
                  >
                    <Trash2 size={14} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      {pullTarget && (
        <Confirm title={`¿Descargar ${pullTarget.nombre}?`} confirmLabel="Descargar" onConfirm={doPull} onCancel={() => setPullTarget(null)}>
          <p>Ollama descargará el modelo «{pullTarget.id}» desde su registro oficial (≈ {pullTarget.descarga_gb} GB). Necesitará unos {pullTarget.ram_gb} GB de RAM libres para usarlo.</p>
          <p>La descarga usa su conexión a Internet una sola vez; después el asistente funciona sin conexión y sus datos no salen del equipo.</p>
        </Confirm>
      )}
    </div>
  )
}

function MessageView({ m, streaming }: { m: Msg; streaming: boolean }) {
  const isUser = m.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-xl ${isUser ? 'bg-surface-3 text-muted' : 'bg-accent-soft text-accent'}`}>{isUser ? <User size={16} /> : <Bot size={16} />}</div>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-[14.5px] leading-relaxed ${isUser ? 'bg-accent text-white' : 'border border-line bg-surface-2 text-fg'}`}>
        <div className="whitespace-pre-wrap">{m.content.replace(/\*\*(.+?)\*\*/g, '$1') || (streaming ? 'Consultando las mediciones…' : '')}</div>
        {m.meta && (
          <div className="mt-3 space-y-2 border-t border-line pt-2.5 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              {m.meta.verificacion && (m.meta.verificacion.verificada ? (
                <span className="flex items-center gap-1 text-ok"><ShieldCheck size={13} /> {m.meta.verificacion.cifras} cifra(s) verificadas con los datos medidos</span>
              ) : (
                <span className="flex items-center gap-1 text-warn"><TriangleAlert size={13} /> Cifras no verificadas: {m.meta.verificacion.no_verificadas.join(', ')}. Tómelas con precaución.</span>
              ))}
              <span className="text-faint">· {m.meta.modo === 'ia' ? `IA local (${m.meta.modelo})` : 'Sin IA'}{m.meta.segundos != null ? ` · ${m.meta.segundos} s` : ''}</span>
            </div>
            {m.meta.motivo && <div className="text-faint">{m.meta.motivo}</div>}
            {m.meta.evidencia && (
              <details className="group">
                <summary className="flex cursor-pointer list-none items-center gap-1 text-muted">
                  <ChevronRight size={13} className="transition-transform group-open:rotate-90" /> Evidencia usada: {Object.keys(m.meta.evidencia).map((k) => TOOL_ES[k] ?? k).join(', ')}
                </summary>
                <pre className="mt-2 max-h-60 overflow-auto rounded-lg bg-surface p-2 font-mono text-[11px] text-muted">{JSON.stringify(m.meta.evidencia, null, 1)}</pre>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
