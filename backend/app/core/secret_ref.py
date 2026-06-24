"""SecretRef indirection: store references to secrets, never plaintext.

A SecretRef is a string ``"<backend>:<locator>"``. Only the ``env`` backend is
supported today (e.g. ``env:OPENAI_API_KEY``); a Vault backend can be added
later without touching callers. The database stores the *reference*; the
plaintext secret is resolved at use time and is never persisted or logged.
"""

import os

SUPPORTED_BACKENDS = ("env",)


class SecretResolutionError(RuntimeError):
    """Raised when a SecretRef cannot be resolved to a value."""


def is_secret_ref(value: str) -> bool:
    """True if ``value`` is a well-formed reference for a supported backend."""
    backend, sep, locator = value.partition(":")
    return bool(sep) and backend in SUPPORTED_BACKENDS and bool(locator)


def resolve_secret(ref: str) -> str:
    """Resolve a SecretRef to its plaintext value at use time.

    Raises SecretResolutionError if the backend is unsupported or the value is
    missing. The error never includes the secret value itself.
    """
    backend, _, locator = ref.partition(":")
    if backend == "env":
        value = os.environ.get(locator)
        if value is None:
            raise SecretResolutionError(f"environment variable {locator!r} is not set")
        return value
    raise SecretResolutionError(f"unsupported secret backend {backend!r}")
