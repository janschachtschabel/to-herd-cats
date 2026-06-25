import { Routes } from '@angular/router';

import { Agents } from './features/agents/agents';
import { ENTITIES } from './features/entities';
import { EntityList } from './shared/entity-list/entity-list';

// One generic EntityList route per configured entity; its title/path/columns
// are supplied as route data and bound to the component's inputs.
export const routes: Routes = [
  { path: '', component: Agents },
  ...ENTITIES.map((entity) => ({
    path: entity.path,
    component: EntityList,
    data: { title: entity.title, path: entity.path, columns: entity.columns },
  })),
];
