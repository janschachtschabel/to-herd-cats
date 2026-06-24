"""Tests for the SecretRef indirection (never store/return plaintext secrets)."""

import pytest

from app.core.secret_ref import SecretResolutionError, is_secret_ref, resolve_secret


def test_is_secret_ref_recognises_supported_backend():
    assert is_secret_ref("env:OPENAI_API_KEY")
    assert not is_secret_ref("plain-secret")
    assert not is_secret_ref("env:")  # empty locator
    assert not is_secret_ref("vault:secret/path")  # unsupported backend today


def test_resolve_env(monkeypatch):
    monkeypatch.setenv("THC_TEST_SECRET", "s3cret")
    assert resolve_secret("env:THC_TEST_SECRET") == "s3cret"


def test_resolve_missing_env_raises(monkeypatch):
    monkeypatch.delenv("THC_MISSING", raising=False)
    with pytest.raises(SecretResolutionError):
        resolve_secret("env:THC_MISSING")


def test_resolve_unsupported_backend_raises():
    with pytest.raises(SecretResolutionError):
        resolve_secret("vault:secret/path")
