"""Request-layer authorization: the current principal and permission guards.

When OIDC is configured, a verified Bearer token takes precedence: its subject
and realm roles become the principal (the app resolves those roles to
permissions — see ``RoleService``). Without a usable token the principal comes
from a dev stub gated by ``auth_dev_mode``:

* dev mode on (default) — an ``X-Dev-Roles`` header (comma-separated role names)
  maps to the union of those roles' permissions; with no header the request is a
  wildcard admin, so the cockpit is usable without a login.
* dev mode off — every request is anonymous (no permissions), so guarded routes
  deny by default.

The ``X-Dev-Roles`` header is a development affordance, honored only in dev mode;
it is superseded by the OIDC token once Keycloak is wired up.
"""

import logging
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status

from app.core.oidc import TokenError
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
    """Resolve the calling principal — OIDC token if present, else the dev stub."""
    verifier = getattr(request.app.state, "oidc", None)
    authorization = request.headers.get("Authorization")
    if verifier is not None and authorization and authorization.startswith("Bearer "):
        try:
            subject, roles = verifier.verify(authorization.removeprefix("Bearer "))
        except TokenError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from None
        permissions = await _permissions_for(request, roles)
        return Principal(subject=subject, permissions=frozenset(permissions))
    # No usable bearer token: fall back to the dev stub.
    if not request.app.state.settings.auth_dev_mode:
        return Principal(subject="anonymous", permissions=frozenset())
    header = request.headers.get(_DEV_ROLES_HEADER)
    if header is None:
        # Admin shortcut stays I/O-free (no role lookup).
        return Principal(subject="dev-admin", permissions=frozenset({WILDCARD}))
    names = [name.strip() for name in header.split(",") if name.strip()]
    permissions = await _permissions_for(request, names)
    return Principal(subject=f"dev:{','.join(names)}", permissions=frozenset(permissions))


async def _permissions_for(request: Request, role_names: list[str]) -> set[str]:
    """Resolve role names to their unioned permissions in a fresh session."""
    factory = request.app.state.session_factory
    async with factory() as session:
        return await RoleService(session).permissions_for_roles(role_names)


def require_permission(permission: str):
    """Build a dependency that 403s unless the principal holds ``permission``."""

    async def guard(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has(permission):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"missing permission: {permission}")
        return principal

    return guard
