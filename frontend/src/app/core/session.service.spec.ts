import { TestBed } from '@angular/core/testing';

import { SessionService } from './session.service';

// With no window.__OIDC__ (the test/dev default), the session is disabled: the
// library service is never injected and every method is a safe no-op. The
// OIDC-enabled redirect flow is verified manually against a running Keycloak.
describe('SessionService (no OIDC config)', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('is disabled and login/logout/init are safe no-ops', async () => {
    const session = TestBed.inject(SessionService);
    expect(session.oidcEnabled).toBe(false);
    expect(session.authenticated()).toBe(false);
    await session.init();
    session.login();
    session.logout();
    expect(session.authenticated()).toBe(false);
  });
});
