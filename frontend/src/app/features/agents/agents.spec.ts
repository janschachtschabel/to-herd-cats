import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { Agent } from './agent';
import { Agents } from './agents';
import { AgentsApi } from './agents-api';

function setup(agents: Agent[]) {
  const api: Partial<AgentsApi> = {
    listAgents: () => of(agents),
    createAgent: () => of({} as Agent),
  };
  TestBed.configureTestingModule({
    imports: [Agents],
    providers: [{ provide: AgentsApi, useValue: api }],
  });
  const fixture = TestBed.createComponent(Agents);
  fixture.detectChanges();
  return fixture.nativeElement as HTMLElement;
}

describe('Agents', () => {
  it('renders agents returned by the API', () => {
    const el = setup([
      { id: '1', name: 'Researcher', status: 'active', goal: 'find things', created_at: '' },
    ]);
    expect(el.textContent).toContain('Researcher');
    expect(el.textContent).toContain('active');
    expect(el.textContent).toContain('find things');
  });

  it('shows an empty state when there are no agents', () => {
    const el = setup([]);
    expect(el.textContent).toContain('Noch keine Agenten');
  });
});
