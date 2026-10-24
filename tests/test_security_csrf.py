"""
Unit & Integration Tests: CSRF Protection & Input Sanitization
"""
import pytest
from security import validate_email_format, validate_phone_format, sanitize_text

def test_input_validation_helpers():
    """Tests server-side input sanitization & format validation."""
    assert validate_email_format('aditya@jobmitra.in') is True
    assert validate_email_format('invalid-email') is False
    assert validate_email_format('') is False

    assert validate_phone_format('+91 9820012345') is True
    assert validate_phone_format('123') is False

    sanitized = sanitize_text('<script>alert("xss")</script>Hello World', max_length=20)
    assert len(sanitized) <= 20

def test_csrf_validation_enforcement(app_instance):
    """
    CSRF Protection Test:
    When CSRF enforcement is enabled, POST requests without matching token are rejected with 400.
    """
    client = app_instance.test_client()
    app_instance.config['ENFORCE_CSRF_IN_TESTS'] = True

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_role'] = 'candidate'
        sess['_csrf_token'] = 'valid-session-csrf-token'

    # 1. POST with missing CSRF token
    resp_no_token = client.post('/candidate/api/profile', json={
        'name': 'Hacked Name'
    })
    assert resp_no_token.status_code == 400

    # 2. POST with invalid CSRF token
    resp_bad_token = client.post('/candidate/api/profile', json={
        'name': 'Hacked Name'
    }, headers={'X-CSRF-Token': 'wrong-token'})
    assert resp_bad_token.status_code == 400

    # 3. POST with correct CSRF token
    resp_valid = client.post('/candidate/api/profile', json={
        'name': 'Valid Name'
    }, headers={'X-CSRF-Token': 'valid-session-csrf-token'})
    assert resp_valid.status_code == 200

    # Reset test config
    app_instance.config['ENFORCE_CSRF_IN_TESTS'] = False
