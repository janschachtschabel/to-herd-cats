import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { API_BASE } from './api-base';
import { AuthService } from './auth.service';

/** Attach the X-Dev-Roles header to backend requests when dev roles are set, so
 *  the dev auth stub can resolve a non-admin principal. Scoped to API_BASE so it
 *  never leaks onto third-party requests. Replaced by the OIDC bearer token when
 *  Keycloak lands. */
export const devRolesInterceptor: HttpInterceptorFn = (req, next) => {
  if (req.url.startsWith(API_BASE)) {
    const roles = inject(AuthService).devRoles();
    if (roles) {
      return next(req.clone({ setHeaders: { 'X-Dev-Roles': roles } }));
    }
  }
  return next(req);
};
