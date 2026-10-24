# Project Audit Report: Job Mitra (Apna Career Mitra)

**Audit Date:** October 2026  
**Audited Codebase:** Job Mitra — Job Portal for Freshers and IT Job Seekers  
**Stack:** Python Flask, HTML5, CSS3, JavaScript, SQLite / MySQL  
**Auditor:** Senior Full-Stack Developer & Application Security Engineer  

---

## 1. Executive Summary

A comprehensive architectural, security, database, and user interface audit was performed on the existing Job Mitra repository. The application was previously conceived as a minimal prototype ("under 500 lines of Python code") with a single HTML template and monolithic JavaScript file. 

While the concept of providing freshers and engineering graduates with direct career opportunities is strong, the codebase possessed **critical security vulnerabilities, lack of authentication and access control, severe data integrity flaws, misleading verification badges, and an insecure mock payment flow**.

---

## 2. High-Severity Security Vulnerabilities

### 2.1 Complete Absence of Authentication & Role-Based Access Control (RBAC)
- **Vulnerability:** There were zero registration, login, logout, password hashing, or session validation routines.
- **Impact:** Any unauthenticated client could access, read, and mutate any profile data, post public job vacancies, or view applications.
- **Remediation:** Implement standard secure session-based authentication with `werkzeug.security` (PBKDF2/scrypt password hashing), CSRF token protection, and decorators (`@login_required`, `@roles_accepted('candidate', 'recruiter', 'admin')`).

### 2.2 Client-Side Profile & Privilege Escalation
- **Vulnerability:** In `POST /api/candidate`, the handler accepted `{ "is_premium": 1 }` directly from the request body and updated `candidate_profile` unconditionally.
- **Impact:** Candidates could freely grant themselves "Pro" status without verification or payment.
- **Remediation:** Strip privileged attributes (`is_premium`, `role`, `is_verified`) from candidate-accessible endpoints; make subscription status purely backend-state-driven.

### 2.3 Fabricated Payment & UTR Verification Bypass
- **Vulnerability:** `POST /api/subscription/activate` accepted any arbitrary string with `len(utr) >= 6` and immediately marked the subscription as `Active` and `is_premium=1`.
- **Impact:** Financial bypass: any visitor entering a dummy string like `"123456"` unlocked premium perks immediately with zero bank or gateway verification.
- **Remediation:** Introduce a formal payment state machine:  
  `PENDING → VERIFIED → ACTIVE` (with terminal states `FAILED`, `CANCELLED`, `EXPIRED`).
  Because live gateway keys are not provisioned in the local environment, transactions must be stored as `PENDING` with explicit labels as "Demo / Manual Admin Verification" mode. Never fabricate bank confirmation.

### 2.4 Unauthenticated Job Posting with Auto-Verified Status
- **Vulnerability:** `POST /api/jobs` allowed unauthenticated users to inject job listings directly into the database with `is_verified = 1` hardcoded on line 436.
- **Impact:** Spammers or malicious actors could flood the portal with fake job postings and phishing links that displayed trusted "Verified Employer" badges.
- **Remediation:** Restrict job creation to authenticated recruiters or admins. New jobs default to `status = 'Pending Review'` and `is_verified = 0`. An administrator must approve or reject listings via a moderation queue.

### 2.5 Hardcoded Secrets & Production Debug Mode
- **Vulnerability:** Default fallback secret `'jobmitra-secret-2026'` hardcoded in `app.py`. Flask launched with `debug=True` binding to `0.0.0.0`.
- **Impact:** Werkzeug interactive debugger could expose arbitrary remote code execution (RCE) in production if exposed.
- **Remediation:** Require dynamic `SECRET_KEY` from `.env`, enforce `debug=False` unless explicitly set in development, enforce secure cookies (`HttpOnly`, `SameSite=Lax`).

---

## 3. Database & Data Integrity Deficiencies

### 3.1 Single-Tenant Candidate Profile Flaw
- **Vulnerability:** `candidate_profile` table stored a single row (`WHERE id=1` hardcoded in `app.py`).
- **Impact:** The database could only accommodate one single candidate across the entire platform. Multiple users overwrote each other's data.
- **Remediation:** Introduce a relational `users` table with multi-tenant `candidate_profiles` linked via `user_id` foreign key.

### 3.2 Broken Bookmark Constraints
- **Vulnerability:** `bookmarks` table defined `job_id INT NOT NULL UNIQUE`.
- **Impact:** Across the entire application, only *one candidate total* could bookmark any given job! If candidate A saved job 1, candidate B was blocked with a database constraint error.
- **Remediation:** Change bookmark constraint to `UNIQUE(user_id, job_id)` with proper cascade foreign keys.

### 3.3 Foreign Key Enforcement in SQLite
- **Vulnerability:** SQLite does not enable foreign key constraint checks unless `PRAGMA foreign_keys = ON;` is explicitly executed per connection.
- **Impact:** Orphaned records in `applications`, `bookmarks`, and `sent_emails`.
- **Remediation:** Enable foreign keys on SQLite connection hook.

### 3.4 Missing Logical Entities
The existing database schema lacked essential entities required for a modern SaaS job portal:
- `users` (id, email, password_hash, role, is_active, created_at)
- `recruiter_profiles` (id, user_id, company_name, designation, verified_employer)
- `employers` (id, name, website, logo, description, verification_status)
- `skills` and `candidate_skills` (normalized relationship)
- `audit_logs` (tracking admin approvals, payment status changes, moderation)
- `job_reports` (candidate safety mechanism to report fraudulent listings)

### 3.5 Misleading Pre-Seeded Demonstration Data
- **Vulnerability:** 15 pre-seeded job vacancies used fictitious recruiter emails (`@technova.in`, `@bharatprecision.com`) and phone numbers while displaying "100% Verified Employer" badges.
- **Impact:** Misleads freshers into thinking fictitious companies are verified partners.
- **Remediation:** Add an `is_demo TINYINT DEFAULT 1` column to jobs. Visually label demonstration listings with a "Sample / Demo Opening" badge and remove false "Verified Employer" assertions from unverified mock listings.

---

## 4. Frontend & User Interface Limitations

### 4.1 Monolithic Structure
- The entire frontend existed in a single 945-line `index.html` file using tab toggling, lacking separate views for Job Search, Job Details, Recruiter Management, Admin Moderation, and Authentication.

### 4.2 Missing Authentication & Management Interfaces
- No Login, Registration, Password Reset views.
- No Recruiter Dashboard for managing job vacancies, applicant review, and status updates (`Applied`, `Shortlisted`, `Interviewing`, `Rejected`, `Hired`).
- No Administrator Dashboard for user management, employer verification, job moderation, and payment audits.

### 4.3 Design Inconsistencies
- The previous theme lacked cohesive design tokens, relying on arbitrary utility classes.
- Required redesign: **Premium Glassmorphism + Modern SaaS** utilizing:
  - Deep dark canvas: `#0B1020`
  - Secondary surface: `#111827`
  - Accents: Indigo `#6366F1`, Violet `#8B5CF6`, Royal Blue `#2563EB`
  - High-contrast typography: Inter / System Sans (`#F8FAFC`, `#94A3B8`)
  - Translucent glass panels with restrained backdrop blur.

---

## 5. Summary of Remediation Plan

| Phase | Objective | Status |
|---|---|---|
| **Phase 1** | Complete project audit & report (`docs/PROJECT_AUDIT.md`) | Completed |
| **Phase 2** | Security hardening: Auth, RBAC, CSRF, Payment state machine, Secure cookies | Next |
| **Phase 3** | Database migration: Multi-tenant schema, Foreign keys, Demo labeling, Backups | Planned |
| **Phase 4** | UI redesign: Premium Glassmorphism + Modern SaaS, Multi-view templates | Planned |
| **Phase 5** | Frontend functionality: Real filters, pagination, applications, bookmarks | Planned |
| **Phase 6** | Explainable job matching engine & fraud reporting | Planned |
| **Phase 7** | Clean modular architecture: Blueprints, config, `.env.example`, `requirements.txt` | Planned |
| **Phase 8** | Comprehensive automated test suite (`pytest`) | Planned |
| **Phase 9** | Documentation: `README.md`, `SECURITY.md`, `TEST_REPORT.md` | Planned |
