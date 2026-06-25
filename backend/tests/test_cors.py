"""CORS is enabled for the configured browser origin (the Angular dev server)."""


async def test_cors_header_for_allowed_origin(client):
    resp = await client.get("/health", headers={"Origin": "http://localhost:4200"})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:4200"
