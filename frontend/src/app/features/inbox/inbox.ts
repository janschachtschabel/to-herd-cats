import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import { AuthService } from '../../core/auth.service';
import { I18n } from '../../core/i18n';
import { TranslatePipe } from '../../core/translate.pipe';
import { InboxApi } from './inbox-api';
import { InboxItem } from './inbox-item';

/** The postbox: human-in-the-loop items with the actions each one allows
    (accept / edit / reject / respond / ignore). Responding resumes the run. */
@Component({
  selector: 'app-inbox',
  imports: [
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressBarModule,
    TranslatePipe,
  ],
  templateUrl: './inbox.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Inbox implements OnInit {
  private readonly api = inject(InboxApi);
  private readonly i18n = inject(I18n);
  protected readonly auth = inject(AuthService);

  readonly items = signal<InboxItem[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  // Optional reply / edited content, keyed by item id.
  contents: Record<string, string> = {};

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.list().subscribe({
      next: (items) => {
        this.items.set(items);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(this.i18n.t('inbox.loadError'));
        this.loading.set(false);
      },
    });
  }

  description(item: InboxItem): string {
    const md = item.payload?.['description_md'];
    return typeof md === 'string' ? md : JSON.stringify(item.payload);
  }

  respond(item: InboxItem, action: string): void {
    const content = this.contents[item.id]?.trim() || undefined;
    this.api.respond(item.id, { action, content }).subscribe({
      next: () => {
        this.contents[item.id] = '';
        this.reload();
      },
      error: () => this.error.set(this.i18n.t('inbox.respondError')),
    });
  }
}
