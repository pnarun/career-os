/**
 * `true` for `npm run dev` / Vite dev server. Debug-only UI (Jobs debug summary, etc.) uses this.
 * Production builds (`npm run build`) set this to `false`.
 */
export const isDevBuild = import.meta.env.DEV
