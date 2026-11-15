# Interfaz de ScriptLens IA

React 19 + TypeScript + Tailwind CSS 4, servida por Vite y empaquetada por Tauri.

| Carpeta | Contenido |
|---|---|
| `src/lib/` | Cliente de la API (`api.ts`), formato de unidades, preferencias, glosario, consulta periódica que se pausa con la ventana oculta |
| `src/components/` | Sistema de diseño: `Card`, `Stat`, `Gauge`, `TimeChart`, `Term`, `Onboarding`, `Shell` (barra lateral, barra superior, pie) |
| `src/pages/` | Panel general, Ajustes, Acerca de y marcadores honestos de módulos en desarrollo |

Comandos: `npm run dev` (puerto 1420) · `npm run build` (tipos + compilación) · `npx oxlint`.
