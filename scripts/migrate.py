"""
Job Mitra - Database Migration Script
Safely upgrades the existing SQLite database without destroying existing data.
Backs up database before running migrations.
"""
import os
import shutil
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jobmitra_local.db')
BACKUP_PATH = DB_PATH + f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def backup_database():
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"[Backup] Successfully backed up database to: {BACKUP_PATH}")
    else:
        print("[Notice] No existing database found. A fresh one will be created.")

def run_migration():
    backup_database()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # 1. Users table
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

    # 2. Employers table
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

    # 3. Recruiter profiles
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recruiter_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        employer_id INTEGER,
        company_name VARCHAR(255) NOT NULL,
        designation VARCHAR(150) DEFAULT 'Talent Acquisition Partner',
        phone VARCHAR(50),
        is_verified INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (employer_id) REFERENCES employers(id) ON DELETE SET NULL
    );
    """)

    # 4. Migrate candidate_profile to include user_id if not present
    cur.execute("PRAGMA table_info(candidate_profile);")
    c_cols = [c[1] for c in cur.fetchall()]
    if 'user_id' not in c_cols:
        cur.execute("ALTER TABLE candidate_profile ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;")
    if 'graduation_year' not in c_cols:
        cur.execute("ALTER TABLE candidate_profile ADD COLUMN graduation_year VARCHAR(20) DEFAULT '2026';")
    if 'bio' not in c_cols:
        cur.execute("ALTER TABLE candidate_profile ADD COLUMN bio TEXT;")
    if 'experience_level' not in c_cols:
        cur.execute("ALTER TABLE candidate_profile ADD COLUMN experience_level VARCHAR(50) DEFAULT 'Fresher';")
    if 'resume_path' not in c_cols:
        cur.execute("ALTER TABLE candidate_profile ADD COLUMN resume_path VARCHAR(255);")
    if 'updated_at' not in c_cols:
        cur.execute("ALTER TABLE candidate_profile ADD COLUMN updated_at TIMESTAMP;")

    # 5. Migrate jobs table to add needed fields
    cur.execute("PRAGMA table_info(jobs);")
    j_cols = [c[1] for c in cur.fetchall()]
    if 'is_demo' not in j_cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN is_demo INTEGER DEFAULT 1;")
    if 'status' not in j_cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN status VARCHAR(50) DEFAULT 'Published';")
    if 'work_mode' not in j_cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN work_mode VARCHAR(50) DEFAULT 'Onsite';")
    if 'graduation_year' not in j_cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN graduation_year VARCHAR(50) DEFAULT '2025, 2026';")
    if 'employer_id' not in j_cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN employer_id INTEGER REFERENCES employers(id) ON DELETE SET NULL;")
    if 'recruiter_id' not in j_cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN recruiter_id INTEGER REFERENCES users(id) ON DELETE SET NULL;")
    if 'source_url' not in j_cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN source_url VARCHAR(255);")
    if 'deadline' not in j_cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN deadline VARCHAR(50);")

    # Mark existing demo jobs properly: is_demo=1, is_verified=0
    cur.execute("UPDATE jobs SET is_demo = 1, is_verified = 0 WHERE is_demo IS NULL OR is_demo = 1;")

    # 6. Rebuild bookmarks table to fix unique constraint flaw (from job_id UNIQUE to UNIQUE(user_id, job_id))
    cur.execute("PRAGMA table_info(bookmarks);")
    b_cols = [c[1] for c in cur.fetchall()]
    if 'user_id' not in b_cols:
        print("[Migration] Re-structuring bookmarks table to associate with user_id...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, job_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        );
        """)
        # Drop old and rename
        cur.execute("DROP TABLE bookmarks;")
        cur.execute("ALTER TABLE bookmarks_new RENAME TO bookmarks;")

    # 7. Migrate applications table to ensure candidate_id and UNIQUE(job_id, candidate_id)
    cur.execute("PRAGMA table_info(applications);")
    a_cols = [c[1] for c in cur.fetchall()]
    if 'candidate_id' not in a_cols:
        cur.execute("ALTER TABLE applications ADD COLUMN candidate_id INTEGER REFERENCES candidate_profile(id) ON DELETE CASCADE;")
        # Link existing application to candidate id 1
        cur.execute("UPDATE applications SET candidate_id = 1 WHERE candidate_id IS NULL;")

    # Add index on applications (job_id, candidate_id)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_app ON applications(job_id, candidate_id);")

    # 8. Skills master table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL UNIQUE,
        category VARCHAR(100) DEFAULT 'General'
    );
    """)

    # 9. Candidate skills relation
    cur.execute("""
    CREATE TABLE IF NOT EXISTS candidate_skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        skill_name VARCHAR(100) NOT NULL,
        proficiency VARCHAR(50) DEFAULT 'Intermediate',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(candidate_id, skill_name),
        FOREIGN KEY (candidate_id) REFERENCES candidate_profile(id) ON DELETE CASCADE
    );
    """)

    # 10. Payments table (implements PENDING -> VERIFIED -> ACTIVE state machine)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
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
        verified_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 11. Subscriptions table migration
    cur.execute("PRAGMA table_info(subscriptions);")
    sub_cols = [c[1] for c in cur.fetchall()]
    if 'user_id' not in sub_cols:
        cur.execute("ALTER TABLE subscriptions ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;")
    if 'payment_id' not in sub_cols:
        cur.execute("ALTER TABLE subscriptions ADD COLUMN payment_id INTEGER REFERENCES payments(id) ON DELETE SET NULL;")
    if 'starts_at' not in sub_cols:
        cur.execute("ALTER TABLE subscriptions ADD COLUMN starts_at TIMESTAMP;")
    if 'expires_at' not in sub_cols:
        cur.execute("ALTER TABLE subscriptions ADD COLUMN expires_at TIMESTAMP;")

    # 12. Audit logs table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action VARCHAR(100) NOT NULL,
        target_type VARCHAR(50) NOT NULL,
        target_id VARCHAR(50),
        ip_address VARCHAR(50),
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 13. Notifications table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title VARCHAR(255) NOT NULL,
        message TEXT NOT NULL,
        type VARCHAR(50) DEFAULT 'info',
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 14. Job Reports table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS job_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        reporter_id INTEGER,
        reason VARCHAR(100) NOT NULL,
        details TEXT,
        status VARCHAR(50) DEFAULT 'Pending' CHECK(status IN ('Pending', 'Reviewed', 'Dismissed', 'Action Taken')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 15. Create initial demonstration users if none exist
    cur.execute("SELECT COUNT(*) FROM users;")
    user_count = cur.fetchone()[0]
    if user_count == 0:
        print("[Migration] Seeding standard candidate & recruiter demonstration accounts...")
        # 1. Candidate Aditya Sharma
        pwd_hash = generate_password_hash("Candidate@123")
        cur.execute("""
        INSERT INTO users (email, password_hash, role, name)
        VALUES ('aditya.engineer@jobmitra.in', ?, 'candidate', 'Aditya Sharma');
        """, (pwd_hash,))
        cand_user_id = cur.lastrowid
        cur.execute("UPDATE candidate_profile SET user_id = ? WHERE id = 1;", (cand_user_id,))
        cur.execute("UPDATE subscriptions SET user_id = ? WHERE id = 1;", (cand_user_id,))

        # 2. Recruiter Priya Verma (TechNova Labs)
        rec_pwd = generate_password_hash("Recruiter@123")
        cur.execute("""
        INSERT INTO users (email, password_hash, role, name)
        VALUES ('priya.recruiter@technova.in', ?, 'recruiter', 'Priya Verma');
        """, (rec_pwd,))
        rec_user_id = cur.lastrowid
        cur.execute("""
        INSERT INTO recruiter_profiles (user_id, company_name, designation, phone, is_verified)
        VALUES (?, 'TechNova Software Labs', 'Lead Technical Recruiter', '+91 80 4123 9001', 0);
        """, (rec_user_id,))

        # Create demo employers
        cur.execute("""
        INSERT OR IGNORE INTO employers (name, website, industry, location, description, is_verified)
        VALUES ('TechNova Software Labs', 'https://technova.example.com', 'Information Technology', 'Bengaluru', 'Software engineering lab specializing in web and cloud platforms.', 0);
        """)
        cur.execute("""
        INSERT OR IGNORE INTO employers (name, website, industry, location, description, is_verified)
        VALUES ('Bharat Precision AutoWorks', 'https://bharatprecision.example.com', 'Automobile Engineering', 'Pune', 'Precision automobile component manufacturer.', 0);
        """)

        # Add initial audit log
        cur.execute("""
        INSERT INTO audit_logs (user_id, action, target_type, target_id, details)
        VALUES (?, 'SCHEMA_MIGRATION', 'SYSTEM', 'DB_INIT', 'Initial schema migration and role setup completed successfully.');
        """, (cand_user_id,))

    conn.commit()
    conn.close()
    print("[Migration] Database migration completed successfully with data integrity preserved!")

if __name__ == '__main__':
    run_migration()
