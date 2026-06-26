import { ChangeDetectionStrategy, Component, OnInit, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { Router, RouterLink } from '@angular/router';

import { CrudApi } from '../../core/crud-api';
import { FormField, SelectOption } from '../../features/entities';

/** Config-driven create form for a backend collection.

    Renders the entity's ``fields`` (text / checkbox / select, plus reference
    fields whose options are loaded from a related collection) and POSTs the
    assembled payload, then returns to the list. Edit (PATCH + pre-fill) and the
    MCP config_schema form are the remaining M7.3b pieces. */
@Component({
  selector: 'app-entity-form',
  imports: [
    FormsModule,
    RouterLink,
    MatButtonModule,
    MatCheckboxModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
  ],
  templateUrl: './entity-form.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EntityForm implements OnInit {
  private readonly api = inject(CrudApi);
  private readonly router = inject(Router);

  readonly title = input.required<string>();
  readonly path = input.required<string>();
  readonly fields = input.required<FormField[]>();

  readonly error = signal<string | null>(null);
  // Options for reference fields, loaded from their related collection. Partial:
  // a field's options are absent until its related collection has loaded.
  readonly options = signal<Partial<Record<string, SelectOption[]>>>({});
  model: Record<string, string | boolean> = {};

  ngOnInit(): void {
    const model: Record<string, string | boolean> = {};
    for (const field of this.fields()) {
      model[field.key] = field.default ?? (field.type === 'checkbox' ? false : '');
      if (field.type === 'reference') {
        this.loadOptions(field);
      }
    }
    this.model = model;
  }

  private loadOptions(field: FormField): void {
    if (!field.refPath || !field.refLabel) {
      return;
    }
    const refLabel = field.refLabel;
    this.api.list<Record<string, unknown>>(field.refPath).subscribe({
      next: (rows) => {
        const opts = rows.map((row) => ({
          value: String(row['id']),
          label: String(row[refLabel]),
        }));
        this.options.update((current) => ({ ...current, [field.key]: opts }));
      },
      error: () => this.error.set('Auswahllisten konnten nicht geladen werden.'),
    });
  }

  save(): void {
    this.error.set(null);
    const missing = this.fields().find((field) => field.required && !this.model[field.key]);
    if (missing) {
      this.error.set(`Pflichtfeld fehlt: ${missing.label}`);
      return;
    }
    this.api.create(this.path(), this.buildPayload()).subscribe({
      next: () => this.router.navigateByUrl('/' + this.path()),
      error: () => this.error.set('Speichern fehlgeschlagen.'),
    });
  }

  private buildPayload(): Record<string, unknown> {
    const payload: Record<string, unknown> = {};
    for (const field of this.fields()) {
      const value = this.model[field.key];
      // Omit empty optional text so the backend's defaults apply.
      if (value === '' && !field.required) {
        continue;
      }
      payload[field.key] = value;
    }
    return payload;
  }
}
