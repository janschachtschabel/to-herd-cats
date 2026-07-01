import { ChangeDetectionStrategy, Component, OnInit, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { Router, RouterLink } from '@angular/router';

import { CrudApi } from '../../core/crud-api';
import { I18n } from '../../core/i18n';
import { TranslatePipe } from '../../core/translate.pipe';
import { FormField, SelectOption } from '../../features/entities';

/** Config-driven create or edit form for a backend collection.

    Renders the entity's ``fields`` (text / textarea / checkbox / select, plus
    single- and multi-reference fields whose options load from a related
    collection — the latter for id lists such as an agent's tool_ids). With an
    ``id`` it pre-fills from the existing entity and PATCHes on save; otherwise
    it POSTs a new one. */
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
    TranslatePipe,
  ],
  templateUrl: './entity-form.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EntityForm implements OnInit {
  private readonly api = inject(CrudApi);
  private readonly router = inject(Router);
  private readonly i18n = inject(I18n);

  readonly title = input.required<string>();
  readonly path = input.required<string>();
  readonly fields = input.required<FormField[]>();
  // Set in edit mode (bound from the route ":id" param); empty means create.
  readonly id = input<string>('');

  readonly error = signal<string | null>(null);
  // Options for reference fields, loaded from their related collection. Partial:
  // a field's options are absent until its related collection has loaded.
  readonly options = signal<Partial<Record<string, SelectOption[]>>>({});
  // A field's value: text/select -> string, checkbox -> boolean, multi-reference
  // -> a list of ids.
  model: Record<string, string | boolean | string[]> = {};

  ngOnInit(): void {
    const model: Record<string, string | boolean | string[]> = {};
    for (const field of this.fields()) {
      model[field.key] =
        field.type === 'multi-reference'
          ? []
          : (field.default ?? (field.type === 'checkbox' ? false : ''));
      if (field.type === 'reference' || field.type === 'multi-reference') {
        this.loadOptions(field);
      }
    }
    this.model = model;
    if (this.id()) {
      this.loadEntity();
    }
  }

  private loadEntity(): void {
    this.api.get<Record<string, unknown>>(this.path(), this.id()).subscribe({
      next: (entity) => {
        const model = { ...this.model };
        for (const field of this.fields()) {
          const value = entity[field.key];
          if (value !== null && value !== undefined) {
            model[field.key] = value as string | boolean | string[];
          }
        }
        this.model = model;
      },
      error: () => this.error.set(this.i18n.t('form.loadError')),
    });
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
      error: () => this.error.set(this.i18n.t('form.optionsError')),
    });
  }

  save(): void {
    this.error.set(null);
    const missing = this.fields().find((field) => field.required && !this.model[field.key]);
    if (missing) {
      this.error.set(this.i18n.t('form.requiredMissing') + ': ' + this.i18n.t(missing.label));
      return;
    }
    const id = this.id();
    const request = id
      ? this.api.update(this.path(), id, this.buildPayload())
      : this.api.create(this.path(), this.buildPayload());
    request.subscribe({
      next: () => this.router.navigateByUrl('/' + this.path()),
      error: () => this.error.set(this.i18n.t('form.saveError')),
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
