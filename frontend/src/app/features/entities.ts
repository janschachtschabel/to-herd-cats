import { Column } from '../shared/entity-list/entity-list';

export interface SelectOption {
  value: string;
  label: string;
}

/** A create-form field (a small UI schema). Required fields are validated on
    the client and again by the backend on submit.

    ``label`` is an i18n key (resolved via the ``t`` pipe / I18n service against
    core/messages.de.ts), not display text. ``options`` hold backend enum tokens
    shown verbatim, so their labels are literal, not keys. */
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

    ``path`` is both the route path and the REST collection path. ``title`` and
    every column/field ``label`` are i18n keys (see core/messages.de.ts). The
    bespoke key-value Setting is excluded (its own view later); the MCP
    config_schema dynamic form is a follow-up (the backend has no config-value
    field for it). */
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
    title: 'title.llmConnections',
    columns: [
      { key: 'name', label: 'label.name' },
      { key: 'provider_model', label: 'label.model' },
    ],
    fields: [
      { key: 'name', label: 'label.name', type: 'text', required: true },
      { key: 'provider_model', label: 'label.model', type: 'text', required: true },
      { key: 'api_base', label: 'label.apiBase', type: 'text' },
      { key: 'enabled', label: 'label.active', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'mcp-servers',
    title: 'title.mcpServers',
    columns: [
      { key: 'name', label: 'label.name' },
      { key: 'transport', label: 'label.transport' },
    ],
    fields: [
      { key: 'name', label: 'label.name', type: 'text', required: true },
      {
        key: 'transport',
        label: 'label.transport',
        type: 'select',
        required: true,
        options: opts('stdio', 'streamable_http'),
      },
      { key: 'command', label: 'label.command', type: 'text' },
      { key: 'url', label: 'label.url', type: 'text' },
    ],
  },
  {
    path: 'tools',
    title: 'title.tools',
    columns: [
      { key: 'name', label: 'label.name' },
      { key: 'enabled', label: 'label.active' },
    ],
    fields: [
      { key: 'name', label: 'label.name', type: 'text', required: true },
      {
        key: 'type',
        label: 'label.type',
        type: 'select',
        options: opts('mcp', 'http', 'builtin'),
        default: 'mcp',
      },
      {
        key: 'mcp_server_id',
        label: 'label.mcpServer',
        type: 'reference',
        refPath: 'mcp-servers',
        refLabel: 'name',
      },
      { key: 'tool_name', label: 'label.toolName', type: 'text' },
      { key: 'enabled', label: 'label.active', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'data-sources',
    title: 'title.dataSources',
    columns: [
      { key: 'name', label: 'label.name' },
      { key: 'kind', label: 'label.kind' },
    ],
    fields: [
      { key: 'name', label: 'label.name', type: 'text', required: true },
      {
        key: 'kind',
        label: 'label.kind',
        type: 'select',
        required: true,
        options: opts('vector', 'graph', 'relational', 'document', 'wiki'),
      },
      { key: 'enabled', label: 'label.active', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'templates',
    title: 'title.templates',
    columns: [
      { key: 'name', label: 'label.name' },
      { key: 'format', label: 'label.format' },
    ],
    fields: [
      { key: 'name', label: 'label.name', type: 'text', required: true },
      {
        key: 'kind',
        label: 'label.kind',
        type: 'select',
        required: true,
        options: opts('report', 'research', 'comparison'),
      },
      {
        key: 'format',
        label: 'label.format',
        type: 'select',
        options: opts('markdown', 'html', 'pdf', 'docx'),
      },
    ],
  },
  {
    path: 'channels',
    title: 'title.channels',
    columns: [
      { key: 'name', label: 'label.name' },
      { key: 'kind', label: 'label.kind' },
      { key: 'direction', label: 'label.direction' },
    ],
    fields: [
      { key: 'name', label: 'label.name', type: 'text', required: true },
      {
        key: 'kind',
        label: 'label.kind',
        type: 'select',
        required: true,
        options: opts('slack', 'email', 'matrix', 'webhook'),
      },
      {
        key: 'direction',
        label: 'label.direction',
        type: 'select',
        options: opts('in', 'out', 'both'),
        default: 'out',
      },
      { key: 'enabled', label: 'label.active', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'triggers',
    title: 'title.triggers',
    columns: [
      { key: 'mode', label: 'label.mode' },
      { key: 'cron', label: 'label.cron' },
      { key: 'enabled', label: 'label.active' },
    ],
    fields: [
      {
        key: 'agent_id',
        label: 'label.agent',
        type: 'reference',
        refPath: 'agents',
        refLabel: 'name',
        required: true,
      },
      {
        key: 'mode',
        label: 'label.mode',
        type: 'select',
        options: opts('on_demand', 'scheduled', 'event', 'autonomous'),
        required: true,
      },
      { key: 'cron', label: 'label.cronScheduled', type: 'text' },
      { key: 'enabled', label: 'label.active', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'skills',
    title: 'title.skills',
    columns: [
      { key: 'name', label: 'label.name' },
      { key: 'invocation', label: 'label.invocation' },
    ],
    fields: [
      { key: 'name', label: 'label.name', type: 'text', required: true },
      {
        key: 'description',
        label: 'label.skillDescription',
        type: 'text',
        required: true,
      },
      { key: 'instructions', label: 'label.instructions', type: 'textarea' },
      {
        key: 'invocation',
        label: 'label.invocation',
        type: 'select',
        options: opts('model_invoked', 'command', 'both'),
        default: 'model_invoked',
      },
      { key: 'enabled', label: 'label.active', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'roles',
    title: 'title.roles',
    columns: [
      { key: 'name', label: 'label.name' },
      { key: 'description', label: 'label.description' },
    ],
    fields: [
      { key: 'name', label: 'label.name', type: 'text', required: true },
      { key: 'description', label: 'label.description', type: 'text' },
    ],
  },
];
