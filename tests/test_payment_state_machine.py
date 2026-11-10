"""
Unit & Integration Tests: Payment Verification State Machine
PENDING -> VERIFIED -> ACTIVE (Failure: FAILED, CANCELLED)
"""
import pytest
from database import query_db
from config import Config

def test_utr_submission_creates_pending_payment(candidate_client):
    """
    Critical Security Test (Phase 2 C):
    The existing UTR-based flow must NOT activate Pro merely because user submits a reference number.
    It must create a record in state PENDING.
    """
    utr_code = "998877665544"
    resp = candidate_client.post('/api/subscription/activate', json={
        'utr_number': utr_code,
        'plan_name': 'Graduate Career Pro',
        'amount': 199
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['status'] == 'PENDING'
    assert 'PENDING verification' in data['message']

    # Verify payment in DB is PENDING
    payment = query_db("SELECT * FROM payments WHERE utr_number = %s", (utr_code,), one=True)
    assert payment is not None
    assert payment['status'] == 'PENDING'

    # Candidate profile MUST NOT be activated as Pro yet!
    cand = query_db("SELECT is_premium FROM candidate_profile WHERE user_id = 1", one=True)
    assert cand['is_premium'] == 0

def test_duplicate_utr_submission_rejected(candidate_client):
    """Prevents duplicate/replay submissions with the same reference number."""
    utr_code = "998877665544"
    resp = candidate_client.post('/api/subscription/activate', json={
        'utr_number': utr_code,
        'plan_name': 'Graduate Career Pro',
        'amount': 199
    })
    assert resp.status_code == 409
    assert b"already submitted this UTR" in resp.data

def test_invalid_utr_length_rejected(candidate_client):
    """Rejects invalid or too short UTR strings."""
    resp = candidate_client.post('/api/subscription/activate', json={
        'utr_number': '123',  # Too short
        'plan_name': 'Graduate Career Pro',
        'amount': 199
    })
    assert resp.status_code == 400

def test_payment_reference_rejected_when_upi_destination_is_unconfigured(candidate_client, monkeypatch):
    """Payment references must not be accepted when no merchant destination is configured."""
    monkeypatch.setattr(Config, "UPI_ID", "your-business-upi@bank")

    response = candidate_client.post('/api/subscription/activate', json={
        'utr_number': '123456789012',
        'plan_name': 'Graduate Career Pro',
        'amount': 199
    })

    assert response.status_code == 503
    assert response.get_json()['success'] is False
    assert 'not configured' in response.get_json()['error'].lower()


def test_plan_response_marks_placeholder_upi_as_unconfigured(client, monkeypatch):
    """The public plans API must not present the example UPI value as a live destination."""
    monkeypatch.setattr(Config, "UPI_ID", "your-business-upi@bank")

    response = client.get('/api/subscription/plans')

    assert response.status_code == 200
    assert response.get_json()['upi_id'] == ""
    assert response.get_json()['payment_configured'] is False


def test_admin_payment_verification_activates_pro(admin_client):
    """
    Admin verification workflow:
    Admin inspects pending payment and transitions state to ACTIVE.
    This atomically activates the candidate's Pro subscription.
    """
    # Grab the pending payment created in previous test
    payment = query_db("SELECT id, user_id FROM payments WHERE status = 'PENDING' LIMIT 1", one=True)
    assert payment is not None
    pid = payment['id']

    # Admin verifies payment
    resp = admin_client.post(f'/admin/api/payments/{pid}/verify', json={
        'status': 'ACTIVE'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'verified' in data['message'].lower()

    # DB state must now be ACTIVE
    p_after = query_db("SELECT status, verified_by FROM payments WHERE id = %s", (pid,), one=True)
    assert p_after['status'] == 'ACTIVE'
    assert p_after['verified_by'] == 3  # Admin ID

    # Candidate profile must now have is_premium = 1
    cand_after = query_db("SELECT is_premium FROM candidate_profile WHERE user_id = %s", (payment['user_id'],), one=True)
    assert cand_after['is_premium'] == 1
