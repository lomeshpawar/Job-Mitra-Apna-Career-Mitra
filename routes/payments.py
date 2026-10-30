"""
Job Mitra - Subscription & Payment State Machine Routes
Handles subscription plan discovery, manual UPI reference submission (PENDING),
and payment state verification.
"""
from flask import Blueprint, request, jsonify, session
from config import Config, is_configured_upi_id
from database import query_db
from security import login_required, log_audit, sanitize_text

payments_bp = Blueprint('payments', __name__)

PLANS_CATALOG = [
    {
        "id": "plan_starter",
        "name": "Starter Boost",
        "price": 99,
        "validity": "30 Days",
        "badge": "Budget",
        "perks": [
            "Direct HR WhatsApp & Call Unlock",
            "15 Fast-Track Applications",
            "Candidate Pro Badge"
        ]
    },
    {
        "id": "plan_graduate",
        "name": "Graduate Career Pro",
        "price": 199,
        "validity": "180 Days",
        "badge": "Most Popular",
        "popular": True,
        "perks": [
            "Unlimited Direct HR Calling & Mail",
            "Top 1% Application Priority",
            "Transparent Skill & Eligibility Breakdown",
            "Dedicated Job Alert Updates"
        ]
    },
    {
        "id": "plan_lifetime",
        "name": "Lifetime Placement Pass",
        "price": 499,
        "validity": "Lifetime (10 Yrs)",
        "badge": "Best Value",
        "perks": [
            "Permanent Pro Status",
            "MNC Recruiter Direct Access",
            "Career Counselor Guidance",
            "Guaranteed Profile Verification"
        ]
    }
]

@payments_bp.route('/api/subscription/plans', methods=['GET'])
def get_plans():
    """Returns available plans and active payment mode information."""
    upi_id = Config.UPI_ID if is_configured_upi_id(Config.UPI_ID) else ""
    return jsonify({
        "upi_id": upi_id,
        "payment_configured": bool(upi_id),
        "gateway_live": Config.PAYMENT_GATEWAY_LIVE,
        "gateway_name": Config.PAYMENT_GATEWAY_NAME,
        "mode": "DEMO_MANUAL_VERIFICATION" if not Config.PAYMENT_GATEWAY_LIVE else "LIVE_GATEWAY",
        "plans": PLANS_CATALOG
    })

@payments_bp.route('/api/subscription/activate', methods=['POST'])
@login_required
def submit_payment_reference():
    """
    Submits a payment reference / UTR for verification.
    CRITICAL SECURITY CONTROLS:
    1. Reference is strictly marked 'PENDING' - never automatically activated!
    2. Enforces UTR uniqueness to prevent replay / duplicate submissions.
    3. Validates amount against catalog.
    4. Explicitly labels the process as Demo / Manual Verification.
    5. Returns transparent status to candidate.
    """
    if not is_configured_upi_id(Config.UPI_ID):
        return jsonify({
            "success": False,
            "error": "UPI payment is not configured. Payment reference submission is temporarily unavailable."
        }), 503

    user_id = session['user_id']
    data = request.json or {}
    utr = sanitize_text(data.get('utr_number', ''), 100).strip()
    plan_name = sanitize_text(data.get('plan_name', 'Graduate Career Pro'), 100)
    amount = data.get('amount')

    # Validate plan & amount
    matched_plan = next((p for p in PLANS_CATALOG if p['name'].lower() == plan_name.lower()), None)
    if not matched_plan:
        return jsonify({"success": False, "error": f"Invalid subscription plan '{plan_name}'."}), 400

    expected_amount = matched_plan['price']
    if amount and int(amount) != expected_amount:
        return jsonify({"success": False, "error": f"Incorrect amount submitted. Expected ₹{expected_amount} for {matched_plan['name']}."}), 400

    amount = expected_amount

    # Validate UTR length and format
    if not utr or len(utr) < 8 or not utr.isalnum():
        return jsonify({"success": False, "error": "Please enter a valid 12-digit UPI Transaction Reference / UTR (alphanumeric)."}), 400

    # Idempotency / Duplicate reference check
    existing_utr = query_db("SELECT id, status, user_id FROM payments WHERE utr_number = %s", (utr,), one=True)
    if existing_utr:
        if existing_utr['user_id'] == user_id:
            return jsonify({
                "success": False,
                "error": f"You have already submitted this UTR. Current status: {existing_utr['status']}."
            }), 409
        else:
            return jsonify({
                "success": False,
                "error": "This transaction reference has already been claimed by another account."
            }), 409

    try:
        # Create payment record in PENDING state
        payment_id = query_db("""
            INSERT INTO payments (user_id, plan_name, amount, currency, upi_id, utr_number, status, payment_mode, notes)
            VALUES (%s, %s, %s, 'INR', %s, %s, 'PENDING', 'UPI', 'Manual reference submitted by candidate')
        """, (user_id, matched_plan['name'], amount, Config.UPI_ID, utr), commit=True)

        log_audit(user_id, 'PAYMENT_SUBMITTED_PENDING', 'PAYMENT', str(payment_id), f"Plan: {matched_plan['name']}, UTR: {utr}")

        return jsonify({
            "success": True,
            "status": "PENDING",
            "payment_id": payment_id,
            "message": (
                f"Payment reference {utr} submitted successfully. "
                "Status: PENDING verification. Because Job Mitra operates in Demo / Manual Verification mode, "
                "an administrator will verify the bank transaction before Pro access is activated."
            ),
            "plan_name": matched_plan['name'],
            "amount": amount,
            "utr": utr,
            "verification_mode": "MANUAL_DEMO_VERIFICATION"
        })
    except Exception as e:
        print(f"[Payment Error] {e}")
        return jsonify({"success": False, "error": "Could not record payment reference. Please try again."}), 500

@payments_bp.route('/api/subscription/status', methods=['GET'])
@login_required
def check_subscription_status():
    """Returns candidate's subscription history and current status."""
    user_id = session['user_id']
    cand = query_db("SELECT is_premium FROM candidate_profile WHERE user_id = %s", (user_id,), one=True)
    is_premium = bool(cand['is_premium']) if cand else False

    recent_payments = query_db("""
        SELECT id, plan_name, amount, utr_number, status, created_at, verified_at
        FROM payments
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 5
    """, (user_id,))

    active_sub = query_db("""
        SELECT * FROM subscriptions
        WHERE user_id = %s AND (status = 'Active' OR status = 'ACTIVE')
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,), one=True)

    return jsonify({
        "is_premium": is_premium,
        "active_subscription": active_sub,
        "recent_payments": recent_payments
    })
