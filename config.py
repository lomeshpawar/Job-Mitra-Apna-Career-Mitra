"""
Job Mitra - Application Configuration
Loads settings securely from environment variables with safe defaults for development.
"""
import os
import secrets
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

_PLACEHOLDER_SECRET_KEYS = {
    'jobmitra-secret-2026',
    'replace-with-a-cryptographically-secure-random-secret-key',
}


def resolve_secret_key(configured_key, debug_mode=False):
    """Return a configured secret key or reject known placeholders.

    A missing key may be generated for local debug use. Non-debug runs must
    provide a stable, operator-generated key so sessions remain valid across
    process restarts and multiple application workers.
    """
    secret_key = (configured_key or '').strip()

    if secret_key.lower() in _PLACEHOLDER_SECRET_KEYS:
        secret_key = ''

    if not secret_key:
        if debug_mode:
            return secrets.token_hex(32)
        raise RuntimeError(
            'Set SECRET_KEY to a unique random value before running Job Mitra '
            'with FLASK_DEBUG disabled. Do not use the .env.example placeholder.'
        )

    return secret_key


class Config:
    # Flask Security
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    SECRET_KEY = resolve_secret_key(os.getenv('SECRET_KEY'), DEBUG)

    PORT = int(os.getenv('PORT', 5000))

    # Session & Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days

    # Request limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max payload

    # Database Settings
    DB_ENGINE = os.getenv('DB_ENGINE', 'auto').lower()
    DB_PATH = os.path.join(BASE_DIR, 'jobmitra_local.db')
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'jobmitra_portal')

    # UPI & Payment Configuration
    UPI_ID = os.getenv('UPI_ID', '7770009027-2@axl')
    PAYMENT_GATEWAY_LIVE = os.getenv('PAYMENT_GATEWAY_LIVE', 'False').lower() in ('true', '1', 'yes')
    PAYMENT_GATEWAY_NAME = os.getenv('PAYMENT_GATEWAY_NAME', 'Manual UPI Verification / Demo')
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')

    # Email & SMTP Configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')
    SMTP_FROM = os.getenv('SMTP_FROM', 'no-reply@jobmitra.in')

    # Security & Rate Limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    # Testing Flag
    TESTING = False
