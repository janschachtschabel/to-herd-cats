import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE } from '../../core/api-base';
import { Agent, AgentCreate } from './agent';

/** Data access for agents against the backend control API. */
@Injectable({ providedIn: 'root' })
export class AgentsApi {
  private readonly http = inject(HttpClient);

  listAgents(): Observable<Agent[]> {
    return this.http.get<Agent[]>(`${API_BASE}/agents`);
  }

  createAgent(payload: AgentCreate): Observable<Agent> {
    return this.http.post<Agent>(`${API_BASE}/agents`, payload);
  }
}
