"""Configuration validation tests for production-sensitive settings."""

import pytest

from app import create_app
from config import is_configured_upi_id, is_usable_secret_key


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "jobmitra-secret-2026",
        "replace-with-a-cryptographically-secure-random-secret-key",
        "too-short",
    ],
)
def test_unusable_session_keys_are_rejected(value):
    assert is_usable_secret_key(value) is False


def test_non_placeholder_session_key_of_sufficient_length_is_accepted():
    assert is_usable_secret_key("a" * 64) is True


@pytest.mark.parametrize(
    "value",
    ["", "your-business-upi@bank", "your-upi-id@bank", None],
)
def test_example_or_missing_upi_destination_is_unconfigured(value):
    assert is_configured_upi_id(value) is False


def test_non_placeholder_upi_destination_is_configured():
    assert is_configured_upi_id("merchant@bank") is True


@pytest.mark.parametrize(
    "secret_key",
    [
        None,
        "",
        "replace-with-a-cryptographically-secure-random-secret-key",
    ],
)
def test_app_factory_rejects_missing_or_placeholder_session_key(secret_key):
    class InvalidConfig:
        SECRET_KEY = secret_key
        TESTING = False

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(InvalidConfig)
