"""
Unit & Integration Tests: Application & Bookmark Persistence and Duplicate Prevention
"""
import pytest
from database import query_db

def test_apply_to_job(candidate_client):
    """Candidate submits a 1-click application."""
    resp = candidate_client.post('/api/jobs/1/apply', json={
        'cover_note': 'I am ready for immediate interview.'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'submitted' in data['message'].lower()

    # Check persistence
    app = query_db("SELECT * FROM applications WHERE job_id = 1 AND candidate_id = 1", one=True)
    assert app is not None
    assert app['status'] == 'Submitted'
    assert app['cover_note'] == 'I am ready for immediate interview.'

def test_duplicate_application_prevention(candidate_client):
    """
    Data Integrity Test (Phase 3 Requirement 3):
    Prevent duplicate applications to the same job by the same candidate.
    """
    resp = candidate_client.post('/api/jobs/1/apply', json={
        'cover_note': 'Trying to apply again.'
    })
    assert resp.status_code == 409
    assert b"already applied" in resp.data

def test_bookmark_and_unbookmark_toggle(candidate_client):
    """
    Data Integrity Test (Phase 3 Requirement 4):
    Bookmark toggling and duplicate bookmark prevention.
    """
    # 1. Bookmark job
    resp1 = candidate_client.post('/api/jobs/1/bookmark')
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    assert data1['bookmarked'] is True

    bm1 = query_db("SELECT * FROM bookmarks WHERE user_id = 1 AND job_id = 1", one=True)
    assert bm1 is not None

    # 2. Toggle again to un-bookmark
    resp2 = candidate_client.post('/api/jobs/1/bookmark')
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2['bookmarked'] is False

    bm2 = query_db("SELECT * FROM bookmarks WHERE user_id = 1 AND job_id = 1", one=True)
    assert bm2 is None
