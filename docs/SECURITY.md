# Job Mitra — Application Security Architecture & Controls

**Project:** Job Mitra — Apna Career Mitra  
**Document Version:** 2.0 (Security Hardened)  
**Security Lead:** Senior Application Security Engineer  

---

## 1. Security Architecture Overview

Job Mitra implements defense-in-depth across the entire application stack:

```
[ Public Client ]
       │
       ▼ (HTTPS / TLS)
[ Session & CSRF Layer ] ──> Validates Session Token & X-CSRF-Token / csrf_token
       │
       ▼
[ Rate Limiting & Throttling ] ──> 5 attempts / 15-minute lockout per IP / identifier
       │
       ▼
[ RBAC Authorization Guard ] ──> @login_required, @roles_accepted('candidate', 'recruiter', 'admin')
       │
       ▼
[ Input Sanitization & Validation ] ──> Email regex, phone normalization, text length clipping
       │
       ▼
[ Business Logic & Ownership Checks ] ──> Validates candidate_id, recruiter_id, unique UTRs
       │
       ▼
[ Parameterized Query Layer ] ──> SQLite (PRAGMA foreign_keys=ON) / MySQL (InnoDB, autocommit=False)
       │
       ▼
[ Immutable Audit Trail ] ──> audit_logs (User ID, IP, Action, Target, Timestamp)
```

---

## 2. Authentication & Credential Storage

### 2.1 Password Hashing
- Cleartext passwords are never stored or logged.
- Hashes are generated using **PBKDF2-HMAC-SHA256** with 600,000 iterations and cryptographically random salts via `werkzeug.security`.
- Login verifications use timing-attack resistant comparisons.

### 2.2 Brute-Force Throttling
- The system monitors consecutive failed sign-in attempts per IP and per target email.
- Exceeding 5 failures results in a mandatory **15-minute lockout** with HTTP status `429 Too Many Requests`.
- Successful logins immediately clear failure counters.

### 2.3 Session Management
- Sessions use server-side signed cookies via `Flask.session`.
- Cookie security flags enforced in `config.py`:
  - `SESSION_COOKIE_HTTPONLY = True` (mitigates XSS session hijacking).
  - `SESSION_COOKIE_SAMESITE = 'Lax'` (mitigates CSRF cross-site leakage).
  - `SESSION_COOKIE_SECURE = True` in production (ensures transmission exclusively over HTTPS).

---

## 3. Role-Based Access Control (RBAC) Matrix

| Resource / Endpoint | Candidate | Recruiter | Administrator | Public / Unauth |
|---|:---:|:---:|:---:|:---:|
| Browse & Search Vacancies (`/`, `/jobs`, `/jobs/<id>`) | Read | Read | Read | Read |
| 1-Click Job Application (`/api/jobs/<id>/apply`) | **Create (Self)** | ❌ 403 | ❌ 403 | ❌ 401 |
| Bookmark Job (`/api/jobs/<id>/bookmark`) | **Toggle (Self)** | **Toggle (Self)** | **Toggle (Self)** | ❌ 401 |
| Candidate Profile & Skills (`/candidate/*`) | **Full (Self)** | ❌ 403 | ❌ 403 | ❌ 401 |
| Post Job Vacancy (`/recruiter/post-job`) | ❌ 403 | **Create (Pending)** | **Create (Direct)** | ❌ 401 |
| Manage Recruiter Postings & Applicants (`/recruiter/*`) | ❌ 403 | **Manage (Own Jobs)** | **Full Oversight** | ❌ 401 |
| Job Moderation (`/admin/moderation`, `/admin/api/jobs/*`) | ❌ 403 | ❌ 403 | **Full Control** | ❌ 401 |
| Employer Verification (`/admin/employers`) | ❌ 403 | ❌ 403 | **Full Control** | ❌ 401 |
| Payment Ledger & Pro Activation (`/admin/payments`) | ❌ 403 | ❌ 403 | **Full Control** | ❌ 401 |
| Security Audit Logs (`/admin/audit-logs`) | ❌ 403 | ❌ 403 | **Full Access** | ❌ 401 |

---

## 4. Payment State Machine & Anti-Fraud Controls

### 4.1 State Machine Design
User-submitted payment references (UTRs) must never activate premium privileges automatically. Job Mitra enforces the following state flow:

```
[ Client Submits UTR ] ──> PENDING (Demo / Manual Mode)
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
     [ Admin Verifies ]                    [ Admin Rejects ]
            │                                     │
            ▼                                     ▼
         ACTIVE                                FAILED / CANCELLED
    (Pro Features On)                         (No Privileges Given)
            │
     [ Expiry Timer ]
            │
            ▼
         EXPIRED
```

### 4.2 Security Rules
1. **Uniqueness & Idempotency:** The `payments.utr_number` column has a unique database constraint. Re-submitting the same reference returns `409 Conflict`.
2. **Amount & Catalog Verification:** The backend verifies that the submitted amount matches the catalog price for the requested plan (`Starter Boost ₹99`, `Graduate Pro ₹199`, `Lifetime Pass ₹499`).
3. **No Sensitive Banking Data:** Card numbers, CVVs, UPI PINs, and net banking credentials are never collected or stored.
4. **Transparent Mode Disclosure:** The portal explicitly identifies local mode as `DEMO_MANUAL_VERIFICATION`. False claims of live gateway integration are prohibited.

---

## 5. Cross-Site Request Forgery (CSRF) Protection

- Every session maintains a cryptographically secure random token (`_csrf_token`).
- `before_request` hook validates `X-CSRF-Token` header (for asynchronous AJAX/Fetch) or `csrf_token` form field (for synchronous HTML form posts).
- Missing or mismatched tokens terminate with `400 Bad Request`.
- Safe idempotent methods (`GET`, `HEAD`, `OPTIONS`) are exempt.

---

## 6. Administrator Bootstrap Tool

To avoid hardcoded administrator passwords, a dedicated CLI tool is provided at `scripts/bootstrap_admin.py`:

```bash
# Interactive Mode
python scripts/bootstrap_admin.py

# Non-Interactive / Automation Mode
$env:ADMIN_EMAIL="admin@jobmitra.in"
$env:ADMIN_NAME="Super Administrator"
$env:ADMIN_PASSWORD="YourStrongPassword123!"
python scripts/bootstrap_admin.py
```

The script:
- Enforces password complexity (min 8 characters, at least 1 uppercase letter, at least 1 number).
- Uses PBKDF2 hashing.
- Writes an audit log entry for accountability.

---

## 7. Audit Logging & Non-Repudiation

All critical security events are recorded in the `audit_logs` table:
- Account creation and role assignment
- Authentication successes and failures
- Candidate profile mutations
- Job postings, approvals, rejections, and takedowns
- Fraud reports filed by candidates
- Payment reference submissions and admin verification transitions

Each audit log entry captures: `timestamp`, `user_id`, `action`, `target_type`, `target_id`, `ip_address`, and `details`.
