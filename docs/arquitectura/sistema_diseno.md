# Sistema de diseño de ScriptLens IA

Implementado como variables CSS en `frontend/src/index.css` y expuesto a Tailwind mediante `@theme inline`.

## Color

| Token | Oscuro | Claro | Uso |
|---|---|---|---|
| `--bg` | `#080b10` | `#f3f5f9` | Fondo (negro grafito) |
| `--surface` / `-2` / `-3` | `#0f141c` / `#151c27` / `#1c2533` | `#fff` / `#f6f8fb` / `#edf1f7` | Tarjetas, controles, pistas |
| `--border` | `#222c3b` | `#dde3ec` | Bordes |
| `--text` / `--text-muted` / `--text-faint` | `#e8eef7` / `#93a1b5` / `#64718a` | `#0e1621` / `#4b5a70` / `#75839a` | Jerarquía de texto |
| `--accent` | `#3b8cff` | `#1f6feb` | Azul tecnológico: acción principal, CPU |
| `--chart-ram` | `#9d7bff` | `#7c4dff` | Serie RAM (distinguible de CPU) |
| `--ok` / `--warn` / `--danger` | verde / ámbar / rojo | versiones oscuras | **Solo** para estados |

Regla: el color de estado nunca es decorativo. Un indicador es azul mientras el valor es normal y cambia a ámbar (≥70 %) o rojo (≥88 %).

## Tipografía

- Interfaz: *Segoe UI Variable Text* (incluida en Windows 11; respaldo Segoe UI).
- Títulos y cifras grandes: *Segoe UI Variable Display*.
- Código y rutas: *Cascadia Mono*.
- Base 15 px × `--font-scale` (ajustable 90–130 % en Ajustes). Cifras con `tabular-nums` para que no "bailen" al actualizarse.

Escala: 11 · 12 · 13 · 14 · 15 · 18 · 20 · 24 · 36 px.

## Espaciado y forma

Escala de 4 px (Tailwind). Tarjetas con radio 14 px, controles 10–12 px, insignias en píldora. Separación entre tarjetas 16–20 px.

## Componentes

`Card`, `Stat`, `Gauge` (indicador circular), `TimeChart` (SVG, cursor con valores), `Bar`, `EstadoBadge`, `Term` (glosario), `Skeleton`, `Toggle`, `Onboarding`, `Sidebar`, `TopBar`, `Footer`.

## Estados de hallazgo

`normal` · `informativo` · `consumo_elevado` · `requiere_revision` · `info_insuficiente` (y en fases siguientes `actividad_sospechosa`, `amenaza_detectada`). Cada uno con icono + texto, nunca solo color.

## Movimiento y accesibilidad

- Aparición suave (`rise`, 450 ms) y transiciones de indicadores de 800 ms.
- "Reducir animaciones" en Ajustes y respeto de `prefers-reduced-motion`.
- Foco visible en todos los controles; navegación con `aria-current`; selector de modo como `radiogroup`; glosario cerrable con Escape.
- Modo sencillo (por defecto) y avanzado (núcleos, consumo sostenido, consumo propio).
