import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthService } from './auth.service';
import { requirePermission } from './permission.guard';

function runGuard(permission: string) {
  return TestBed.runInInjectionContext(() =>
    requirePermission(permission)({} as never, {} as never),
  );
}

describe('requirePermission', () => {
  it('allows activation when the permission is held', () => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: { has: () => true } as unknown as AuthService },
      ],
    });
    expect(runGuard('agent.create')).toBe(true);
  });

  it('redirects to the start page when the permission is missing', () => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: { has: () => false } as unknown as AuthService },
      ],
    });
    const result = runGuard('agent.create');
    expect(result instanceof UrlTree).toBe(true);
    expect(String(result)).toBe('/');
  });
});
