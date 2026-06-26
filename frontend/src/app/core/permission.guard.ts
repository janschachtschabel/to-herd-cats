import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

/** Route guard factory: allow activation only if the principal holds
 *  `permission`, otherwise redirect to the start page. */
export function requirePermission(permission: string): CanActivateFn {
  return () => {
    const auth = inject(AuthService);
    return auth.has(permission) ? true : inject(Router).parseUrl('/');
  };
}
