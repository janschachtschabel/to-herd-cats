"""Agent ownership: the creator owns the agent; the owner OR a holder of the
manage permission may update/delete it (M8.3c)."""


async def _role(client, name: str, permissions: list[str]) -> None:
    # Seeded with no auth header -> dev-admin (wildcard) may create roles.
    await client.post("/roles", json={"name": name, "permissions": permissions})


async def test_create_records_owner_from_principal(client):
    await _role(client, "maker", ["agent.create"])
    agent = (
        await client.post("/agents", json={"name": "A"}, headers={"X-Dev-Roles": "maker"})
    ).json()
    assert agent["created_by"] == "dev:maker"


async def test_owner_may_update_and_delete_without_manage_permission(client):
    await _role(client, "maker", ["agent.create"])  # can create, NOT update/delete
    owner = {"X-Dev-Roles": "maker"}
    agent = (await client.post("/agents", json={"name": "A"}, headers=owner)).json()

    upd = await client.patch(f"/agents/{agent['id']}", json={"goal": "g"}, headers=owner)
    assert upd.status_code == 200
    assert upd.json()["goal"] == "g"

    assert (await client.delete(f"/agents/{agent['id']}", headers=owner)).status_code == 204


async def test_non_owner_without_permission_is_denied(client):
    await _role(client, "maker", ["agent.create"])
    await _role(client, "stranger", [])
    agent = (
        await client.post("/agents", json={"name": "A"}, headers={"X-Dev-Roles": "maker"})
    ).json()
    stranger = {"X-Dev-Roles": "stranger"}

    assert (
        await client.patch(f"/agents/{agent['id']}", json={"goal": "g"}, headers=stranger)
    ).status_code == 403
    assert (await client.delete(f"/agents/{agent['id']}", headers=stranger)).status_code == 403


async def test_non_owner_with_permission_may_update_and_delete(client):
    await _role(client, "maker", ["agent.create"])
    await _role(client, "manager", ["agent.update", "agent.delete"])
    agent = (
        await client.post("/agents", json={"name": "A"}, headers={"X-Dev-Roles": "maker"})
    ).json()
    manager = {"X-Dev-Roles": "manager"}

    assert (
        await client.patch(f"/agents/{agent['id']}", json={"goal": "g"}, headers=manager)
    ).status_code == 200
    assert (await client.delete(f"/agents/{agent['id']}", headers=manager)).status_code == 204


async def test_update_missing_agent_is_404(client):
    await _role(client, "manager", ["agent.update"])
    resp = await client.patch(
        "/agents/does-not-exist", json={"goal": "g"}, headers={"X-Dev-Roles": "manager"}
    )
    assert resp.status_code == 404
