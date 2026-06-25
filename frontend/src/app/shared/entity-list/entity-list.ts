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

import { CrudApi } from '../../core/crud-api';

export interface Column {
  key: string;
  label: string;
}

interface Row {
  id: string;
  [key: string]: unknown;
}

/** Generic list of a backend collection with per-row delete.

    Title, REST path and columns are inputs (bound from the route config), so one
    component serves every simple entity. Create/edit forms are rendered from
    schema separately (M7.3). */
@Component({
  selector: 'app-entity-list',
  imports: [RouterLink, MatButtonModule, MatIconModule, MatProgressBarModule, MatTableModule],
  templateUrl: './entity-list.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EntityList implements OnInit {
  private readonly api = inject(CrudApi);

  readonly title = input.required<string>();
  readonly path = input.required<string>();
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
        this.error.set('Daten konnten nicht geladen werden.');
        this.loading.set(false);
      },
    });
  }

  delete(id: string): void {
    this.api.remove(this.path(), id).subscribe({
      next: () => this.reload(),
      error: () => this.error.set('Löschen fehlgeschlagen.'),
    });
  }
}
