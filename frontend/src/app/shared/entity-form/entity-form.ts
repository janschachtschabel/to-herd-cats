import { ChangeDetectionStrategy, Component, OnInit, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { Router, RouterLink } from '@angular/router';

import { CrudApi } from '../../core/crud-api';
import { FormField } from '../../features/entities';

/** Config-driven create form for a backend collection.

    Renders the entity's ``fields`` and POSTs the assembled payload, then returns
    to the list. Edit (PATCH + pre-fill) and richer field types (foreign-key
    reference, the MCP config_schema) are M7.3b. */
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
  model: Record<string, string | boolean> = {};

  ngOnInit(): void {
    const model: Record<string, string | boolean> = {};
    for (const field of this.fields()) {
      model[field.key] = field.default ?? (field.type === 'checkbox' ? false : '');
    }
    this.model = model;
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
