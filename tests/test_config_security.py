import pytest

from config import resolve_secret_key


@pytest.mark.parametrize(
    "placeholder",
    [
        "jobmitra-secret-2026",
        "replace-with-a-cryptographically-secure-random-secret-key",
    ],
)
def test_placeholder_secret_is_rejected_when_debug_is_disabled(placeholder):
    with pytest.raises(RuntimeError, match="Set SECRET_KEY"):
        resolve_secret_key(placeholder, debug_mode=False)


def test_missing_secret_is_rejected_when_debug_is_disabled():
    with pytest.raises(RuntimeError, match="Set SECRET_KEY"):
        resolve_secret_key(None, debug_mode=False)


@pytest.mark.parametrize("configured_key", [None, "jobmitra-secret-2026"])
def test_missing_or_placeholder_secret_generates_ephemeral_key_in_debug(configured_key):
    generated = resolve_secret_key(configured_key, debug_mode=True)

    assert len(generated) == 64
    assert generated != configured_key


def test_configured_secret_is_preserved():
    configured = "test-only-unique-secret-value"
    assert resolve_secret_key(configured, debug_mode=False) == configured
