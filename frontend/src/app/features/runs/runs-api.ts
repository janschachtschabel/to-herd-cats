import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE } from '../../core/api-base';
import { MetricsSummary, Run } from './run';

/** Read access to runs and the aggregate metrics summary (observability). */
@Injectable({ providedIn: 'root' })
export class RunsApi {
  private readonly http = inject(HttpClient);

  listRuns(): Observable<Run[]> {
    return this.http.get<Run[]>(`${API_BASE}/runs`);
  }

  metricsSummary(): Observable<MetricsSummary> {
    return this.http.get<MetricsSummary>(`${API_BASE}/metrics/summary`);
  }
}
