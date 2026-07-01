import { Routes } from '@angular/router';

import { requirePermission } from './core/permission.guard';
import { AGENT_FIELDS } from './features/agents/agent-fields';
import { Agents } from './features/agents/agents';
import { ENTITIES } from './features/entities';
import { Inbox } from './features/inbox/inbox';
import { Runs } from './features/runs/runs';
import { EntityForm } from './shared/entity-form/entity-form';
import { EntityList } from './shared/entity-list/entity-list';

// Each entity gets a generic list route; entities with a create-form config also
// get a "/new" route. title/path/columns/fields are route data bound to the
// component inputs (withComponentInputBinding). Agents keep a bespoke list (with
// the run action) but reuse the generic entity-form for their rich config.
export const routes: Routes = [
  { path: '', redirectTo: 'agents', pathMatch: 'full' },
  { path: 'agents', component: Agents },
  {
    path: 'agents/new',
    component: EntityForm,
    data: { title: 'nav.agents', path: 'agents', fields: AGENT_FIELDS },
    canActivate: [requirePermission('agent.create')],
  },
  {
    path: 'agents/:id/edit',
    component: EntityForm,
    data: { title: 'nav.agents', path: 'agents', fields: AGENT_FIELDS },
    canActivate: [requirePermission('agent.update')],
  },
  { path: 'inbox', component: Inbox },
  { path: 'runs', component: Runs },
  ...ENTITIES.flatMap((entity) => {
    const list = {
      path: entity.path,
      component: EntityList,
      data: {
        title: entity.title,
        path: entity.path,
        resource: entity.resource,
        columns: entity.columns,
        creatable: !!entity.fields,
      },
    };
    if (!entity.fields) {
      return [list];
    }
    const formData = { title: entity.title, path: entity.path, fields: entity.fields };
    return [
      list,
      {
        path: `${entity.path}/new`,
        component: EntityForm,
        data: formData,
        canActivate: [requirePermission(`${entity.resource}.create`)],
      },
      {
        path: `${entity.path}/:id/edit`,
        component: EntityForm,
        data: formData,
        canActivate: [requirePermission(`${entity.resource}.update`)],
      },
    ];
  }),
];
