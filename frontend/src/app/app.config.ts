import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
  provideZonelessChangeDetection,
} from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { authInterceptor, provideAuth } from 'angular-auth-oidc-client';

import { API_BASE } from './core/api-base';
import { AuthService } from './core/auth.service';
import { devRolesInterceptor } from './core/dev-roles.interceptor';
import { OIDC_CONFIG } from './core/oidc-config';
import { SessionService } from './core/session.service';
import { routes } from './app.routes';

// OIDC is wired only when configured at runtime (window.__OIDC__); otherwise the
// app runs on the dev stub. provideAuth supplies the library service and its
// interceptor attaches the bearer token to API_BASE calls (secureRoutes).
const oidcProviders = OIDC_CONFIG
  ? [
      provideAuth({
        config: {
          authority: OIDC_CONFIG.authority,
          clientId: OIDC_CONFIG.clientId,
          redirectUrl: window.location.origin,
          postLogoutRedirectUri: window.location.origin,
          scope: 'openid profile email',
          responseType: 'code',
          silentRenew: true,
          useRefreshToken: true,
          secureRoutes: [API_BASE],
        },
      }),
    ]
  : [];

// Zoneless change detection (no zone.js) is required for the app to bootstrap -
// the scaffold ships without zone.js, so without this provider Angular errors at
// startup. Material 21 uses CSS-based animations, so no @angular/animations
// provider is needed. withComponentInputBinding flows route data
// (title/path/columns) into the generic EntityList component's inputs.
export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    provideHttpClient(
      withInterceptors([devRolesInterceptor, ...(OIDC_CONFIG ? [authInterceptor()] : [])]),
    ),
    ...oidcProviders,
    provideRouter(routes, withComponentInputBinding()),
    // Establish the session (process any OIDC callback) and load the principal's
    // permissions before the app renders, so guards and gating have them on
    // first paint.
    provideAppInitializer(() => {
      // Inject synchronously (the injection context ends at the first await),
      // then establish the session before loading the principal.
      const session = inject(SessionService);
      const auth = inject(AuthService);
      return session.init().then(() => auth.load());
    }),
  ],
};
