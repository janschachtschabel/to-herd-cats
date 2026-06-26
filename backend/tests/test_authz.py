"""Authorization: the dev-stub principal and the permission guards.

The guards are exercised over HTTP against the agents and inbox routes. In dev
mode (the default) a header-less request is a wildcard admin (so the rest of the
suite stays credential-free) and an ``X-Dev-Roles`` header maps to the named
roles' permissions. With dev mode off the stub is inactive: every request is
anonymous, guarded routes deny, and the header is not honored.
"""

import pytest_asyncio
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient

from app.api.security import Principal
from app.core.db import make_session_factory
from app.core.permissions import WILDCARD
from app.core.settings import Settings
from app.main import create_app

# Mutating routes intentionally left unguarded (read-only analysis over a body).
_OPEN_MUTATIONS = {("POST", "/runs/compare")}


def test_principal_has_direct_and_wildcard():
    holder = Principal(subject="s", permissions=frozenset({"agent.create"}))
    assert holder.has("agent.create")
    assert not holder.has("agent.delete")

    admin = Principal(subject="a", permissions=frozenset({WILDCARD}))
    assert admin.has("anything")

    nobody = Principal(subject="n", permissions=frozenset())
    assert not nobody.has("agent.create")


async def test_dev_mode_admin_without_credentials(client):
    # No X-Dev-Roles header in dev mode => wildcard admin.
    resp = await client.post("/agents", json={"name": "A"})
    assert resp.status_code == 201


async def test_role_header_with_permission_allows(client):
    role = await client.post("/roles", json={"name": "creator", "permissions": ["agent.create"]})
    assert role.status_code == 201

    resp = await client.post("/agents", json={"name": "A"}, headers={"X-Dev-Roles": "creator"})
    assert resp.status_code == 201


async def test_role_header_without_permission_denies(client):
    await client.post("/roles", json={"name": "viewer", "permissions": ["agent.read"]})

    resp = await client.post("/agents", json={"name": "A"}, headers={"X-Dev-Roles": "viewer"})
    assert resp.status_code == 403


async def test_unknown_role_denies(client):
    resp = await client.post("/agents", json={"name": "A"}, headers={"X-Dev-Roles": "ghost"})
    assert resp.status_code == 403


async def test_permissions_are_unioned_across_roles(client):
    await client.post("/roles", json={"name": "maker", "permissions": ["agent.create"]})
    await client.post("/roles", json={"name": "remover", "permissions": ["agent.delete"]})
    created = (
        await client.post("/agents", json={"name": "Temp"}, headers={"X-Dev-Roles": "maker"})
    ).json()

    # "maker" alone cannot delete; "maker,remover" can.
    only_maker = await client.delete(f"/agents/{created['id']}", headers={"X-Dev-Roles": "maker"})
    assert only_maker.status_code == 403
    both = await client.delete(f"/agents/{created['id']}", headers={"X-Dev-Roles": "maker,remover"})
    assert both.status_code == 204


@pytest_asyncio.fixture
async def locked_client(engine):
    """Client whose app has the auth stub off (auth_dev_mode=False)."""
    settings = Settings(
        database_url=engine.url.render_as_string(hide_password=False),
        auth_dev_mode=False,
    )
    app = create_app(settings)
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


async def test_locked_mode_denies_writes(locked_client):
    resp = await locked_client.post("/agents", json={"name": "A"})
    assert resp.status_code == 403


async def test_locked_mode_does_not_honor_dev_roles_header(locked_client):
    # The header is a dev affordance; with the stub off it must not authorize.
    await locked_client.post("/roles", json={"name": "admin", "permissions": ["agent.create"]})
    resp = await locked_client.post("/agents", json={"name": "A"}, headers={"X-Dev-Roles": "admin"})
    assert resp.status_code == 403


async def test_reads_stay_open(locked_client):
    # Reads are not guarded in this increment, even with the stub off.
    resp = await locked_client.get("/agents")
    assert resp.status_code == 200


async def test_run_create_requires_its_own_permission(client):
    # A role that can create agents still cannot start runs without run.create.
    agent = (await client.post("/agents", json={"name": "A"})).json()
    await client.post("/roles", json={"name": "norun", "permissions": ["agent.create"]})
    denied = await client.post(
        f"/agents/{agent['id']}/runs", json={"goal": "x"}, headers={"X-Dev-Roles": "norun"}
    )
    assert denied.status_code == 403


async def test_me_reports_admin_without_credentials(client):
    body = (await client.get("/me")).json()
    assert body["subject"] == "dev-admin"
    assert body["permissions"] == ["*"]


async def test_me_reflects_dev_roles_header(client):
    await client.post("/roles", json={"name": "ed", "permissions": ["agent.create", "tool.create"]})
    body = (await client.get("/me", headers={"X-Dev-Roles": "ed"})).json()
    assert set(body["permissions"]) == {"agent.create", "tool.create"}


def test_every_write_route_is_permission_guarded():
    """Every mutating route must carry a require_permission guard.

    Introspects the wired app so a future write endpoint added without a guard
    fails here rather than shipping open.
    """
    app = create_app(Settings())
    unguarded = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = route.methods & {"POST", "PUT", "PATCH", "DELETE"}
        if not methods:
            continue
        if any((method, route.path) in _OPEN_MUTATIONS for method in methods):
            continue
        guarded = any(
            getattr(dep.call, "__qualname__", "").startswith("require_permission")
            for dep in route.dependant.dependencies
        )
        if not guarded:
            unguarded.append(f"{sorted(methods)} {route.path}")
    assert unguarded == [], f"unguarded write routes: {unguarded}"
