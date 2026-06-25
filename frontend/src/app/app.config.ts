import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter, withComponentInputBinding } from '@angular/router';

import { routes } from './app.routes';

// Angular Material 21 uses CSS-based animations, so no @angular/animations
// provider is needed (the package is intentionally not installed).
// withComponentInputBinding flows route data (title/path/columns) into the
// generic EntityList component's inputs.
export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideHttpClient(),
    provideRouter(routes, withComponentInputBinding()),
  ],
};
