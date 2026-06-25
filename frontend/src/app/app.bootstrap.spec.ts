import { bootstrapApplication } from '@angular/platform-browser';

import { App } from './app';
import { appConfig } from './app.config';

/** Smoke test for the real bootstrap path. The component specs use TestBed
    (which supplies its own change detection), so they never exercise the actual
    appConfig + bootstrapApplication; this does, catching gross config errors a
    component spec would miss. */
describe('application bootstrap', () => {
  it('bootstraps App with appConfig (change detection configured)', async () => {
    document.body.innerHTML = '<app-root></app-root>';
    const ref = await bootstrapApplication(App, appConfig);
    try {
      expect(ref.components.length).toBe(1);
    } finally {
      ref.destroy();
    }
  });
});
