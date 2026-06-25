import { Routes } from '@angular/router';

import { Agents } from './features/agents/agents';
import { ENTITIES } from './features/entities';
import { Inbox } from './features/inbox/inbox';
import { EntityForm } from './shared/entity-form/entity-form';
import { EntityList } from './shared/entity-list/entity-list';

// Each entity gets a generic list route; entities with a create-form config also
// get a "/new" route. title/path/columns/fields are route data bound to the
// component inputs (withComponentInputBinding).
export const routes: Routes = [
  { path: '', component: Agents },
  { path: 'inbox', component: Inbox },
  ...ENTITIES.flatMap((entity) => {
    const list = {
      path: entity.path,
      component: EntityList,
      data: {
        title: entity.title,
        path: entity.path,
        columns: entity.columns,
        creatable: !!entity.fields,
      },
    };
    if (!entity.fields) {
      return [list];
    }
    return [
      list,
      {
        path: `${entity.path}/new`,
        component: EntityForm,
        data: { title: entity.title, path: entity.path, fields: entity.fields },
      },
    ];
  }),
];
