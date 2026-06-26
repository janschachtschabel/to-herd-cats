"""Bootstrap data seeded at startup.

A fresh deployment with the dev stub off (``auth_dev_mode=false``) has no way to
grant the first permission: creating a role itself needs ``role.create``, which
no principal holds yet. Seeding a single ``admin`` role (all permissions) breaks
that chicken-and-egg — a user carrying the matching Keycloak realm role then has
full access and can define the remaining roles in the UI.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import WILDCARD
from app.models.role import Role
from app.repositories.roles import SqlAlchemyRoleRepository

logger = logging.getLogger(__name__)

ADMIN_ROLE_NAME = "admin"


async def seed_default_roles(session: AsyncSession) -> None:
    """Create the bootstrap ``admin`` role when no roles exist yet.

    Idempotent: a no-op once any role is present, so it never overwrites roles an
    operator has defined. Assumes the schema is already migrated (the app does).
    """
    repo = SqlAlchemyRoleRepository(session)
    if await repo.list():
        return
    await repo.add(
        Role(
            name=ADMIN_ROLE_NAME,
            description="Full access (bootstrap role).",
            permissions=[WILDCARD],
        )
    )
    await session.commit()
    logger.info("seeded bootstrap '%s' role", ADMIN_ROLE_NAME)
