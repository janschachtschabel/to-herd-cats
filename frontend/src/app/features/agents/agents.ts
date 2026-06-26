import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Router } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { I18n } from '../../core/i18n';
import { TranslatePipe } from '../../core/translate.pipe';
import { Agent } from './agent';
import { AgentsApi } from './agents-api';

/** Lists the agents from the backend, creates new ones, and starts a run.

    Zoneless change detection is driven by signal writes, so the API results are
    stored in signals rather than plain fields. */
@Component({
  selector: 'app-agents',
  imports: [
    FormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatListModule,
    MatProgressBarModule,
    TranslatePipe,
  ],
  templateUrl: './agents.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Agents {
  private readonly api = inject(AgentsApi);
  private readonly router = inject(Router);
  private readonly i18n = inject(I18n);
  protected readonly auth = inject(AuthService);

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
        this.error.set(this.i18n.t('agents.loadError'));
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
      error: () => this.error.set(this.i18n.t('agents.createError')),
    });
  }

  run(agent: Agent): void {
    this.error.set(null);
    this.api.runAgent(agent.id, agent.goal?.trim() || this.i18n.t('agents.defaultGoal')).subscribe({
      next: () => this.router.navigateByUrl('/runs'),
      error: () => this.error.set(this.i18n.t('agents.runError')),
    });
  }
}
