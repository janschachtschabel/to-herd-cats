import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE } from './api-base';

/** Generic list + delete against a REST collection on the backend.

    Used by the entity-list shells. Create/edit forms are rendered from schema
    separately (M7.3), so only the operations every collection shares live here. */
@Injectable({ providedIn: 'root' })
export class CrudApi {
  private readonly http = inject(HttpClient);

  list<T>(path: string): Observable<T[]> {
    return this.http.get<T[]>(`${API_BASE}/${path}`);
  }

  remove(path: string, id: string): Observable<void> {
    return this.http.delete<void>(`${API_BASE}/${path}/${id}`);
  }

  create<T>(path: string, payload: unknown): Observable<T> {
    return this.http.post<T>(`${API_BASE}/${path}`, payload);
  }

  get<T>(path: string, id: string): Observable<T> {
    return this.http.get<T>(`${API_BASE}/${path}/${id}`);
  }

  update<T>(path: string, id: string, payload: unknown): Observable<T> {
    return this.http.patch<T>(`${API_BASE}/${path}/${id}`, payload);
  }
}
