import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { MetricsSummary, Run } from './run';
import { Runs } from './runs';
import { RunsApi } from './runs-api';

const RUN: Run = {
  id: 'r1',
  agent_id: 'a1',
  status: 'completed',
  result: { content: 'done' },
  metrics: {},
  started_at: '2026-01-01',
  finished_at: '2026-01-01',
  created_at: '',
};

function setup(runs: Run[], summary: MetricsSummary) {
  const api = {
    listRuns: () => of(runs),
    metricsSummary: () => of(summary),
  } as unknown as RunsApi;
  TestBed.configureTestingModule({
    imports: [Runs],
    providers: [{ provide: RunsApi, useValue: api }],
  });
  const fixture = TestBed.createComponent(Runs);
  fixture.detectChanges();
  return fixture.nativeElement as HTMLElement;
}

describe('Runs', () => {
  it('renders the metrics summary and the run history', () => {
    const el = setup([RUN], {
      total_runs: 1,
      by_status: { completed: 1 },
      total_tokens: 5,
      total_cost: 0.01,
    });
    expect(el.textContent).toContain('Runs gesamt: 1');
    expect(el.textContent).toContain('completed');
    expect(el.textContent).toContain('Tokens: 5');
  });

  it('shows an empty state when there are no runs', () => {
    const el = setup([], { total_runs: 0, by_status: {}, total_tokens: 0, total_cost: 0 });
    expect(el.textContent).toContain('Keine Runs');
  });
});
