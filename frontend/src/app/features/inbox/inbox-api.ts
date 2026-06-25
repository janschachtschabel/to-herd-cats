import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE } from '../../core/api-base';
import { InboxItem, InboxResponse } from './inbox-item';

/** Data access for the postbox: list items and respond (resumes the run). */
@Injectable({ providedIn: 'root' })
export class InboxApi {
  private readonly http = inject(HttpClient);

  list(): Observable<InboxItem[]> {
    return this.http.get<InboxItem[]>(`${API_BASE}/inbox`);
  }

  respond(id: string, response: InboxResponse): Observable<unknown> {
    return this.http.post(`${API_BASE}/inbox/${id}/respond`, response);
  }
}
