import { Column } from '../shared/entity-list/entity-list';

/** A backend collection shown as a generic list shell (list + delete).

    ``path`` is both the route path and the REST collection path. Create/edit
    forms are rendered from schema separately (M7.3). The bespoke key-value
    Setting entity is intentionally excluded - it gets its own view later. */
export interface EntityConfig {
  path: string;
  title: string;
  columns: Column[];
}

export const ENTITIES: EntityConfig[] = [
  {
    path: 'llm-connections',
    title: 'LLM-Verbindungen',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'provider_model', label: 'Modell' },
    ],
  },
  {
    path: 'mcp-servers',
    title: 'MCP-Server',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'transport', label: 'Transport' },
    ],
  },
  {
    path: 'tools',
    title: 'Werkzeuge',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'enabled', label: 'Aktiv' },
    ],
  },
  {
    path: 'data-sources',
    title: 'Datenquellen',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'kind', label: 'Art' },
    ],
  },
  {
    path: 'templates',
    title: 'Vorlagen',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'format', label: 'Format' },
    ],
  },
  {
    path: 'channels',
    title: 'Kanäle',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'kind', label: 'Art' },
      { key: 'direction', label: 'Richtung' },
    ],
  },
  {
    path: 'triggers',
    title: 'Trigger',
    columns: [
      { key: 'mode', label: 'Modus' },
      { key: 'cron', label: 'Cron' },
      { key: 'enabled', label: 'Aktiv' },
    ],
  },
  {
    path: 'skills',
    title: 'Skills',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'kind', label: 'Art' },
    ],
  },
  {
    path: 'roles',
    title: 'Rollen',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'description', label: 'Beschreibung' },
    ],
  },
];
