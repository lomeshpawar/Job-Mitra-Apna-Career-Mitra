"""
Job Mitra - Test Configuration & Fixtures
Sets up an isolated test SQLite database and authenticated Flask test clients.
"""
import os
import tempfile
import sqlite3
import pytest
from werkzeug.security import generate_password_hash

# Set testing environment variables before importing app
os.environ['TESTING'] = 'True'
os.environ['DB_ENGINE'] = 'sqlite'
os.environ['SECRET_KEY'] = 'test-secret-key-for-pytest-execution-only'

from config import Config
Config.TESTING = True

from app import create_app
from database import query_db

@pytest.fixture(scope='session')
def test_db_path():
    """Creates a temporary SQLite file for the test session."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture(scope='session')
def app_instance(test_db_path):
    """Initializes Flask application pointing to the isolated test database."""
    Config.DB_PATH = test_db_path
    app = create_app(Config)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['ENFORCE_CSRF_IN_TESTS'] = False

    # Initialize schema
    conn = sqlite3.connect(test_db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # Create tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email VARCHAR(150) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL CHECK(role IN ('candidate', 'recruiter', 'admin')),
        name VARCHAR(150) NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS candidate_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(150) NOT NULL,
        email VARCHAR(150) NOT NULL,
        phone VARCHAR(50),
        city VARCHAR(100) DEFAULT 'Bengaluru',
        stream VARCHAR(100) DEFAULT 'Computer Science / IT',
        education VARCHAR(255) DEFAULT 'B.Tech / Graduate',
        graduation_year VARCHAR(20) DEFAULT '2026',
        bio TEXT,
        skills TEXT,
        experience_level VARCHAR(50) DEFAULT 'Fresher',
        resume_path VARCHAR(255),
        is_premium INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(255) NOT NULL UNIQUE,
        website VARCHAR(255),
        industry VARCHAR(100),
        location VARCHAR(100),
        description TEXT,
        is_verified INTEGER NOT NULL DEFAULT 0,
        logo_url VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS recruiter_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
        employer_id INTEGER REFERENCES employers(id) ON DELETE SET NULL,
        company_name VARCHAR(255) NOT NULL,
        designation VARCHAR(150) DEFAULT 'Recruiter',
        phone VARCHAR(50),
        is_verified INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(255) NOT NULL,
        company VARCHAR(255) NOT NULL,
        stream VARCHAR(100) NOT NULL,
        qualification VARCHAR(255) NOT NULL,
        graduation_year VARCHAR(50) DEFAULT '2025, 2026',
        city VARCHAR(100) NOT NULL,
        salary_min INT NOT NULL,
        salary_max INT NOT NULL,
        job_type VARCHAR(50) DEFAULT 'Full Time',
        work_mode VARCHAR(50) DEFAULT 'Onsite',
        experience VARCHAR(50) DEFAULT 'Freshers / 0-1 yr',
        skills_required TEXT NOT NULL,
        is_premium INTEGER DEFAULT 0,
        is_urgent INTEGER DEFAULT 1,
        is_verified INTEGER DEFAULT 0,
        is_demo INTEGER DEFAULT 1,
        status VARCHAR(50) DEFAULT 'Published',
        hr_email VARCHAR(150) NOT NULL,
        hr_phone VARCHAR(50) NOT NULL,
        address VARCHAR(255) DEFAULT 'Tech Park, India',
        description TEXT NOT NULL,
        employer_id INTEGER REFERENCES employers(id) ON DELETE SET NULL,
        recruiter_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        source_url VARCHAR(255),
        deadline VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        candidate_id INTEGER NOT NULL REFERENCES candidate_profile(id) ON DELETE CASCADE,
        candidate_name VARCHAR(150) NOT NULL,
        candidate_email VARCHAR(150) NOT NULL,
        candidate_phone VARCHAR(50) NOT NULL,
        candidate_skills TEXT,
        cover_note TEXT,
        status VARCHAR(50) DEFAULT 'Submitted',
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(job_id, candidate_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, job_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        plan_name VARCHAR(100) NOT NULL,
        amount INTEGER NOT NULL,
        currency VARCHAR(10) DEFAULT 'INR',
        upi_id VARCHAR(100) NOT NULL,
        utr_number VARCHAR(100) NOT NULL UNIQUE,
        status VARCHAR(50) NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'VERIFIED', 'ACTIVE', 'FAILED', 'CANCELLED', 'EXPIRED')),
        payment_mode VARCHAR(50) DEFAULT 'UPI',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified_at TIMESTAMP,
        verified_by INTEGER REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        payment_id INTEGER REFERENCES payments(id) ON DELETE SET NULL,
        plan_name VARCHAR(100) NOT NULL,
        amount INTEGER NOT NULL,
        upi_id VARCHAR(100) NOT NULL,
        utr_number VARCHAR(100) NOT NULL,
        candidate_email VARCHAR(150) NOT NULL,
        status VARCHAR(50) DEFAULT 'Active',
        starts_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        action VARCHAR(100) NOT NULL,
        target_type VARCHAR(50) NOT NULL,
        target_id VARCHAR(50),
        ip_address VARCHAR(50),
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS job_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        reporter_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        reason VARCHAR(100) NOT NULL,
        details TEXT,
        status VARCHAR(50) DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed test users
    pw_hash = generate_password_hash("TestPassword123!")

    # 1. Candidate
    cur.execute("INSERT INTO users (email, password_hash, role, name) VALUES ('candidate@test.com', ?, 'candidate', 'Test Candidate')", (pw_hash,))
    cand_uid = cur.lastrowid
    cur.execute("""
        INSERT INTO candidate_profile (user_id, name, email, phone, stream, education, skills, is_premium)
        VALUES (?, 'Test Candidate', 'candidate@test.com', '+91 9999999999', 'Computer Science / IT', 'B.Tech', 'Python, SQL, HTML', 0)
    """, (cand_uid,))

    # 2. Recruiter
    cur.execute("INSERT INTO users (email, password_hash, role, name) VALUES ('recruiter@test.com', ?, 'recruiter', 'Test Recruiter')", (pw_hash,))
    rec_uid = cur.lastrowid
    cur.execute("""
        INSERT INTO recruiter_profiles (user_id, company_name, designation, is_verified)
        VALUES (?, 'Test Corp', 'Talent Lead', 0)
    """, (rec_uid,))

    # 3. Admin
    cur.execute("INSERT INTO users (email, password_hash, role, name) VALUES ('admin@test.com', ?, 'admin', 'Test Admin')", (pw_hash,))

    # Seed a published job
    cur.execute("""
        INSERT INTO jobs (title, company, stream, qualification, city, salary_min, salary_max, skills_required, is_premium, is_urgent, is_verified, is_demo, status, hr_email, hr_phone, description, recruiter_id)
        VALUES ('Graduate Software Engineer', 'Test Corp', 'Computer Science / IT', 'B.Tech / MCA', 'Bengaluru', 30000, 45000, 'Python, SQL, Flask', 0, 1, 0, 1, 'Published', 'hr@testcorp.com', '+91 80 12345678', 'Exciting fresher role in software development.', ?)
    """, (rec_uid,))

    conn.commit()
    conn.close()

    return app

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()

@pytest.fixture
def candidate_client(app_instance):
    """Client logged in as Test Candidate."""
    client = app_instance.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_email'] = 'candidate@test.com'
        sess['user_name'] = 'Test Candidate'
        sess['user_role'] = 'candidate'
        sess['_csrf_token'] = 'test-csrf-token-12345'
    return client

@pytest.fixture
def recruiter_client(app_instance):
    """Client logged in as Test Recruiter."""
    client = app_instance.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_email'] = 'recruiter@test.com'
        sess['user_name'] = 'Test Recruiter'
        sess['user_role'] = 'recruiter'
        sess['_csrf_token'] = 'test-csrf-token-12345'
    return client

@pytest.fixture
def admin_client(app_instance):
    """Client logged in as Test Admin."""
    client = app_instance.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 3
        sess['user_email'] = 'admin@test.com'
        sess['user_name'] = 'Test Admin'
        sess['user_role'] = 'admin'
        sess['_csrf_token'] = 'test-csrf-token-12345'
    return client
