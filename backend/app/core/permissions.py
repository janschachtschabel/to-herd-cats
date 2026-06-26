"""The permission catalog: the authorization vocabulary the API enforces.

Permissions are ``<resource>.<action>`` strings stored on roles
(``Role.permissions``) and checked by the guards in ``app.api.security``. Only
the permissions actually enforced by a guard today are named here; add a
constant when a new guard needs one. ``WILDCARD`` is the "all permissions"
marker an admin role (and the dev-admin fallback) carries.
"""

WILDCARD = "*"


class Permission:
    """Named permission strings (see module docstring)."""

    AGENT_CREATE = "agent.create"
    AGENT_UPDATE = "agent.update"
    AGENT_DELETE = "agent.delete"
    RUN_APPROVE = "run.approve"
