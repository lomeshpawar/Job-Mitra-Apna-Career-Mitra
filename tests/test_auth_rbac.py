"""
Unit & Integration Tests: Authentication, Registration, Password Hashing & RBAC
"""
import pytest
from database import query_db

def test_candidate_registration(client):
    """Tests new candidate account registration."""
    resp = client.post('/auth/register', data={
        'name': 'New Student',
        'email': 'student.new@test.com',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!',
        'role': 'candidate',
        'phone': '+91 9123456789',
        'stream': 'Computer Science / IT',
        'education': 'B.Tech'
    }, follow_redirects=True)
    assert resp.status_code == 200

    user = query_db("SELECT * FROM users WHERE email = %s", ('student.new@test.com',), one=True)
    assert user is not None
    assert user['role'] == 'candidate'

    # Candidate profile should be auto-created
    cand = query_db("SELECT * FROM candidate_profile WHERE user_id = %s", (user['id'],), one=True)
    assert cand is not None
    assert cand['name'] == 'New Student'
    assert cand['is_premium'] == 0

def test_prevent_self_assign_admin_role(client):
    """Security Check: Users must not be able to assign themselves admin privileges on registration."""
    resp = client.post('/auth/register', data={
        'name': 'Hacker Wannabe',
        'email': 'hacker@test.com',
        'password': 'HackerPassword123!',
        'confirm_password': 'HackerPassword123!',
        'role': 'admin',  # Attempting privilege escalation
        'phone': '+91 9998887776'
    }, follow_redirects=True)

    user = query_db("SELECT * FROM users WHERE email = %s", ('hacker@test.com',), one=True)
    assert user is not None
    # Must be forced to 'candidate', NOT 'admin'
    assert user['role'] == 'candidate'

def test_login_valid_credentials(client):
    """Tests signing in with valid credentials."""
    resp = client.post('/auth/login', data={
        'email': 'candidate@test.com',
        'password': 'TestPassword123!'
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert '/candidate/dashboard' in resp.headers['Location']

def test_login_invalid_password(client):
    """Tests login rejection with wrong password."""
    resp = client.post('/auth/login', data={
        'email': 'candidate@test.com',
        'password': 'WrongPassword123!'
    })
    assert resp.status_code == 401

def test_unauthenticated_access_denied(client):
    """Tests that unauthenticated clients cannot access protected dashboards."""
    resp = client.get('/candidate/dashboard', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']

    api_resp = client.get('/api/jobs/1/bookmark')
    assert api_resp.status_code in (401, 405)

def test_rbac_candidate_cannot_access_recruiter(candidate_client):
    """RBAC: Candidate role must be blocked from recruiter dashboard."""
    resp = candidate_client.get('/recruiter/dashboard')
    assert resp.status_code == 403

def test_rbac_candidate_cannot_access_admin(candidate_client):
    """RBAC: Candidate role must be blocked from admin console."""
    resp = candidate_client.get('/admin/dashboard')
    assert resp.status_code == 403

def test_rbac_recruiter_cannot_access_admin(recruiter_client):
    """RBAC: Recruiter role must be blocked from admin console."""
    resp = recruiter_client.get('/admin/dashboard')
    assert resp.status_code == 403

def test_rbac_admin_has_full_access(admin_client):
    """RBAC: Administrator has access to administrative routes."""
    resp = admin_client.get('/admin/dashboard')
    assert resp.status_code == 200
    assert b"Administrator Command Center" in resp.data
