import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  input,
  signal,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableModule } from '@angular/material/table';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { CrudApi } from '../../core/crud-api';
import { I18n } from '../../core/i18n';
import { TranslatePipe } from '../../core/translate.pipe';

export interface Column {
  key: string;
  label: string;
}

interface Row {
  id: string;
  [key: string]: unknown;
}

/** Generic list of a backend collection with per-row edit/delete.

    Title, REST path and columns are inputs (bound from the route config), so one
    component serves every simple entity. Create/edit forms are rendered from
    schema separately (entity-form). */
@Component({
  selector: 'app-entity-list',
  imports: [
    RouterLink,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTableModule,
    TranslatePipe,
  ],
  templateUrl: './entity-list.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EntityList implements OnInit {
  private readonly api = inject(CrudApi);
  private readonly i18n = inject(I18n);
  protected readonly auth = inject(AuthService);

  readonly title = input.required<string>();
  readonly path = input.required<string>();
  // Permission resource prefix (e.g. "tool"); empty when unset (gates open).
  readonly resource = input('');
  readonly columns = input.required<Column[]>();
  readonly creatable = input(false);

  readonly rows = signal<Row[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  readonly displayedColumns = computed(() => [...this.columns().map((c) => c.key), 'actions']);

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.list<Row>(this.path()).subscribe({
      next: (rows) => {
        this.rows.set(rows);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(this.i18n.t('list.loadError'));
        this.loading.set(false);
      },
    });
  }

  delete(id: string): void {
    this.api.remove(this.path(), id).subscribe({
      next: () => this.reload(),
      error: () => this.error.set(this.i18n.t('list.deleteError')),
    });
  }
}
