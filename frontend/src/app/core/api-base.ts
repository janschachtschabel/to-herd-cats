/** Base URL of the backend control API (the FastAPI app).
 *
 * Defaults to the local dev backend. A deployment can override it at runtime by
 * setting `globalThis.__API_BASE__` (e.g. from a small config script in
 * index.html, evaluated before the app bundle) - so a production build can
 * target any host without rebuilding. */
export const API_BASE =
  (globalThis as { __API_BASE__?: string }).__API_BASE__ ?? 'http://localhost:8000';
