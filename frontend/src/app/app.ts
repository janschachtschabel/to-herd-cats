import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatListModule } from '@angular/material/list';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from './core/auth.service';
import { SessionService } from './core/session.service';
import { TranslatePipe } from './core/translate.pipe';
import { ENTITIES } from './features/entities';

@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    MatButtonModule,
    TranslatePipe,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly entities = ENTITIES;
  protected readonly auth = inject(AuthService);
  protected readonly session = inject(SessionService);

  /** Dev affordance: act as the typed role names (sent as X-Dev-Roles). */
  setDevRoles(event: Event): void {
    this.auth.setDevRoles((event.target as HTMLInputElement).value);
  }
}
