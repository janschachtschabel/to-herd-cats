import { Column } from '../shared/entity-list/entity-list';

export interface SelectOption {
  value: string;
  label: string;
}

/** A create-form field (a small UI schema). Required fields are validated on
    the client and again by the backend on submit. */
export interface FormField {
  key: string;
  label: string;
  type: 'text' | 'checkbox' | 'select';
  required?: boolean;
  options?: SelectOption[];
  default?: string | boolean;
}

/** A backend collection shown as a generic list shell (list + delete) and,
    when ``fields`` is set, a config-driven create form.

    ``path`` is both the route path and the REST collection path. Entities with a
    required foreign key (tools, triggers) and the bespoke key-value Setting are
    excluded for now; their create forms (and the MCP config_schema form) are
    M7.3b. */
export interface EntityConfig {
  path: string;
  title: string;
  columns: Column[];
  fields?: FormField[];
}

function opts(...values: string[]): SelectOption[] {
  return values.map((value) => ({ value, label: value }));
}

export const ENTITIES: EntityConfig[] = [
  {
    path: 'llm-connections',
    title: 'LLM-Verbindungen',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'provider_model', label: 'Modell' },
    ],
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      { key: 'provider_model', label: 'Modell', type: 'text', required: true },
      { key: 'api_base', label: 'API-Basis-URL', type: 'text' },
      { key: 'enabled', label: 'Aktiv', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'mcp-servers',
    title: 'MCP-Server',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'transport', label: 'Transport' },
    ],
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      {
        key: 'transport',
        label: 'Transport',
        type: 'select',
        required: true,
        options: opts('stdio', 'streamable_http'),
      },
      { key: 'command', label: 'Kommando', type: 'text' },
      { key: 'url', label: 'URL', type: 'text' },
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
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      {
        key: 'kind',
        label: 'Art',
        type: 'select',
        required: true,
        options: opts('vector', 'graph', 'relational', 'document', 'wiki'),
      },
      { key: 'enabled', label: 'Aktiv', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'templates',
    title: 'Vorlagen',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'format', label: 'Format' },
    ],
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      {
        key: 'kind',
        label: 'Art',
        type: 'select',
        required: true,
        options: opts('report', 'research', 'comparison'),
      },
      {
        key: 'format',
        label: 'Format',
        type: 'select',
        options: opts('markdown', 'html', 'pdf', 'docx'),
      },
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
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      {
        key: 'kind',
        label: 'Art',
        type: 'select',
        required: true,
        options: opts('slack', 'email', 'matrix', 'webhook'),
      },
      {
        key: 'direction',
        label: 'Richtung',
        type: 'select',
        options: opts('in', 'out', 'both'),
        default: 'out',
      },
      { key: 'enabled', label: 'Aktiv', type: 'checkbox', default: true },
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
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      { key: 'description', label: 'Beschreibung', type: 'text', required: true },
      { key: 'kind', label: 'Art', type: 'text' },
      { key: 'enabled', label: 'Aktiv', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'roles',
    title: 'Rollen',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'description', label: 'Beschreibung' },
    ],
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      { key: 'description', label: 'Beschreibung', type: 'text' },
    ],
  },
];
