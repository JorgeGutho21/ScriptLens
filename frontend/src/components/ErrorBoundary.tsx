import { Component, type ReactNode } from 'react'

/** Si una pantalla falla, se muestra un aviso en lugar de dejar toda la ventana en blanco. */
export class ErrorBoundary extends Component<{ children: ReactNode; resetKey?: string }, { error: Error | null }> {
  state = { error: null as Error | null }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  componentDidUpdate(prev: { resetKey?: string }) {
    if (prev.resetKey !== this.props.resetKey && this.state.error) this.setState({ error: null })
  }

  render() {
    if (this.state.error)
      return (
        <div className="mx-auto max-w-xl pt-10" role="alert">
          <div className="card p-6">
            <h2 className="font-display text-lg font-semibold">Esta sección tuvo un problema</h2>
            <p className="mt-2 text-sm text-muted">El resto de ScriptLens sigue funcionando. Puede cambiar de sección o volver a intentarlo.</p>
            <p className="mt-3 break-all font-mono text-xs text-faint">{this.state.error.message}</p>
            <button onClick={() => this.setState({ error: null })} className="mt-4 rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white">
              Reintentar
            </button>
          </div>
        </div>
      )
    return this.props.children
  }
}
