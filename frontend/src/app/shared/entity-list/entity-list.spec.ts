import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { CrudApi } from '../../core/crud-api';
import { EntityList } from './entity-list';

type Row = { id: string; [k: string]: unknown };

function createWith(rows: Row[], remove?: CrudApi['remove']) {
  // A loose stub: CrudApi.list is generic, so a concrete fake is cast through
  // unknown rather than satisfying the generic signature structurally.
  const api = {
    list: () => of(rows),
    remove: remove ?? (() => of(undefined as void)),
  } as unknown as CrudApi;
  TestBed.configureTestingModule({
    imports: [EntityList],
    providers: [{ provide: CrudApi, useValue: api }],
  });
  const fixture = TestBed.createComponent(EntityList);
  fixture.componentRef.setInput('title', 'LLM-Verbindungen');
  fixture.componentRef.setInput('path', 'llm-connections');
  fixture.componentRef.setInput('columns', [{ key: 'name', label: 'Name' }]);
  fixture.detectChanges();
  return fixture;
}

describe('EntityList', () => {
  it('renders rows returned by the API', () => {
    const fixture = createWith([{ id: '1', name: 'OpenAI' }]);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('OpenAI');
  });

  it('shows an empty state when there are no rows', () => {
    const fixture = createWith([]);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Keine Einträge');
  });

  it('deletes a row through the API path', () => {
    const calls: Array<[string, string]> = [];
    const remove: CrudApi['remove'] = (path, id) => {
      calls.push([path, id]);
      return of(undefined as void);
    };
    const fixture = createWith([{ id: 'a1', name: 'OpenAI' }], remove);
    fixture.componentInstance.delete('a1');
    expect(calls).toEqual([['llm-connections', 'a1']]);
  });
});
