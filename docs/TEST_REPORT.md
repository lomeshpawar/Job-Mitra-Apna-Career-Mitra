# Job Mitra — Automated Test Execution Report

**Latest PR #3 CI verification:** **45/45 passed** on Python 3.14.9 / Ubuntu 24.04 in 0.76 seconds. [GitHub Actions run #41108659165](https://github.com/lomeshpawar/Job-Mitra-Apna-Career-Mitra/actions/runs/41108659165).  
**Historical local execution:** 29/29 passed in 2.30 seconds with Python 3.14.8, Pytest 9.1.1, Flask 3.1.3, and SQLite 3.  

---

## GitHub Actions verification — 30 October 2026

- Workflow: **Python CI**
- Pull request: [#3 — Reject placeholder session and payment configuration](https://github.com/lomeshpawar/Job-Mitra-Apna-Career-Mitra/pull/3)
- Latest completed PR head: `42854a392f73e0a0c690310c8aa0de5094db5795`
- Runner: Ubuntu 24.04
- Python: 3.14.9
- Application and test-module compilation: passed
- Pytest: **45 passed in 0.76s**

The current CI suite includes the original 29 tests plus 16 configuration and payment checks for missing/placeholder session keys, UPI destination handling, app-startup validation, and payment-submission fail-closed behavior. This result is from GitHub Actions, not a local execution claim.

## Historical local execution summary

The detailed test listing below records the original 29-test local run. The additional 14 CI test cases are summarized above.

## Historical test-case listing

A comprehensive automated test suite and live end-to-end smoke test runner were executed to verify all bug fixes, security controls, database constraints, role-based access rules, payment state transitions, and UI routes.

```
============================= test session starts =============================
platform win32 -- Python 3.14.8, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Lomesh Pawar\Downloads\JOB PORTAL 001
collected 29 items

tests/test_applications_bookmarks.py::test_apply_to_job PASSED           [  3%]
tests/test_applications_bookmarks.py::test_duplicate_application_prevention PASSED [  6%]
tests/test_applications_bookmarks.py::test_bookmark_and_unbookmark_toggle PASSED [ 10%]
tests/test_auth_rbac.py::test_candidate_registration PASSED              [ 13%]
tests/test_auth_rbac.py::test_prevent_self_assign_admin_role PASSED      [ 17%]
tests/test_auth_rbac.py::test_login_valid_credentials PASSED             [ 20%]
tests/test_auth_rbac.py::test_login_invalid_password PASSED              [ 24%]
tests/test_auth_rbac.py::test_unauthenticated_access_denied PASSED       [ 27%]
tests/test_auth_rbac.py::test_rbac_candidate_cannot_access_recruiter PASSED [ 31%]
tests/test_auth_rbac.py::test_rbac_candidate_cannot_access_admin PASSED  [ 34%]
tests/test_auth_rbac.py::test_rbac_recruiter_cannot_access_admin PASSED  [ 37%]
tests/test_auth_rbac.py::test_rbac_admin_has_full_access PASSED          [ 41%]
tests/test_candidate_ownership.py::test_candidate_cannot_manipulate_premium_status PASSED [ 44%]
tests/test_candidate_ownership.py::test_candidate_skills_management PASSED [ 48%]
tests/test_candidate_ownership.py::test_candidate_profile_validation PASSED [ 51%]
tests/test_job_search_filters.py::test_api_jobs_search_by_query PASSED   [ 55%]
tests/test_job_search_filters.py::test_api_jobs_filter_by_city PASSED    [ 58%]
tests/test_job_search_filters.py::test_api_jobs_filter_by_stream PASSED  [ 62%]
tests/test_job_search_filters.py::test_api_jobs_filter_by_min_salary PASSED [ 65%]
tests/test_job_search_filters.py::test_explainable_matching_engine PASSED [ 68%]
tests/test_payment_state_machine.py::test_utr_submission_creates_pending_payment PASSED [ 72%]
tests/test_payment_state_machine.py::test_duplicate_utr_submission_rejected PASSED [ 75%]
tests/test_payment_state_machine.py::test_invalid_utr_length_rejected PASSED [ 79%]
tests/test_payment_state_machine.py::test_admin_payment_verification_activates_pro PASSED [ 82%]
tests/test_recruiter_workflow.py::test_recruiter_job_posting_defaults_to_pending PASSED [ 86%]
tests/test_recruiter_workflow.py::test_recruiter_views_own_job_applicants PASSED [ 89%]
tests/test_recruiter_workflow.py::test_cross_tenant_recruiter_isolation PASSED [ 93%]
tests/test_security_csrf.py::test_input_validation_helpers PASSED        [ 96%]
tests/test_security_csrf.py::test_csrf_validation_enforcement PASSED     [100%]

============================= 29 passed in 2.30s ==============================
```

---

## Test Suite Breakdown by Security & Functional Area

### 2.1 Authentication & Role-Based Access Control (`tests/test_auth_rbac.py`)
| Test Case | Description | Result |
|---|---|:---:|
| `test_candidate_registration` | Verifies candidate registration, password hashing, and profile auto-creation | ✅ PASS |
| `test_prevent_self_assign_admin_role` | Security Check: Blocks clients from registering with role `admin` | ✅ PASS |
| `test_login_valid_credentials` | Verifies session generation and correct role redirect | ✅ PASS |
| `test_login_invalid_password` | Verifies rejection of incorrect password with HTTP 401 | ✅ PASS |
| `test_unauthenticated_access_denied` | Verifies unauthenticated redirects to login or HTTP 401 | ✅ PASS |
| `test_rbac_candidate_cannot_access_recruiter` | Verifies candidates receive HTTP 403 on recruiter dashboard | ✅ PASS |
| `test_rbac_candidate_cannot_access_admin` | Verifies candidates receive HTTP 403 on admin dashboard | ✅ PASS |
| `test_rbac_recruiter_cannot_access_admin` | Verifies recruiters receive HTTP 403 on admin dashboard | ✅ PASS |
| `test_rbac_admin_has_full_access` | Verifies administrators have full access to management consoles | ✅ PASS |

### 2.2 Candidate Ownership & Escalation Prevention (`tests/test_candidate_ownership.py`)
| Test Case | Description | Result |
|---|---|:---:|
| `test_candidate_cannot_manipulate_premium_status` | Security Check: Prevents clients from setting `is_premium=1` via profile payload | ✅ PASS |
| `test_candidate_skills_management` | Verifies dynamic addition and removal of candidate technical skills | ✅ PASS |
| `test_candidate_profile_validation` | Verifies server-side validation on profile contact numbers | ✅ PASS |

### 2.3 Payment State Machine (`tests/test_payment_state_machine.py`)
| Test Case | Description | Result |
|---|---|:---:|
| `test_utr_submission_creates_pending_payment` | Security Check: Submitting UTR enters state `PENDING` and does NOT grant Pro | ✅ PASS |
| `test_duplicate_utr_submission_rejected` | Anti-Replay: Prevents duplicate reference submissions (HTTP 409) | ✅ PASS |
| `test_invalid_utr_length_rejected` | Validates minimum length and alphanumeric format of transaction reference | ✅ PASS |
| `test_admin_payment_verification_activates_pro` | Verifies administrator can verify transaction and transition state to `ACTIVE` | ✅ PASS |

### 2.4 Application & Bookmark Persistence (`tests/test_applications_bookmarks.py`)
| Test Case | Description | Result |
|---|---|:---:|
| `test_apply_to_job` | Verifies 1-click application persistence in SQLite database | ✅ PASS |
| `test_duplicate_application_prevention` | Data Integrity: Prevents duplicate application to same job by same candidate | ✅ PASS |
| `test_bookmark_and_unbookmark_toggle` | Verifies bookmark toggle and unique constraint on `(user_id, job_id)` | ✅ PASS |

### 2.5 Recruiter Workflow & Cross-Tenant Isolation (`tests/test_recruiter_workflow.py`)
| Test Case | Description | Result |
|---|---|:---:|
| `test_recruiter_job_posting_defaults_to_pending` | Verifies new recruiter job listings default to `Pending Review` & `is_verified=0` | ✅ PASS |
| `test_recruiter_views_own_job_applicants` | Verifies recruiters can view submitted applicant details for their postings | ✅ PASS |
| `test_cross_tenant_recruiter_isolation` | Cross-Tenant Security: Recruiter B cannot view or update Recruiter A's postings | ✅ PASS |

### 2.6 Job Search & Matching Engine (`tests/test_job_search_filters.py`)
| Test Case | Description | Result |
|---|---|:---:|
| `test_api_jobs_search_by_query` | Keyword search across titles, skills, and descriptions | ✅ PASS |
| `test_api_jobs_filter_by_city` | Filters vacancies by location city | ✅ PASS |
| `test_api_jobs_filter_by_stream` | Filters vacancies by academic engineering stream | ✅ PASS |
| `test_api_jobs_filter_by_min_salary` | Filters vacancies by minimum salary package | ✅ PASS |
| `test_explainable_matching_engine` | Verifies explainable transparent recommendations without fake AI | ✅ PASS |

### 2.7 CSRF Protection & Input Sanitization (`tests/test_security_csrf.py`)
| Test Case | Description | Result |
|---|---|:---:|
| `test_input_validation_helpers` | Format validation for emails, phone numbers, and string clipping | ✅ PASS |
| `test_csrf_validation_enforcement` | Blocks state-changing requests lacking matching `X-CSRF-Token` | ✅ PASS |

---

## 3. End-to-End Live HTTP Smoke Tests (`scripts/smoke_test.py`)

All 12 live HTTP routes tested against the running local database:
- `[PASS]` Homepage (`GET /`)
- `[PASS]` Search Page (`GET /jobs`)
- `[PASS]` Job Detail Page (`GET /jobs/1`)
- `[PASS]` Login Page (`GET /auth/login`)
- `[PASS]` Register Page (`GET /auth/register`)
- `[PASS]` Forgot Password Page (`GET /auth/forgot-password`)
- `[PASS]` Jobs API (`GET /api/jobs`)
- `[PASS]` Subscription Plans API (`GET /api/subscription/plans`)
- `[PASS]` Candidate Dashboard (`GET /candidate/dashboard`)
- `[PASS]` Recruiter Dashboard (`GET /recruiter/dashboard`)
- `[PASS]` Recruiter Post Vacancy (`GET /recruiter/post-job`)
- `[PASS]` Admin Dashboard (`GET /admin/dashboard`)
- `[PASS]` Admin Moderation Queue (`GET /admin/moderation`)
- `[PASS]` Admin Payment Audit (`GET /admin/payments`)
- `[PASS]` Admin Employer Verification (`GET /admin/employers`)
- `[PASS]` Admin Fraud Reports (`GET /admin/reports`)
- `[PASS]` Admin Security Audit Logs (`GET /admin/audit-logs`)
