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

class Config:
    # Flask Security
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY or SECRET_KEY == 'jobmitra-secret-2026':
        # Generate an ephemeral secure key if none is securely supplied, with a warning
        SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))

    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
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
