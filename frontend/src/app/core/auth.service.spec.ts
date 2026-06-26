import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { API_BASE } from './api-base';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('permits everything before load (optimistic wildcard)', () => {
    expect(service.has('agent.create')).toBe(true);
  });

  it('narrows permissions from /me on load', async () => {
    const loaded = service.load();
    httpMock.expectOne(`${API_BASE}/me`).flush({ subject: 'dev:x', permissions: ['agent.create'] });
    await loaded;
    expect(service.has('agent.create')).toBe(true);
    expect(service.has('agent.delete')).toBe(false);
  });

  it('honors the wildcard from /me', async () => {
    const loaded = service.load();
    httpMock.expectOne(`${API_BASE}/me`).flush({ subject: 'dev-admin', permissions: ['*'] });
    await loaded;
    expect(service.has('anything')).toBe(true);
  });

  it('denies by default when /me fails', async () => {
    const loaded = service.load();
    httpMock.expectOne(`${API_BASE}/me`).error(new ProgressEvent('network'));
    await loaded;
    expect(service.has('agent.create')).toBe(false);
  });

  it('persists dev roles and reloads the principal', async () => {
    service.setDevRoles('editor');
    expect(service.devRoles()).toBe('editor');
    expect(localStorage.getItem('cockpit.devRoles')).toBe('editor');
    httpMock.expectOne(`${API_BASE}/me`).flush({ subject: 'dev:editor', permissions: [] });
  });

  it('clears dev roles when set to empty', () => {
    localStorage.setItem('cockpit.devRoles', 'editor');
    service.setDevRoles('');
    expect(service.devRoles()).toBe('');
    expect(localStorage.getItem('cockpit.devRoles')).toBeNull();
    httpMock.expectOne(`${API_BASE}/me`).flush({ subject: 'dev-admin', permissions: ['*'] });
  });
});
