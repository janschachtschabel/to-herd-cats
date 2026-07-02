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

  it('loads reference-field options from the related collection', () => {
    const api = {
      create: () => of({}),
      list: () => of([{ id: 's1', name: 'GitHub MCP' }]),
    } as unknown as CrudApi;
    TestBed.configureTestingModule({
      imports: [EntityForm],
      providers: [{ provide: CrudApi, useValue: api }, provideRouter([])],
    });
    const fixture = TestBed.createComponent(EntityForm);
    fixture.componentRef.setInput('title', 'Werkzeuge');
    fixture.componentRef.setInput('path', 'tools');
    fixture.componentRef.setInput('fields', [
      {
        key: 'mcp_server_id',
        label: 'MCP-Server',
        type: 'reference',
        refPath: 'mcp-servers',
        refLabel: 'name',
      },
    ]);
    fixture.detectChanges();
    expect(fixture.componentInstance.options()['mcp_server_id']).toEqual([
      { value: 's1', label: 'GitHub MCP' },
    ]);
  });

  it('loads options for a multi-reference field and submits the selected ids', () => {
    const created: Array<[string, unknown]> = [];
    const api = {
      create: (path: string, payload: unknown) => {
        created.push([path, payload]);
        return of({});
      },
      list: () =>
        of([
          { id: 't1', name: 'Search' },
          { id: 't2', name: 'Fetch' },
        ]),
    } as unknown as CrudApi;
    TestBed.configureTestingModule({
      imports: [EntityForm],
      providers: [{ provide: CrudApi, useValue: api }, provideRouter([])],
    });
    const fixture = TestBed.createComponent(EntityForm);
    fixture.componentRef.setInput('title', 'Agenten');
    fixture.componentRef.setInput('path', 'agents');
    fixture.componentRef.setInput('fields', [
      {
        key: 'tool_ids',
        label: 'Werkzeuge',
        type: 'multi-reference',
        refPath: 'tools',
        refLabel: 'name',
      },
    ]);
    fixture.detectChanges();
    vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);

    expect(fixture.componentInstance.options()['tool_ids']).toEqual([
      { value: 't1', label: 'Search' },
      { value: 't2', label: 'Fetch' },
    ]);
    expect(fixture.componentInstance.model['tool_ids']).toEqual([]);

    fixture.componentInstance.model = { tool_ids: ['t1', 't2'] };
    fixture.componentInstance.save();
    expect(created).toEqual([['agents', { tool_ids: ['t1', 't2'] }]]);
  });

  it('parses a json field on save and rejects invalid json', () => {
    const created: Array<[string, unknown]> = [];
    const api = {
      create: (path: string, payload: unknown) => {
        created.push([path, payload]);
        return of({});
      },
    } as unknown as CrudApi;
    TestBed.configureTestingModule({
      imports: [EntityForm],
      providers: [{ provide: CrudApi, useValue: api }, provideRouter([])],
    });
    const fixture = TestBed.createComponent(EntityForm);
    fixture.componentRef.setInput('title', 'Vorlagen');
    fixture.componentRef.setInput('path', 'templates');
    fixture.componentRef.setInput('fields', [
      { key: 'output_schema', label: 'Schema', type: 'json' },
    ]);
    fixture.detectChanges();
    vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);

    // valid json is parsed into an object
    fixture.componentInstance.model = { output_schema: '{"a": 1}' };
    fixture.componentInstance.save();
    expect(created).toEqual([['templates', { output_schema: { a: 1 } }]]);

    // invalid json blocks the submit and reports the error
    created.length = 0;
    fixture.componentInstance.model = { output_schema: '{bad' };
    fixture.componentInstance.save();
    expect(created).toEqual([]);
    expect(fixture.componentInstance.error()).toContain('JSON');
  });

  it('pre-fills from the entity and PATCHes on save in edit mode', () => {
    const updated: Array<[string, string, unknown]> = [];
    const api = {
      get: () => of({ name: 'Existing', enabled: false }),
      update: (path: string, id: string, payload: unknown) => {
        updated.push([path, id, payload]);
        return of({});
      },
    } as unknown as CrudApi;
    TestBed.configureTestingModule({
      imports: [EntityForm],
      providers: [{ provide: CrudApi, useValue: api }, provideRouter([])],
    });
    const fixture = TestBed.createComponent(EntityForm);
    fixture.componentRef.setInput('title', 'Rollen');
    fixture.componentRef.setInput('path', 'roles');
    fixture.componentRef.setInput('fields', FIELDS);
    fixture.componentRef.setInput('id', 'r1');
    fixture.detectChanges();
    vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);

    expect(fixture.componentInstance.model).toEqual({ name: 'Existing', enabled: false });
    fixture.componentInstance.save();
    expect(updated).toEqual([['roles', 'r1', { name: 'Existing', enabled: false }]]);
  });

  it('renders a textarea field and submits its value', () => {
    const created: Array<[string, unknown]> = [];
    const api = {
      create: (path: string, payload: unknown) => {
        created.push([path, payload]);
        return of({});
      },
    } as unknown as CrudApi;
    TestBed.configureTestingModule({
      imports: [EntityForm],
      providers: [{ provide: CrudApi, useValue: api }, provideRouter([])],
    });
    const fixture = TestBed.createComponent(EntityForm);
    fixture.componentRef.setInput('title', 'Skills');
    fixture.componentRef.setInput('path', 'skills');
    fixture.componentRef.setInput('fields', [
      { key: 'instructions', label: 'Anweisungen', type: 'textarea' },
    ]);
    fixture.detectChanges();
    vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);

    expect((fixture.nativeElement as HTMLElement).querySelector('textarea')).toBeTruthy();
    fixture.componentInstance.model = { instructions: '# How to' };
    fixture.componentInstance.save();
    expect(created).toEqual([['skills', { instructions: '# How to' }]]);
  });
});
