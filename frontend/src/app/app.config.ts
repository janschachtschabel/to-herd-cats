import {
  ApplicationConfig,
  provideBrowserGlobalErrorListeners,
  provideZonelessChangeDetection,
} from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter, withComponentInputBinding } from '@angular/router';

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
    provideHttpClient(),
    provideRouter(routes, withComponentInputBinding()),
  ],
};
