"""Request-layer authorization: the current principal and permission guards.

Until Keycloak/OIDC lands (a later M8 sub-step) the principal comes from a dev
stub, gated by ``auth_dev_mode``:

* dev mode on (default) — an ``X-Dev-Roles`` header (comma-separated role names)
  is mapped to the union of those roles' permissions; with no header the request
  is a wildcard admin, so the cockpit is usable without a login.
* dev mode off — every request is anonymous (no permissions), so guarded routes
  deny by default. The OIDC resolver replaces this branch when real auth lands.

The header is a development affordance only: it is honored solely in dev mode and
is replaced wholesale by the OIDC token's subject and roles later.
"""

import logging
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status

from app.core.permissions import WILDCARD
from app.services.roles import RoleService

logger = logging.getLogger(__name__)

_DEV_ROLES_HEADER = "X-Dev-Roles"


@dataclass(frozen=True)
class Principal:
    """The calling identity and the permissions it holds."""

    subject: str
    permissions: frozenset[str]

    def has(self, permission: str) -> bool:
        """True if the principal holds ``permission`` (or the wildcard)."""
        return WILDCARD in self.permissions or permission in self.permissions


async def get_principal(request: Request) -> Principal:
    """Resolve the calling principal (dev stub — see module docstring)."""
    if not request.app.state.settings.auth_dev_mode:
        # Stub disabled; the OIDC resolver will replace this branch.
        return Principal(subject="anonymous", permissions=frozenset())
    header = request.headers.get(_DEV_ROLES_HEADER)
    if header is None:
        return Principal(subject="dev-admin", permissions=frozenset({WILDCARD}))
    names = [name.strip() for name in header.split(",") if name.strip()]
    # Only the header path needs the DB, so the admin path stays I/O-free.
    factory = request.app.state.session_factory
    async with factory() as session:
        permissions = await RoleService(session).permissions_for_roles(names)
    return Principal(subject=f"dev:{','.join(names)}", permissions=frozenset(permissions))


def require_permission(permission: str):
    """Build a dependency that 403s unless the principal holds ``permission``."""

    async def guard(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has(permission):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"missing permission: {permission}")
        return principal

    return guard
