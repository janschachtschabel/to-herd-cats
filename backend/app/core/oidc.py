"""OIDC (Keycloak) access-token verification.

Verifies a Bearer access token's RS256 signature against the issuer's JWKS plus
its ``iss`` / ``aud`` / ``exp`` claims, then returns the subject and the realm
roles. The role→permission mapping stays in the app (see ``RoleService``), so
the token supplies *membership* and the app supplies *permissions*.

Verification is off until configured (``Settings.oidc_*``); the dev stub in
``app.api.security`` applies meanwhile.
"""

import logging

import jwt
from jwt import PyJWKClient

from app.core.settings import Settings

logger = logging.getLogger(__name__)


class TokenError(Exception):
    """Raised when an access token fails verification."""


class OidcVerifier:
    """Verifies access tokens against an issuer's JWKS.

    ``jwks_client`` is injected so the signing-key source can be faked in tests
    without network access (production builds a real ``PyJWKClient``).
    """

    def __init__(self, issuer: str, audience: str, jwks_client: PyJWKClient) -> None:
        self._issuer = issuer
        self._audience = audience
        self._jwks = jwks_client

    def verify(self, token: str) -> tuple[str, list[str]]:
        """Return ``(subject, realm_roles)`` for a valid token, else ``TokenError``."""
        try:
            signing_key = self._jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
                # Reject tokens missing the claims we rely on, rather than
                # silently skipping their checks.
                options={"require": ["exp", "iss", "aud"]},
            )
        except jwt.PyJWTError as exc:
            raise TokenError(str(exc)) from exc
        subject = claims.get("sub")
        if not subject:
            raise TokenError("token has no subject")
        roles = claims.get("realm_access", {}).get("roles", [])
        return subject, list(roles)


def build_verifier(settings: Settings) -> OidcVerifier | None:
    """Build the verifier from settings, or ``None`` when OIDC is not configured."""
    if not settings.oidc_issuer or not settings.oidc_jwks_uri:
        return None
    return OidcVerifier(
        settings.oidc_issuer,
        settings.oidc_audience,
        PyJWKClient(settings.oidc_jwks_uri),
    )
