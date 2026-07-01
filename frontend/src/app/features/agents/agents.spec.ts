import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { AuthService } from '../../core/auth.service';
import { I18n } from '../../core/i18n';
import { Agent } from './agent';
import { Agents } from './agents';
import { AgentsApi } from './agents-api';

function setup(agents: Agent[], extra: Partial<AgentsApi> = {}) {
  const api: Partial<AgentsApi> = {
    listAgents: () => of(agents),
    runAgent: () => of({}),
    ...extra,
  };
  TestBed.configureTestingModule({
    imports: [Agents],
    providers: [
      { provide: AgentsApi, useValue: api },
      { provide: AuthService, useValue: { has: () => true } as unknown as AuthService },
      provideRouter([]),
    ],
  });
  const fixture = TestBed.createComponent(Agents);
  fixture.detectChanges();
  return fixture;
}

describe('Agents', () => {
  it('renders agents returned by the API', () => {
    const el = setup([
      { id: '1', name: 'Researcher', status: 'active', goal: 'find things', created_at: '' },
    ]).nativeElement as HTMLElement;
    expect(el.textContent).toContain('Researcher');
    expect(el.textContent).toContain('active');
    expect(el.textContent).toContain('find things');
  });

  it('shows an empty state when there are no agents', () => {
    const el = setup([]).nativeElement as HTMLElement;
    expect(el.textContent).toContain('Noch keine Agenten');
  });

  it('links to the create form and each agent edit form', () => {
    const el = setup([{ id: 'a1', name: 'R', status: 'active', goal: '', created_at: '' }])
      .nativeElement as HTMLElement;
    const hrefs = Array.from(el.querySelectorAll('a')).map((a) => a.getAttribute('href'));
    expect(hrefs).toContain('/agents/new');
    expect(hrefs).toContain('/agents/a1/edit');
  });

  it('starts a run with the agent goal and navigates to the runs view', () => {
    const calls: Array<[string, string]> = [];
    const fixture = setup([], {
      runAgent: (id: string, goal: string) => {
        calls.push([id, goal]);
        return of({});
      },
    });
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    fixture.componentInstance.run({
      id: 'a1',
      name: 'R',
      status: 'active',
      goal: 'do x',
      created_at: '',
    });
    expect(calls).toEqual([['a1', 'do x']]);
    expect(navigate).toHaveBeenCalledWith('/runs');
  });

  it('falls back to the configured default goal when the agent has none', () => {
    const calls: Array<[string, string]> = [];
    const fixture = setup([], {
      runAgent: (id: string, goal: string) => {
        calls.push([id, goal]);
        return of({});
      },
    });
    vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    const defaultGoal = TestBed.inject(I18n).t('agents.defaultGoal');
    fixture.componentInstance.run({
      id: 'a2',
      name: 'R',
      status: 'active',
      goal: '',
      created_at: '',
    });
    expect(calls).toEqual([['a2', defaultGoal]]);
  });
});
