"""OIDC access-token verification and its integration with get_principal.

Tokens are signed with a throwaway RSA keypair and verified against a fake JWKS
source, so the whole flow runs without a Keycloak server or any network access.
"""

import time
from types import SimpleNamespace

import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient

from app.core.db import make_session_factory
from app.core.oidc import OidcVerifier, TokenError, build_verifier
from app.core.settings import Settings
from app.main import create_app

_ISSUER = "https://issuer.example/realms/cockpit"
_AUDIENCE = "cockpit"
_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUBLIC_KEY = _PRIVATE_KEY.public_key()
_OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class _FakeJwks:
    """Stands in for PyJWKClient, returning a fixed public key."""

    def __init__(self, public_key) -> None:
        self._key = public_key

    def get_signing_key_from_jwt(self, token):  # noqa: ARG002 - signature parity
        return SimpleNamespace(key=self._key)


def _make_token(
    *, sub="user-1", roles=("editor",), iss=_ISSUER, aud=_AUDIENCE, exp_delta=3600, key=_PRIVATE_KEY
):
    now = int(time.time())
    claims = {
        "iss": iss,
        "aud": aud,
        "iat": now,
        "exp": now + exp_delta,
        "realm_access": {"roles": list(roles)},
    }
    if sub is not None:
        claims["sub"] = sub
    return jwt.encode(claims, key, algorithm="RS256")


def _verifier() -> OidcVerifier:
    return OidcVerifier(_ISSUER, _AUDIENCE, _FakeJwks(_PUBLIC_KEY))


def test_verify_returns_subject_and_roles():
    subject, roles = _verifier().verify(_make_token(sub="u1", roles=["editor", "viewer"]))
    assert subject == "u1"
    assert roles == ["editor", "viewer"]


def test_verify_rejects_bad_signature():
    with pytest.raises(TokenError):
        _verifier().verify(_make_token(key=_OTHER_KEY))


def test_verify_rejects_wrong_audience():
    with pytest.raises(TokenError):
        _verifier().verify(_make_token(aud="someone-else"))


def test_verify_rejects_wrong_issuer():
    with pytest.raises(TokenError):
        _verifier().verify(_make_token(iss="https://evil.example"))


def test_verify_rejects_expired():
    with pytest.raises(TokenError):
        _verifier().verify(_make_token(exp_delta=-10))


def test_verify_rejects_missing_subject():
    with pytest.raises(TokenError):
        _verifier().verify(_make_token(sub=None))


def test_build_verifier_disabled_without_config():
    assert build_verifier(Settings()) is None


def test_build_verifier_enabled_with_config():
    verifier = build_verifier(
        Settings(oidc_issuer="https://i/realms/c", oidc_jwks_uri="https://i/realms/c/certs")
    )
    assert verifier is not None


@pytest_asyncio.fixture
async def oidc_client(engine):
    """Client whose app verifies OIDC tokens with the test keypair."""
    settings = Settings(database_url=engine.url.render_as_string(hide_password=False))
    app = create_app(settings)
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)
    app.state.oidc = OidcVerifier(_ISSUER, _AUDIENCE, _FakeJwks(_PUBLIC_KEY))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


async def test_me_reflects_the_token_principal(oidc_client):
    await oidc_client.post("/roles", json={"name": "editor", "permissions": ["agent.create"]})
    token = _make_token(sub="user-1", roles=["editor"])

    body = (await oidc_client.get("/me", headers={"Authorization": f"Bearer {token}"})).json()
    assert body["subject"] == "user-1"
    assert body["permissions"] == ["agent.create"]


async def test_token_permits_a_guarded_write(oidc_client):
    await oidc_client.post("/roles", json={"name": "editor", "permissions": ["agent.create"]})
    token = _make_token(roles=["editor"])

    resp = await oidc_client.post(
        "/agents", json={"name": "A"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 201


async def test_token_without_permission_is_denied(oidc_client):
    await oidc_client.post("/roles", json={"name": "viewer", "permissions": []})
    token = _make_token(roles=["viewer"])

    resp = await oidc_client.post(
        "/agents", json={"name": "A"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


async def test_invalid_token_is_rejected(oidc_client):
    token = _make_token(key=_OTHER_KEY)
    resp = await oidc_client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
