import { FormField, opts } from '../entities';

/** The agent create/edit form schema, rendered by the generic entity-form.
 *
 *  The reference / multi-reference fields are what actually wire an agent to its
 *  LLM connection, tools, skills, data sources and output template — all of
 *  which the run engine already consumes (services/runs.py). Memory and
 *  guardrails are nested objects, edited as JSON. */
export const AGENT_FIELDS: FormField[] = [
  { key: 'name', label: 'label.name', type: 'text', required: true },
  { key: 'role', label: 'agentField.role', type: 'text' },
  { key: 'goal', label: 'agentField.goal', type: 'textarea' },
  { key: 'description', label: 'agentField.description', type: 'textarea' },
  { key: 'instructions', label: 'agentField.instructions', type: 'textarea' },
  {
    key: 'status',
    label: 'agentField.status',
    type: 'select',
    options: opts('draft', 'active', 'disabled'),
    default: 'draft',
  },
  {
    key: 'llm_connection_id',
    label: 'agentField.llm',
    type: 'reference',
    refPath: 'llm-connections',
    refLabel: 'name',
  },
  {
    key: 'tool_ids',
    label: 'agentField.tools',
    type: 'multi-reference',
    refPath: 'tools',
    refLabel: 'name',
  },
  {
    key: 'skill_ids',
    label: 'agentField.skills',
    type: 'multi-reference',
    refPath: 'skills',
    refLabel: 'name',
  },
  {
    key: 'data_source_ids',
    label: 'agentField.dataSources',
    type: 'multi-reference',
    refPath: 'data-sources',
    refLabel: 'name',
  },
  {
    key: 'default_template_id',
    label: 'agentField.template',
    type: 'reference',
    refPath: 'templates',
    refLabel: 'name',
  },
  { key: 'memory', label: 'agentField.memory', type: 'json' },
  { key: 'guardrails', label: 'agentField.guardrails', type: 'json' },
];
