/** OIDC runtime config, read from `window.__OIDC__` (set by a small script in
 *  index.html, evaluated before the app bundle — like API_BASE). Null means OIDC
 *  is disabled and the dev stub (X-Dev-Roles) applies. See
 *  infra/keycloak/README.md. */
export interface OidcConfig {
  authority: string;
  clientId: string;
}

export const OIDC_CONFIG: OidcConfig | null =
  (globalThis as { __OIDC__?: OidcConfig }).__OIDC__ ?? null;
