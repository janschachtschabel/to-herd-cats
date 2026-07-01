import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE } from '../../core/api-base';
import { Agent } from './agent';

/** Data access for the agents list + run. Create/edit go through the generic
    CrudApi via the entity-form, so no create/update lives here. */
@Injectable({ providedIn: 'root' })
export class AgentsApi {
  private readonly http = inject(HttpClient);

  listAgents(): Observable<Agent[]> {
    return this.http.get<Agent[]>(`${API_BASE}/agents`);
  }

  runAgent(agentId: string, goal: string): Observable<unknown> {
    return this.http.post(`${API_BASE}/agents/${agentId}/runs`, { goal });
  }
}
