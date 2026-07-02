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
  // ``reference`` selects one related id; ``multi-reference`` selects many (a
  // list of ids, e.g. an agent's tool_ids). Both load options from ``refPath``.
  // ``json`` edits an object/array field as JSON text (parsed on save).
  type: 'text' | 'textarea' | 'checkbox' | 'select' | 'reference' | 'multi-reference' | 'json';
  required?: boolean;
  options?: SelectOption[];
  refPath?: string; // reference: the collection to load options from
  refLabel?: string; // reference: the field on each row to show as its label
  default?: string | boolean;
}

/** An optional per-row action: POST /{path}/{id}/{action}, then reload the list.
    Used e.g. for an MCP server's "discover tools". */
export interface RowAction {
  labelKey: string;
  action: string;
  permission: string;
}

/** A backend collection shown as a generic list shell (list + delete, plus an
    optional per-row ``rowAction``) and, when ``fields`` is set, a config-driven
    create/edit form (reference fields load their options from a related
    collection).

    ``path`` is both the route path and the REST collection path. ``title`` and
    every column/field ``label`` are i18n keys (see core/messages.de.ts). The
    bespoke key-value Setting is excluded (its own view later).

    ``resource`` is the backend permission prefix for this collection (e.g.
    ``tool`` → ``tool.create`` / ``tool.update`` / ``tool.delete``); the list
    and form gate their actions on it. */
export interface EntityConfig {
  path: string;
  resource: string;
  title: string;
  columns: Column[];
  fields?: FormField[];
  rowAction?: RowAction;
}

export function opts(...values: string[]): SelectOption[] {
  return values.map((value) => ({ value, label: value }));
}

export const ENTITIES: EntityConfig[] = [
  {
    path: 'llm-connections',
    resource: 'llm_connection',
    title: 'title.llmConnections',
    columns: [
      { key: 'name', label: 'label.name' },
      { key: 'provider_model', label: 'label.model' },
    ],
    fields: [
      { key: 'name', label: 'label.name', type: 'text', required: true },
      { key: 'provider_model', label: 'label.model', type: 'text', required: true },
      { key: 'api_base', label: 'label.apiBase', type: 'text' },
      { key: 'api_key_ref', label: 'label.apiKeyRef', type: 'text' },
      { key: 'enabled', label: 'label.active', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'mcp-servers',
    resource: 'mcp_server',
    title: 'title.mcpServers',
    rowAction: {
      labelKey: 'action.discover',
      action: 'discover',
      permission: 'mcp_server.discover',
    },
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
      { key: 'credentials_ref', label: 'label.credentialsRef', type: 'text' },
      { key: 'args', label: 'label.args', type: 'json' },
      { key: 'config_schema', label: 'label.configSchema', type: 'json' },
    ],
  },
  {
    path: 'tools',
    resource: 'tool',
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
    resource: 'data_source',
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
      {
        key: 'mcp_server_id',
        label: 'label.mcpServer',
        type: 'reference',
        refPath: 'mcp-servers',
        refLabel: 'name',
      },
      { key: 'embedding_model', label: 'label.embeddingModel', type: 'text' },
      { key: 'collection', label: 'label.collection', type: 'text' },
      { key: 'connection_ref', label: 'label.dataConnection', type: 'json' },
      { key: 'enabled', label: 'label.active', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'templates',
    resource: 'template',
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
      { key: 'render_template', label: 'label.renderTemplate', type: 'textarea' },
      { key: 'output_schema', label: 'label.outputSchema', type: 'json' },
    ],
  },
  {
    path: 'channels',
    resource: 'channel',
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
      {
        key: 'mcp_server_id',
        label: 'label.mcpServer',
        type: 'reference',
        refPath: 'mcp-servers',
        refLabel: 'name',
      },
      { key: 'connection_ref', label: 'label.connectionRef', type: 'text' },
      { key: 'routing', label: 'label.routing', type: 'json' },
      { key: 'enabled', label: 'label.active', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'triggers',
    resource: 'trigger',
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
      { key: 'timezone', label: 'label.timezone', type: 'text' },
      { key: 'enabled', label: 'label.active', type: 'checkbox', default: true },
    ],
  },
  {
    path: 'skills',
    resource: 'skill',
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
    resource: 'role',
    title: 'title.roles',
    columns: [
      { key: 'name', label: 'label.name' },
      { key: 'description', label: 'label.description' },
    ],
    fields: [
      { key: 'name', label: 'label.name', type: 'text', required: true },
      { key: 'description', label: 'label.description', type: 'text' },
      {
        key: 'permissions',
        label: 'label.permissions',
        type: 'multi-reference',
        refPath: 'permissions',
        refLabel: 'name',
      },
    ],
  },
];
