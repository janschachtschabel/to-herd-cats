"""Smoke test: the app is wired and the liveness endpoint responds."""


async def test_health_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
