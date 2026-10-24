"""
Unit & Integration Tests: Candidate Ownership & Privilege Escalation Prevention
"""
import pytest
from database import query_db

def test_candidate_cannot_manipulate_premium_status(candidate_client):
    """
    Critical Security Test (Phase 2 B):
    Candidates must not be able to change their is_premium status through the profile update endpoint.
    """
    # Verify candidate starts as is_premium = 0
    cand_before = query_db("SELECT is_premium FROM candidate_profile WHERE user_id = 1", one=True)
    assert cand_before['is_premium'] == 0

    # Attempt to send is_premium = 1 via payload
    resp = candidate_client.post('/candidate/api/profile', json={
        'name': 'Test Candidate',
        'phone': '+91 9999999999',
        'city': 'Pune',
        'is_premium': 1  # Malicious payload
    })
    assert resp.status_code == 200

    # Database must still have is_premium = 0
    cand_after = query_db("SELECT is_premium, city FROM candidate_profile WHERE user_id = 1", one=True)
    assert cand_after['is_premium'] == 0
    assert cand_after['city'] == 'Pune'  # Valid field updated

def test_candidate_skills_management(candidate_client):
    """Tests dynamically adding and removing technical skills."""
    # Add skill
    resp = candidate_client.post('/candidate/api/skills', json={
        'skill': 'ReactJS',
        'action': 'add'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'ReactJS' in data['skills']

    # Remove skill
    resp2 = candidate_client.post('/candidate/api/skills', json={
        'skill': 'ReactJS',
        'action': 'remove'
    })
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert 'ReactJS' not in data2['skills']

def test_candidate_profile_validation(candidate_client):
    """Tests server-side validation on profile update (e.g. invalid phone number)."""
    resp = candidate_client.post('/candidate/api/profile', json={
        'phone': '123'  # Invalid phone
    })
    assert resp.status_code == 400
    assert b"valid contact number" in resp.data
