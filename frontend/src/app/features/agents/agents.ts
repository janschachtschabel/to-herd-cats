import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Agent } from './agent';
import { AgentsApi } from './agents-api';

/** Lists the agents from the backend and creates new ones.

    Zoneless change detection is driven by signal writes, so the API results are
    stored in signals rather than plain fields. */
@Component({
  selector: 'app-agents',
  imports: [FormsModule],
  templateUrl: './agents.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Agents {
  private readonly api = inject(AgentsApi);

  readonly agents = signal<Agent[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  name = '';
  goal = '';

  constructor() {
    this.reload();
  }

  reload(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listAgents().subscribe({
      next: (agents) => {
        this.agents.set(agents);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load agents.');
        this.loading.set(false);
      },
    });
  }

  create(): void {
    const name = this.name.trim();
    if (!name) {
      return;
    }
    this.api.createAgent({ name, goal: this.goal.trim() || undefined }).subscribe({
      next: () => {
        this.name = '';
        this.goal = '';
        this.reload();
      },
      error: () => this.error.set('Failed to create agent.'),
    });
  }
}
