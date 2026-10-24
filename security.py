"""
Job Mitra - Security & Authentication Utilities
Handles password hashing, role-based access control (RBAC), CSRF protection,
login attempt throttling, and audit logging.
"""
import re
import secrets
from functools import wraps
from datetime import datetime, timedelta
from flask import session, request, redirect, url_for, jsonify, abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from database import query_db

# In-memory tracking for failed login attempts: { 'ip_or_email': [timestamps] }
FAILED_ATTEMPTS = {}

def hash_password(password: str) -> str:
    """Hashes password using PBKDF2:SHA256 with salt."""
    return generate_password_hash(password, method='pbkdf2:sha256:600000')

def verify_password(hash_val: str, password: str) -> bool:
    """Verifies clear password against stored hash."""
    return check_password_hash(hash_val, password)

def is_rate_limited(identifier: str, max_attempts: int = 5, lockout_minutes: int = 15) -> bool:
    """Checks whether the identifier has exceeded allowed failed attempts."""
    now = datetime.now()
    attempts = FAILED_ATTEMPTS.get(identifier, [])
    # Filter attempts within lockout window
    valid_attempts = [t for t in attempts if now - t < timedelta(minutes=lockout_minutes)]
    FAILED_ATTEMPTS[identifier] = valid_attempts
    return len(valid_attempts) >= max_attempts

def record_failed_attempt(identifier: str):
    """Records a failed login attempt."""
    now = datetime.now()
    if identifier not in FAILED_ATTEMPTS:
        FAILED_ATTEMPTS[identifier] = []
    FAILED_ATTEMPTS[identifier].append(now)

def clear_failed_attempts(identifier: str):
    """Clears failed attempts upon successful login."""
    FAILED_ATTEMPTS.pop(identifier, None)

def generate_csrf_token() -> str:
    """Generates a secure CSRF token and binds it to the user session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf():
    """
    Validates CSRF token on state-changing requests.
    Accepts token from form data ('csrf_token') or HTTP header ('X-CSRF-Token').
    """
    # Allow safe GET, HEAD, OPTIONS
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return

    # Check testing exemption
    if current_app.config.get('TESTING') and not current_app.config.get('ENFORCE_CSRF_IN_TESTS'):
        return

    session_token = session.get('_csrf_token')
    if not session_token:
        # Generate token if missing in session
        session_token = generate_csrf_token()

    # Check header first, then form
    submitted_token = request.headers.get('X-CSRF-Token')
    if not submitted_token and request.form:
        submitted_token = request.form.get('csrf_token')
    if not submitted_token and request.is_json and isinstance(request.json, dict):
        submitted_token = request.json.get('csrf_token')

    if not submitted_token or not secrets.compare_digest(session_token, submitted_token):
        abort(400, "CSRF verification failed. Please refresh and try again.")

def log_audit(user_id, action: str, target_type: str, target_id: str = None, details: str = None):
    """Logs security and administrative events to audit_logs."""
    ip = request.remote_addr if request else '127.0.0.1'
    try:
        query_db("""
            INSERT INTO audit_logs (user_id, action, target_type, target_id, ip_address, details)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, action, target_type, str(target_id) if target_id else None, ip, details), commit=True)
    except Exception as e:
        print(f"[Audit Log Error] Could not write audit log: {e}")

# ==========================================
# RBAC Decorators
# ==========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required", "code": "AUTH_REQUIRED"}), 401
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def roles_accepted(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({"error": "Authentication required", "code": "AUTH_REQUIRED"}), 401
                return redirect(url_for('auth.login', next=request.url))
            
            user_role = session.get('user_role')
            if user_role not in roles:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({"error": f"Forbidden: '{user_role}' does not have permission.", "code": "FORBIDDEN"}), 403
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

candidate_required = roles_accepted('candidate')
recruiter_required = roles_accepted('recruiter', 'admin')
admin_required = roles_accepted('admin')

# ==========================================
# Input Validation Helpers
# ==========================================

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

def validate_email_format(email: str) -> bool:
    return bool(email and EMAIL_REGEX.match(email.strip()))

def validate_phone_format(phone: str) -> bool:
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone.strip())
    return len(cleaned) >= 10 and cleaned.isdigit()

def sanitize_text(text: str, max_length: int = 500) -> str:
    if not text:
        return ""
    cleaned = text.strip()
    return cleaned[:max_length]
