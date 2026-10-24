"""
Unit & Integration Tests: Recruiter Workflow & Cross-Tenant Isolation
"""
import pytest
from database import query_db

def test_recruiter_job_posting_defaults_to_pending(recruiter_client):
    """
    Recruiter posting a job must default to 'Pending Review' and is_verified = 0.
    Must not auto-verify untrusted postings!
    """
    resp = recruiter_client.post('/recruiter/post-job', data={
        'title': 'Junior CAD Draftsman',
        'company': 'Bharat Precision AutoWorks',
        'stream': 'Mechanical Engineering',
        'qualification': 'B.Tech Mechanical / Diploma',
        'city': 'Pune',
        'work_mode': 'Onsite',
        'salary_min': 25000,
        'salary_max': 35000,
        'experience': 'Freshers / 0-1 yr',
        'job_type': 'Full Time',
        'skills_required': 'AutoCAD, SolidWorks',
        'hr_email': 'hr@bharatprecision.com',
        'hr_phone': '+91 20 12345678',
        'address': 'MIDC Bhosari, Pune',
        'description': 'Hands on 3D CAD modeling position.'
    }, follow_redirects=True)
    assert resp.status_code == 200

    job = query_db("SELECT * FROM jobs WHERE title = 'Junior CAD Draftsman'", one=True)
    assert job is not None
    assert job['status'] == 'Pending Review'
    assert job['is_verified'] == 0
    assert job['recruiter_id'] == 2  # Belongs to logged in recruiter

def test_recruiter_views_own_job_applicants(recruiter_client):
    """Recruiter can view applicant roster for their own posting."""
    resp = recruiter_client.get('/recruiter/jobs/1/applicants')
    assert resp.status_code == 200
    assert b"Submitted Candidate Applications" in resp.data

def test_cross_tenant_recruiter_isolation(app_instance):
    """
    Cross-Tenant Isolation Test (Phase 2 A):
    Recruiter B cannot view applicants or update status of Recruiter A's postings.
    """
    # Create Recruiter B
    client_b = app_instance.test_client()
    with client_b.session_transaction() as sess:
        sess['user_id'] = 99
        sess['user_email'] = 'recruiter_b@test.com'
        sess['user_name'] = 'Recruiter B'
        sess['user_role'] = 'recruiter'
        sess['_csrf_token'] = 'test-csrf-token'

    # Recruiter B tries to view applicants for job 1 (owned by recruiter 2)
    resp = client_b.get('/recruiter/jobs/1/applicants')
    assert resp.status_code == 403

    # Recruiter B tries to update applicant status for job 1
    resp2 = client_b.post('/recruiter/api/applications/1/status', json={
        'status': 'Hired'
    })
    assert resp2.status_code == 403
