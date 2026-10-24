# Job Mitra — Apna Career Mitra
### Job Portal for Freshers and IT Job Seekers

A modern, secure, and responsive recruitment platform built with **Python Flask**, **SQLite (with automatic MySQL engine support)**, **HTML5**, **CSS3 (Premium Glassmorphism + Modern SaaS)**, and **JavaScript**.

---

## 🌟 Key Features

1. **Modern SaaS & Premium Glassmorphism Interface**:
   - Styled using custom design tokens: Main Background `#0B1020`, Secondary `#111827`, Primary Accent `#6366F1`, Secondary Accent `#8B5CF6`, CTA Accent `#2563EB`, Main Text `#F8FAFC`, Secondary Text `#94A3B8`.
   - Restrained translucent dark surfaces with backdrop blur (`blur(14px)`), smooth 0.2s cubic transitions, subtle glow accents, and responsive layout (375px, 430px, 768px, 1024px, 1440px).

2. **Role-Based Access Control (RBAC) & Multi-Tenant Architecture**:
   - Distinct roles: **Candidate**, **Recruiter**, and **Administrator**.
   - **Candidate Experience:** Personalized dashboard, true profile completion meter, technical skill manager, application tracker, saved jobs (bookmarks), and transparent recommendation scores.
   - **Recruiter Console:** Job vacancy creation (`Draft`, `Pending Review`, `Published`, `Rejected`, `Closed`), authorized applicant list review, and applicant status management (`Submitted`, `Under Review`, `Shortlisted`, `Interviewing`, `Rejected`, `Hired`).
   - **Administrator Command Center:** Platform metrics, job moderation queue, employer verification queue, fraud reports, payment audit ledger, and immutable security audit logs.

3. **Audited Payment State Machine**:
   - Implements safe state transitions: `PENDING → VERIFIED → ACTIVE` (with terminal states `FAILED`, `CANCELLED`, `EXPIRED`).
   - User-submitted UPI UTR reference codes enter state `PENDING` in our audited ledger.
   - Transparently discloses local development mode as **Demo / Manual Verification Mode** — zero fake or unverified instant activations!
   - Enforces transaction reference uniqueness, amount verification, and idempotency.

4. **Multi-Criteria Job Discovery & Transparent Match Engine**:
   - Real-time search across roles, skills, employers, and descriptions with debounce.
   - Server-side multi-faceted filtering: Location City, Academic Stream, Qualification, Experience Level, Work Mode (Onsite / Hybrid / Remote), Salary Range.
   - Real database pagination and sorting.
   - Transparent explainable recommendation engine computing scores based on verified technical skills (45%), stream match (25%), location preference (15%), and graduation batch eligibility (15%) with human-readable explanations.

5. **Application Security & Hardening**:
   - PBKDF2-HMAC-SHA256 password hashing via `werkzeug.security`.
   - CSRF protection on all state-changing requests (`POST`, `PUT`, `DELETE`).
   - Brute-force throttling (5 attempts / 15-minute lockout per IP / email).
   - Strict candidate ownership validation: users cannot assign themselves elevated roles or alter their premium status through profile update payloads.
   - Cross-tenant recruiter isolation: recruiters can only access their own postings and applicants.
   - Safe administrator bootstrap procedure (`scripts/bootstrap_admin.py`).

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Git (optional)

### 2. Install Dependencies
In the project directory, install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
Copy-Item .env.example .env
```
*(A default `.env` is already configured for local SQLite execution).*

### 4. Database Setup & Migration
To inspect and migrate the SQLite database with full data preservation:
```bash
python scripts/migrate.py
```

### 5. (Optional) Bootstrap an Administrator
To create or promote an administrator account safely:
```bash
# Interactive mode:
python scripts/bootstrap_admin.py

# Or non-interactively in PowerShell:
$env:ADMIN_EMAIL="admin@jobmitra.in"
$env:ADMIN_NAME="Super Administrator"
$env:ADMIN_PASSWORD="AdminSecretPass2026!"
python scripts/bootstrap_admin.py
```

### 6. Run the Application
Start the Flask development server:
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Demonstration Accounts for Testing

The local database is pre-seeded with three demonstration accounts:

| Role | Email | Password | Dashboard URL |
|---|---|---|---|
| **Candidate** | `aditya.engineer@jobmitra.in` | `Candidate@123` | `http://127.0.0.1:5000/candidate/dashboard` |
| **Recruiter** | `priya.recruiter@technova.in` | `Recruiter@123` | `http://127.0.0.1:5000/recruiter/dashboard` |
| **Admin** | `admin@jobmitra.in` | `AdminSecretPass2026!` | `http://127.0.0.1:5000/admin/dashboard` |

*(Quick 1-click credential fill buttons are also available on the Login page at `/auth/login`)*.

---

## 🧪 Running Automated Tests

Run the full automated test suite using `pytest`:
```bash
python -m pytest tests/ -v
```

Run end-to-end live HTTP route smoke tests:
```bash
python scripts/smoke_test.py
```

---

## 📂 Project Architecture

```
JOB PORTAL 001/
├── app.py                     # Application factory and server entrypoint
├── config.py                  # Environment-based configuration
├── database.py                # Dual SQLite / MySQL database layer with foreign keys
├── security.py                # RBAC decorators, CSRF protection, password hashing
├── matching.py                # Explainable job recommendation engine
├── requirements.txt           # Pinned production and test dependencies
├── .env.example               # Safe environment variable template
├── .env                       # Local environment settings
├── jobmitra_local.db          # Migrated multi-tenant SQLite database
├── routes/
│   ├── auth.py                # Login, Register, Logout, Session state
│   ├── candidate.py           # Candidate dashboard, skills, profile, applications
│   ├── recruiter.py           # Recruiter console, job posting, applicant review
│   ├── admin.py               # Moderation queue, employer verification, payment audit
│   ├── jobs.py                # Job discovery, filters, details, bookmarks, apply, report
│   └── payments.py            # UPI Pro subscription plans, UTR submission (PENDING)
├── templates/
│   ├── base.html              # Base layout with Glassmorphism navigation and modals
│   ├── index.html             # Redesigned homepage
│   ├── jobs/
│   │   ├── index.html         # Dedicated multi-criteria search page
│   │   └── detail.html        # Job details with transparent specs and demo warnings
│   ├── auth/                  # Login, Register, Forgot Password
│   ├── candidate/             # Candidate dashboard
│   ├── recruiter/             # Recruiter dashboard, Post job, Applicant tracker
│   ├── admin/                 # Command center, Moderation, Payments, Employers, Reports
│   └── components/modals/     # Subscription, 1-Click Apply, Send Mail, Report modals
├── static/
│   ├── css/style.css          # Design system stylesheet
│   └── js/app.js              # Client application engine
├── scripts/
│   ├── migrate.py             # Schema migration preserving existing data
│   ├── bootstrap_admin.py     # Administrator creation tool
│   └── smoke_test.py          # End-to-end HTTP smoke test runner
├── tests/                     # 29 automated pytest unit and integration tests
└── docs/
    ├── PROJECT_AUDIT.md       # Initial project audit report
    ├── SECURITY.md            # Application security architecture
    └── TEST_REPORT.md         # Automated test execution report
```

---

## 📄 Documentation

- [Project Audit Report](docs/PROJECT_AUDIT.md)
- [Security Architecture & Controls](docs/SECURITY.md)
- [Automated Test Execution Report](docs/TEST_REPORT.md)
