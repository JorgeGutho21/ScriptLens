/** Logotipo original de ScriptLens IA: lente de análisis con corchetes de código. */
export function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="sl-lens" x1="10" y1="8" x2="50" y2="52" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6DB0FF" />
          <stop offset="1" stopColor="#1F6FEB" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="15" fill="#0B1220" />
      <rect x="0.75" y="0.75" width="62.5" height="62.5" rx="14.25" stroke="#22324A" strokeWidth="1.5" />
      <circle cx="28" cy="28" r="15" stroke="url(#sl-lens)" strokeWidth="5" />
      <path d="M39.5 39.5 L51 51" stroke="url(#sl-lens)" strokeWidth="6.5" strokeLinecap="round" />
      <path
        d="M24 22 L19 28 L24 34 M32 22 L37 28 L32 34"
        stroke="#E8EEF7"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <LogoMark size={compact ? 30 : 34} />
      {!compact && (
        <div className="leading-tight">
          <div className="font-display text-[15px] font-semibold tracking-tight text-fg">
            ScriptLens <span className="text-accent">IA</span>
          </div>
          <div className="text-[11px] text-faint">Diagnóstico inteligente</div>
        </div>
      )}
    </div>
  )
}
