import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE } from './api-base';

const DEV_ROLES_KEY = 'cockpit.devRoles';
const WILDCARD = '*';

interface Me {
  subject: string;
  permissions: string[];
}

/** Holds the current principal's permissions and answers permission checks the
 *  UI gates on.
 *
 *  Permissions load from the backend `/me` at startup (see the app initializer
 *  in app.config). Until then they default to the wildcard, so the first paint
 *  is optimistic and `load()` narrows to the real set once it resolves. In dev,
 *  `X-Dev-Roles` (see dev-roles.interceptor) lets you act as specific roles; an
 *  OIDC token replaces that mechanism when Keycloak lands. */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly permissions = signal<ReadonlySet<string>>(new Set([WILDCARD]));
  private readonly _devRoles = signal(localStorage.getItem(DEV_ROLES_KEY) ?? '');

  /** Comma-separated dev role names sent as X-Dev-Roles (empty = none). */
  readonly devRoles = this._devRoles.asReadonly();

  /** Whether the current principal holds `permission` (the wildcard grants all). */
  has(permission: string): boolean {
    const held = this.permissions();
    return held.has(WILDCARD) || held.has(permission);
  }

  /** Load the current principal from the backend. Called by the app initializer
   *  and again whenever the dev roles change. */
  async load(): Promise<void> {
    try {
      const me = await firstValueFrom(this.http.get<Me>(`${API_BASE}/me`));
      this.permissions.set(new Set(me.permissions));
    } catch {
      // Backend unreachable: deny by default rather than over-permit the UI.
      this.permissions.set(new Set());
    }
  }

  /** Set the dev role names (persisted) and reload the principal. */
  setDevRoles(roles: string): void {
    const trimmed = roles.trim();
    this._devRoles.set(trimmed);
    if (trimmed) {
      localStorage.setItem(DEV_ROLES_KEY, trimmed);
    } else {
      localStorage.removeItem(DEV_ROLES_KEY);
    }
    void this.load();
  }
}
