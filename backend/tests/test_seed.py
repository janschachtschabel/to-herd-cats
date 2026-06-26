"""Startup role seeding (bootstrap admin)."""

from app.core.seed import seed_default_roles
from app.models.role import Role
from app.repositories.roles import SqlAlchemyRoleRepository


async def test_seeds_admin_role_when_empty(db_session):
    await seed_default_roles(db_session)

    roles = await SqlAlchemyRoleRepository(db_session).list()
    assert len(roles) == 1
    assert roles[0].name == "admin"
    assert roles[0].permissions == ["*"]


async def test_seed_is_idempotent_when_roles_exist(db_session):
    repo = SqlAlchemyRoleRepository(db_session)
    await repo.add(Role(name="editor", permissions=["agent.create"]))
    await db_session.commit()

    await seed_default_roles(db_session)

    roles = await repo.list()
    assert {r.name for r in roles} == {"editor"}  # no admin seeded over existing roles


async def test_seed_runs_once(db_session):
    await seed_default_roles(db_session)
    await seed_default_roles(db_session)

    roles = await SqlAlchemyRoleRepository(db_session).list()
    assert [r.name for r in roles] == ["admin"]
