import { Injectable } from '@angular/core';

import { MESSAGES_DE } from './messages.de';

/** Minimal in-house i18n. One locale (German) for now; a second locale is just
 *  another message map selected here. Swappable for a full i18n library later
 *  behind the same `t` interface. */
@Injectable({ providedIn: 'root' })
export class I18n {
  private readonly messages = MESSAGES_DE;

  /** Translate a key; falls back to the key itself when it is not defined. */
  t(key: string): string {
    return this.messages[key] ?? key;
  }
}
