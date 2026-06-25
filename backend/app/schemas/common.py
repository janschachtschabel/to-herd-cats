"""Shared schema building blocks reused across entities."""

from typing import Annotated

from pydantic import AfterValidator

from app.core.secret_ref import is_secret_ref


def _validate_secret_ref(value: str | None) -> str | None:
    if value is not None and not is_secret_ref(value):
        raise ValueError("must be a secret reference like 'env:VAR_NAME', not a plaintext secret")
    return value


# A nullable string that, when present, must be a valid SecretRef (never plaintext).
SecretRefField = Annotated[str | None, AfterValidator(_validate_secret_ref)]
