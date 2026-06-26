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
  type: 'text' | 'textarea' | 'checkbox' | 'select' | 'reference';
  required?: boolean;
  options?: SelectOption[];
  refPath?: string; // reference: the collection to load options from
  refLabel?: string; // reference: the field on each row to show as its label
  default?: string | boolean;
}

/** A backend collection shown as a generic list shell (list + delete) and,
    when ``fields`` is set, a config-driven create/edit form (reference fields
    load their options from a related collection).

    ``path`` is both the route path and the REST collection path. The bespoke
    key-value Setting is excluded (its own view later); the MCP config_schema
    dynamic form is a follow-up (the backend has no config-value field for it). */
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
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      {
        key: 'type',
        label: 'Typ',
        type: 'select',
        options: opts('mcp', 'http', 'builtin'),
        default: 'mcp',
      },
      {
        key: 'mcp_server_id',
        label: 'MCP-Server',
        type: 'reference',
        refPath: 'mcp-servers',
        refLabel: 'name',
      },
      { key: 'tool_name', label: 'Tool-Name am Server', type: 'text' },
      { key: 'enabled', label: 'Aktiv', type: 'checkbox', default: true },
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
    fields: [
      {
        key: 'agent_id',
        label: 'Agent',
        type: 'reference',
        refPath: 'agents',
        refLabel: 'name',
        required: true,
      },
      {
        key: 'mode',
        label: 'Modus',
        type: 'select',
        options: opts('on_demand', 'scheduled', 'event', 'autonomous'),
        required: true,
      },
      { key: 'cron', label: 'Cron (für scheduled)', type: 'text' },
      { key: 'enabled', label: 'Aktiv', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'skills',
    title: 'Skills',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'invocation', label: 'Aufruf' },
    ],
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      {
        key: 'description',
        label: 'Beschreibung (Trigger für progressive disclosure)',
        type: 'text',
        required: true,
      },
      { key: 'instructions', label: 'Anweisungen (SKILL.md-Inhalt)', type: 'textarea' },
      {
        key: 'invocation',
        label: 'Aufruf',
        type: 'select',
        options: opts('model_invoked', 'command', 'both'),
        default: 'model_invoked',
      },
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
