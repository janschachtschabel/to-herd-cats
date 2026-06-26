"""The permission catalog: the authorization vocabulary the API enforces.

Permissions are ``<resource>.<action>`` strings stored on roles
(``Role.permissions``) and checked by the guards in ``app.api.security``. Every
constant here guards a real mutating endpoint; reads are unguarded in this
phase. ``WILDCARD`` is the "all permissions" marker an admin role (and the
dev-admin fallback) carries.

Convention: CRUD endpoints use ``create`` / ``update`` / ``delete``; a named
sub-action (``POST /{id}/<verb>``) uses that verb, so execution actions stay
separable from configuration (e.g. ``trigger.fire`` apart from
``trigger.update``).
"""

WILDCARD = "*"


class Permission:
    """Named permission strings (see module docstring)."""

    AGENT_CREATE = "agent.create"
    AGENT_UPDATE = "agent.update"
    AGENT_DELETE = "agent.delete"

    LLM_CONNECTION_CREATE = "llm_connection.create"
    LLM_CONNECTION_UPDATE = "llm_connection.update"
    LLM_CONNECTION_DELETE = "llm_connection.delete"

    SKILL_CREATE = "skill.create"
    SKILL_UPDATE = "skill.update"
    SKILL_DELETE = "skill.delete"

    MCP_SERVER_CREATE = "mcp_server.create"
    MCP_SERVER_UPDATE = "mcp_server.update"
    MCP_SERVER_DELETE = "mcp_server.delete"
    MCP_SERVER_DISCOVER = "mcp_server.discover"

    TOOL_CREATE = "tool.create"
    TOOL_UPDATE = "tool.update"
    TOOL_DELETE = "tool.delete"

    DATA_SOURCE_CREATE = "data_source.create"
    DATA_SOURCE_UPDATE = "data_source.update"
    DATA_SOURCE_DELETE = "data_source.delete"

    TEMPLATE_CREATE = "template.create"
    TEMPLATE_UPDATE = "template.update"
    TEMPLATE_DELETE = "template.delete"

    CHANNEL_CREATE = "channel.create"
    CHANNEL_UPDATE = "channel.update"
    CHANNEL_DELETE = "channel.delete"

    TRIGGER_CREATE = "trigger.create"
    TRIGGER_UPDATE = "trigger.update"
    TRIGGER_DELETE = "trigger.delete"
    TRIGGER_FIRE = "trigger.fire"

    ROLE_CREATE = "role.create"
    ROLE_UPDATE = "role.update"
    ROLE_DELETE = "role.delete"

    SETTING_UPDATE = "setting.update"
    SETTING_DELETE = "setting.delete"

    RUN_CREATE = "run.create"
    RUN_APPROVE = "run.approve"

    EVENT_PUBLISH = "event.publish"
