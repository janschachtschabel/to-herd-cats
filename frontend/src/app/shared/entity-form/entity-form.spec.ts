import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { CrudApi } from '../../core/crud-api';
import { FormField } from '../../features/entities';
import { EntityForm } from './entity-form';

const FIELDS: FormField[] = [
  { key: 'name', label: 'Name', type: 'text', required: true },
  { key: 'enabled', label: 'Aktiv', type: 'checkbox', default: true },
];

function setup(createImpl: (path: string, payload: unknown) => unknown = () => of({})) {
  // provideRouter gives the full router context RouterLink needs; CrudApi.create
  // is generic, so the fake is cast through unknown.
  const api = { create: createImpl } as unknown as CrudApi;
  TestBed.configureTestingModule({
    imports: [EntityForm],
    providers: [{ provide: CrudApi, useValue: api }, provideRouter([])],
  });
  const fixture = TestBed.createComponent(EntityForm);
  const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
  fixture.componentRef.setInput('title', 'Rollen');
  fixture.componentRef.setInput('path', 'roles');
  fixture.componentRef.setInput('fields', FIELDS);
  fixture.detectChanges();
  return { fixture, navigate };
}

describe('EntityForm', () => {
  it('seeds the model from field defaults', () => {
    const { fixture } = setup();
    expect(fixture.componentInstance.model).toEqual({ name: '', enabled: true });
  });

  it('posts the assembled payload and returns to the list', () => {
    const created: Array<[string, unknown]> = [];
    const { fixture, navigate } = setup((path, payload) => {
      created.push([path, payload]);
      return of({});
    });
    fixture.componentInstance.model = { name: 'Editor', enabled: true };
    fixture.componentInstance.save();
    expect(created).toEqual([['roles', { name: 'Editor', enabled: true }]]);
    expect(navigate).toHaveBeenCalledWith('/roles');
  });

  it('blocks submit when a required field is empty', () => {
    const created: unknown[] = [];
    const { fixture } = setup((path, payload) => {
      created.push([path, payload]);
      return of({});
    });
    fixture.componentInstance.model = { name: '', enabled: true };
    fixture.componentInstance.save();
    expect(created).toEqual([]);
    expect(fixture.componentInstance.error()).toContain('Pflichtfeld');
  });
});
