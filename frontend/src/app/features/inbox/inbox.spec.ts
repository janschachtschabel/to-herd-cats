import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { AuthService } from '../../core/auth.service';
import { Inbox } from './inbox';
import { InboxApi } from './inbox-api';
import { InboxItem } from './inbox-item';

const PENDING: InboxItem = {
  id: 'i1',
  run_id: 'r1',
  agent_id: 'a1',
  type: 'approval_request',
  payload: { description_md: 'Approve the draft?' },
  allowed_responses: ['accept', 'reject'],
  status: 'pending',
  response: null,
  created_at: '',
};

function setup(
  items: InboxItem[],
  respondImpl: (id: string, response: unknown) => unknown = () => of({}),
) {
  const api = { list: () => of(items), respond: respondImpl } as unknown as InboxApi;
  TestBed.configureTestingModule({
    imports: [Inbox],
    providers: [
      { provide: InboxApi, useValue: api },
      { provide: AuthService, useValue: { has: () => true } as unknown as AuthService },
    ],
  });
  const fixture = TestBed.createComponent(Inbox);
  fixture.detectChanges();
  return fixture;
}

describe('Inbox', () => {
  it('renders a pending item with its description and allowed actions', () => {
    const text = (setup([PENDING]).nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Approve the draft?');
    expect(text).toContain('accept');
    expect(text).toContain('reject');
  });

  it('shows an empty state when the postbox is empty', () => {
    const text = (setup([]).nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Keine Einträge');
  });

  it('sends the chosen action and any typed content to the API', () => {
    const calls: Array<[string, unknown]> = [];
    const fixture = setup([PENDING], (id, response) => {
      calls.push([id, response]);
      return of({});
    });
    fixture.componentInstance.contents['i1'] = 'Looks good';
    fixture.componentInstance.respond(PENDING, 'accept');
    expect(calls).toEqual([['i1', { action: 'accept', content: 'Looks good' }]]);
  });
});
