"""
Job Mitra - Administrator Bootstrap Procedure
Safe, documented command to bootstrap or promote an administrator account.
Never relies on hardcoded default credentials.
Usage:
    python scripts/bootstrap_admin.py
Or non-interactively via environment variables:
    $env:ADMIN_EMAIL="admin@jobmitra.in"
    $env:ADMIN_NAME="Platform Administrator"
    $env:ADMIN_PASSWORD="YourStrongPassword123!"
    python scripts/bootstrap_admin.py
"""
import os
import sys
import sqlite3
import getpass
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jobmitra_local.db')

def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    return True, ""

def bootstrap_admin():
    print("=" * 60)
    print(" Job Mitra - Secure Administrator Bootstrap Tool")
    print("=" * 60)

    email = os.getenv('ADMIN_EMAIL')
    name = os.getenv('ADMIN_NAME')
    password = os.getenv('ADMIN_PASSWORD')

    if not email:
        try:
            email = input("Enter Administrator Email: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(1)

    if not email or '@' not in email:
        print("[Error] A valid email address is required.")
        sys.exit(1)

    if not name:
        try:
            name = input("Enter Administrator Full Name [Platform Administrator]: ").strip() or "Platform Administrator"
        except (EOFError, KeyboardInterrupt):
            name = "Platform Administrator"

    if not password:
        try:
            password = getpass.getpass("Enter Administrator Password (min 8 chars, 1 uppercase, 1 digit): ")
            confirm = getpass.getpass("Confirm Administrator Password: ")
            if password != confirm:
                print("[Error] Passwords do not match.")
                sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(1)

    is_valid, err = validate_password(password)
    if not is_valid:
        print(f"[Error] Weak password: {err}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    cur.execute("SELECT id, role FROM users WHERE email = ?;", (email,))
    existing = cur.fetchone()

    hashed_pw = generate_password_hash(password)

    if existing:
        user_id, current_role = existing
        cur.execute("UPDATE users SET role = 'admin', password_hash = ?, name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                    (hashed_pw, name, user_id))
        print(f"[Success] Existing user '{email}' (previously '{current_role}') upgraded to Administrator (ID: {user_id}).")
        action = "ADMIN_PROMOTED"
    else:
        cur.execute("""
        INSERT INTO users (email, password_hash, role, name)
        VALUES (?, ?, 'admin', ?);
        """, (email, hashed_pw, name))
        user_id = cur.lastrowid
        print(f"[Success] New Administrator '{email}' created successfully (ID: {user_id}).")
        action = "ADMIN_BOOTSTRAP_CREATED"

    cur.execute("""
    INSERT INTO audit_logs (user_id, action, target_type, target_id, details)
    VALUES (?, ?, 'USER', ?, 'Administrator bootstrap procedure executed safely.');
    """, (user_id, action, str(user_id)))

    conn.commit()
    conn.close()
    print("[Done] Admin credentials safely stored with PBKDF2/scrypt hashing.")

if __name__ == '__main__':
    bootstrap_admin()
