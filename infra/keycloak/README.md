# Keycloak (OIDC) for the cockpit — local setup

This runs a local Keycloak and imports a ready-made `cockpit` realm so the
backend can verify real access tokens (M8.3a) and the frontend can log users in
(M8.3b). It is **development only** — see `compose.yml`.

## 1. Start Keycloak

```bash
docker compose -f infra/keycloak/compose.yml up
```

- Realm issuer: `http://localhost:8080/realms/cockpit`
- Admin console: `http://localhost:8080/admin` (`admin` / `admin`)
- Demo user: `demo` / `demo` (realm role `editor`)

The bundled realm (`realm-export.json`) defines:

- a **public PKCE client** `cockpit-frontend` (redirect/web-origin
  `http://localhost:4200`),
- an **audience mapper** that puts `cockpit` into each access token's `aud`
  (this is what the backend checks — keep it in sync with `COCKPIT_OIDC_AUDIENCE`),
- example **realm roles** `admin` / `editor` / `viewer`.

## 2. Point the backend at it

Keycloak asserts **role membership**; the cockpit still owns the
**role → permission** mapping. Turn the dev stub off and enable OIDC:

```bash
# backend/.env (or the process environment)
COCKPIT_AUTH_DEV_MODE=false
COCKPIT_OIDC_ISSUER=http://localhost:8080/realms/cockpit
COCKPIT_OIDC_JWKS_URI=http://localhost:8080/realms/cockpit/protocol/openid-connect/certs
COCKPIT_OIDC_AUDIENCE=cockpit
```

A verified token then becomes the principal; an invalid one is rejected with
401. With `COCKPIT_AUTH_DEV_MODE=true` (the default) and no token, the
`X-Dev-Roles` dev stub still applies — handy when Keycloak isn't running.

## 3. Map the realm roles to permissions

For each Keycloak **realm role** create a cockpit **Role with the same name**
(Roles view, or `POST /roles`) and give it permissions:

| Realm role | Suggested cockpit permissions |
| ---------- | ----------------------------- |
| `admin`    | `*` (everything)              |
| `editor`   | the `*.create` / `*.update` / `*.delete` and `run.create` / `run.approve` it should have |
| `viewer`   | none (read-only)              |

A token whose roles have no matching cockpit Role resolves to no permissions, so
guarded routes return 403 (unknown role names are logged).

## 4. Frontend

The Angular app reads its OIDC config from `window.__OIDC__` at runtime (set it
from a small script in `index.html`, evaluated before the bundle), e.g.:

```html
<script>
  window.__OIDC__ = {
    authority: 'http://localhost:8080/realms/cockpit',
    clientId: 'cockpit-frontend',
  };
</script>
```

When `__OIDC__` is unset the app stays in dev mode (the `X-Dev-Roles` toolbar
input); when set, it logs in against Keycloak and sends the bearer token.
