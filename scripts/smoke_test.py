"""
Job Mitra - Smoke Test Script
Executes end-to-end HTTP request testing across all views and API endpoints against the live local database.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app
from database import query_db

def run_smoke_tests():
    print("=" * 60)
    print(" Running Job Mitra Comprehensive Smoke Tests")
    print("=" * 60)

    client = app.test_client()

    routes_to_test = [
        ('/', 200, "Homepage"),
        ('/jobs', 200, "Search Page"),
        ('/jobs/1', 200, "Job Detail Page (#1)"),
        ('/auth/login', 200, "Login Page"),
        ('/auth/register', 200, "Register Page"),
        ('/auth/forgot-password', 200, "Forgot Password Page"),
        ('/api/jobs', 200, "Jobs API"),
        ('/api/subscription/plans', 200, "Subscription Plans API")
    ]

    all_passed = True

    for url, expected_status, label in routes_to_test:
        resp = client.get(url)
        status_ok = resp.status_code == expected_status
        mark = "PASS" if status_ok else f"FAIL ({resp.status_code})"
        print(f"[{mark}] {label} -> GET {url}")
        if not status_ok:
            all_passed = False

    # Test Candidate Session
    print("\n--- Testing Candidate Authenticated Views ---")
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_email'] = 'aditya.engineer@jobmitra.in'
        sess['user_name'] = 'Aditya Sharma'
        sess['user_role'] = 'candidate'
        sess['_csrf_token'] = 'test-token'

    c_resp = client.get('/candidate/dashboard')
    print(f"[{'PASS' if c_resp.status_code == 200 else 'FAIL'}] Candidate Dashboard -> Status: {c_resp.status_code}")
    if c_resp.status_code != 200: all_passed = False

    # Test Recruiter Session
    print("\n--- Testing Recruiter Authenticated Views ---")
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_email'] = 'priya.recruiter@technova.in'
        sess['user_name'] = 'Priya Verma'
        sess['user_role'] = 'recruiter'
        sess['_csrf_token'] = 'test-token'

    r_resp1 = client.get('/recruiter/dashboard')
    print(f"[{'PASS' if r_resp1.status_code == 200 else 'FAIL'}] Recruiter Dashboard -> Status: {r_resp1.status_code}")
    r_resp2 = client.get('/recruiter/post-job')
    print(f"[{'PASS' if r_resp2.status_code == 200 else 'FAIL'}] Recruiter Post Job -> Status: {r_resp2.status_code}")
    if r_resp1.status_code != 200 or r_resp2.status_code != 200: all_passed = False

    # Test Admin Session
    print("\n--- Testing Administrator Authenticated Views ---")
    with client.session_transaction() as sess:
        sess['user_id'] = 3
        sess['user_email'] = 'admin@jobmitra.in'
        sess['user_name'] = 'Super Administrator'
        sess['user_role'] = 'admin'
        sess['_csrf_token'] = 'test-token'

    admin_urls = [
        ('/admin/dashboard', "Admin Dashboard"),
        ('/admin/moderation', "Job Moderation Queue"),
        ('/admin/payments', "Payment & Subscription Audit"),
        ('/admin/employers', "Employer Verification Queue"),
        ('/admin/reports', "Fraud Reports Queue"),
        ('/admin/audit-logs', "Security Audit Logs")
    ]
    for url, label in admin_urls:
        a_resp = client.get(url)
        status_ok = a_resp.status_code == 200
        print(f"[{'PASS' if status_ok else 'FAIL'}] {label} -> GET {url} (Status: {a_resp.status_code})")
        if not status_ok: all_passed = False

    print("=" * 60)
    if all_passed:
        print(" ALL SMOKE TESTS PASSED CLEANLY (100% OK)!")
    else:
        print(" SOME SMOKE TESTS FAILED. CHECK LOGS ABOVE.")
    print("=" * 60)

if __name__ == '__main__':
    run_smoke_tests()
