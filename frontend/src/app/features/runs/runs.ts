import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { forkJoin } from 'rxjs';

import { I18n } from '../../core/i18n';
import { TranslatePipe } from '../../core/translate.pipe';
import { MetricsSummary, Run } from './run';
import { RunsApi } from './runs-api';

/** Observability view: the aggregate metrics summary plus the run history,
    each run expandable to its result. Read-only. */
@Component({
  selector: 'app-runs',
  imports: [MatExpansionModule, MatProgressBarModule, TranslatePipe],
  templateUrl: './runs.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Runs implements OnInit {
  private readonly api = inject(RunsApi);
  private readonly i18n = inject(I18n);

  readonly runs = signal<Run[]>([]);
  readonly summary = signal<MetricsSummary | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    forkJoin([this.api.listRuns(), this.api.metricsSummary()]).subscribe({
      next: ([runs, summary]) => {
        this.runs.set(runs);
        this.summary.set(summary);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(this.i18n.t('runs.loadError'));
        this.loading.set(false);
      },
    });
  }

  result(run: Run): string {
    return JSON.stringify(run.result);
  }

  byStatus(summary: MetricsSummary): string {
    return Object.entries(summary.by_status)
      .map(([status, count]) => `${status}: ${count}`)
      .join(', ');
  }
}
