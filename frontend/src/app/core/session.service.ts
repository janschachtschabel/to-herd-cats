import { Injectable, inject, signal } from '@angular/core';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { firstValueFrom } from 'rxjs';

import { OIDC_CONFIG } from './oidc-config';

/** Wraps the OIDC session so the rest of the app needn't know whether real auth
 *  is active.
 *
 *  With OIDC configured it drives login/logout and tracks the authenticated
 *  state; the library's interceptor attaches the bearer token to API calls.
 *  Without it (dev) everything is a no-op and the X-Dev-Roles stub applies — the
 *  library service is not even injected, so no auth config is required. */
@Injectable({ providedIn: 'root' })
export class SessionService {
  // Only touch the library's provider when OIDC is actually configured.
  private readonly oidc = OIDC_CONFIG ? inject(OidcSecurityService) : null;
  readonly oidcEnabled = OIDC_CONFIG !== null;

  private readonly _authenticated = signal(false);
  readonly authenticated = this._authenticated.asReadonly();

  /** Process the OIDC callback / restore the session. No-op without OIDC. */
  async init(): Promise<void> {
    if (!this.oidc) {
      return;
    }
    this.oidc.isAuthenticated$.subscribe((result) =>
      this._authenticated.set(result.isAuthenticated),
    );
    await firstValueFrom(this.oidc.checkAuth());
  }

  login(): void {
    this.oidc?.authorize();
  }

  logout(): void {
    this.oidc?.logoff().subscribe();
  }
}
