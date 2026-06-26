import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
  provideZonelessChangeDetection,
} from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter, withComponentInputBinding } from '@angular/router';

import { AuthService } from './core/auth.service';
import { devRolesInterceptor } from './core/dev-roles.interceptor';
import { routes } from './app.routes';

// Zoneless change detection (no zone.js) is required for the app to bootstrap -
// the scaffold ships without zone.js, so without this provider Angular errors at
// startup. Material 21 uses CSS-based animations, so no @angular/animations
// provider is needed. withComponentInputBinding flows route data
// (title/path/columns) into the generic EntityList component's inputs.
export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    provideHttpClient(withInterceptors([devRolesInterceptor])),
    provideRouter(routes, withComponentInputBinding()),
    // Load the current principal's permissions before the app renders, so route
    // guards and action gating have them on first paint.
    provideAppInitializer(() => inject(AuthService).load()),
  ],
};
