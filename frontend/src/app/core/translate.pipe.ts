import { Pipe, PipeTransform, inject } from '@angular/core';

import { I18n } from './i18n';

/** `{{ 'some.key' | t }}` - resolves a message key to its localized string.
 *
 * Pure: keys and the message map are stable, so it runs once per key. */
@Pipe({ name: 't' })
export class TranslatePipe implements PipeTransform {
  private readonly i18n = inject(I18n);

  transform(key: string): string {
    return this.i18n.t(key);
  }
}
