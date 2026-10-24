"""
Unit & Integration Tests: Job Search, Multi-Criteria Filtering, and Transparent Matching
"""
import pytest
from matching import compute_job_match

def test_api_jobs_search_by_query(client):
    """Tests keyword search across job title and skills."""
    resp = client.get('/api/jobs?q=Software')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] >= 1
    assert any('Software' in j['title'] for j in data['jobs'])

def test_api_jobs_filter_by_city(client):
    """Tests city location filter."""
    resp = client.get('/api/jobs?city=Bengaluru')
    assert resp.status_code == 200
    data = resp.get_json()
    assert all('Bengaluru' in j['city'] for j in data['jobs'])

def test_api_jobs_filter_by_stream(client):
    """Tests engineering stream discipline filter."""
    resp = client.get('/api/jobs?stream=Computer+Science+%2F+IT')
    assert resp.status_code == 200
    data = resp.get_json()
    assert all('Computer Science' in j['stream'] for j in data['jobs'])

def test_api_jobs_filter_by_min_salary(client):
    """Tests minimum salary threshold filter."""
    resp = client.get('/api/jobs?min_salary=30000')
    assert resp.status_code == 200
    data = resp.get_json()
    assert all(j['salary_max'] >= 30000 for j in data['jobs'])

def test_explainable_matching_engine():
    """
    Transparent Rule-based Job Matching Test (Phase 6):
    Must provide explainable reasons without inventing fake AI models.
    """
    candidate = {
        'skills': 'Python, SQL, Flask, Git',
        'stream': 'Computer Science / IT',
        'city': 'Bengaluru',
        'graduation_year': '2026'
    }
    job = {
        'skills_required': 'Python, Flask, Docker, Kubernetes',
        'stream': 'Computer Science / IT',
        'city': 'Bengaluru',
        'work_mode': 'Onsite',
        'graduation_year': '2025, 2026'
    }

    match_res = compute_job_match(candidate, job)
    assert match_res['score'] >= 70
    assert 'Python' in match_res['matched_skills']
    assert 'Flask' in match_res['matched_skills']
    assert len(match_res['reasons']) >= 3
    # Verify reasons are human-readable
    assert any('skills' in r.lower() for r in match_res['reasons'])
    assert any('stream' in r.lower() for r in match_res['reasons'])
