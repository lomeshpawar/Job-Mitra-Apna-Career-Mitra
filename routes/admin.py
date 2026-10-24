"""
Job Mitra - Administrator Management Routes
Platform Overview, Moderation Queue, Employer Verification, Payment Audit, and Security Audit Logs.
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session, abort, flash, redirect, url_for
from database import query_db, execute_transaction
from security import admin_required, log_audit, sanitize_text

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Renders Administrator Command Center with platform metrics and quick queues."""
    user_counts = query_db("SELECT role, COUNT(*) AS count FROM users GROUP BY role")
    role_map = {r['role']: r['count'] for r in user_counts}

    total_jobs = query_db("SELECT COUNT(*) AS c FROM jobs", one=True)['c']
    pending_jobs = query_db("SELECT COUNT(*) AS c FROM jobs WHERE status = 'Pending Review'", one=True)['c']
    total_apps = query_db("SELECT COUNT(*) AS c FROM applications", one=True)['c']
    pending_payments = query_db("SELECT COUNT(*) AS c FROM payments WHERE status = 'PENDING'", one=True)['c']
    active_subscriptions = query_db("SELECT COUNT(*) AS c FROM subscriptions WHERE status = 'Active' OR status = 'ACTIVE'", one=True)['c']
    pending_reports = query_db("SELECT COUNT(*) AS c FROM job_reports WHERE status = 'Pending'", one=True)['c']
    unverified_employers = query_db("SELECT COUNT(*) AS c FROM employers WHERE is_verified = 0", one=True)['c']

    recent_jobs = query_db("SELECT * FROM jobs ORDER BY id DESC LIMIT 5")
    recent_payments = query_db("SELECT p.*, u.name AS user_name, u.email AS user_email FROM payments p JOIN users u ON p.user_id = u.id ORDER BY p.id DESC LIMIT 5")
    recent_audits = query_db("SELECT a.*, u.email AS user_email FROM audit_logs a LEFT JOIN users u ON a.user_id = u.id ORDER BY a.id DESC LIMIT 8")

    return render_template(
        'admin/dashboard.html',
        role_map=role_map,
        total_jobs=total_jobs,
        pending_jobs=pending_jobs,
        total_apps=total_apps,
        pending_payments=pending_payments,
        active_subscriptions=active_subscriptions,
        pending_reports=pending_reports,
        unverified_employers=unverified_employers,
        recent_jobs=recent_jobs,
        recent_payments=recent_payments,
        recent_audits=recent_audits
    )

@admin_bp.route('/moderation')
@admin_required
def moderation_queue():
    """Renders job moderation queue."""
    status_filter = request.args.get('status', 'Pending Review')
    jobs = query_db("SELECT j.*, u.name AS recruiter_name, u.email AS recruiter_email FROM jobs j LEFT JOIN users u ON j.recruiter_id = u.id WHERE j.status = %s ORDER BY j.id DESC", (status_filter,))
    return render_template('admin/moderation.html', jobs=jobs, current_status=status_filter)

@admin_bp.route('/api/jobs/<int:job_id>/moderate', methods=['POST'])
@admin_required
def moderate_job(job_id):
    """Approves, rejects, verifies, or closes a job listing."""
    admin_id = session['user_id']
    data = request.json or {}
    action = data.get('action', '').lower()  # 'approve', 'reject', 'verify', 'unverify', 'close'

    job = query_db("SELECT * FROM jobs WHERE id = %s", (job_id,), one=True)
    if not job:
        return jsonify({"success": False, "error": "Job vacancy not found."}), 404

    if action == 'approve':
        query_db("UPDATE jobs SET status = 'Published' WHERE id = %s", (job_id,), commit=True)
        msg = f"Job '{job['title']}' approved and published."
    elif action == 'reject':
        query_db("UPDATE jobs SET status = 'Rejected' WHERE id = %s", (job_id,), commit=True)
        msg = f"Job '{job['title']}' rejected."
    elif action == 'verify':
        query_db("UPDATE jobs SET is_verified = 1 WHERE id = %s", (job_id,), commit=True)
        msg = f"Job '{job['title']}' employer status set to Verified."
    elif action == 'unverify':
        query_db("UPDATE jobs SET is_verified = 0 WHERE id = %s", (job_id,), commit=True)
        msg = f"Job '{job['title']}' employer status set to Unverified."
    elif action == 'close':
        query_db("UPDATE jobs SET status = 'Closed' WHERE id = %s", (job_id,), commit=True)
        msg = f"Job '{job['title']}' closed."
    else:
        return jsonify({"success": False, "error": "Unknown moderation action."}), 400

    log_audit(admin_id, f'JOB_MODERATED_{action.upper()}', 'JOB', str(job_id), msg)
    return jsonify({"success": True, "message": msg})

@admin_bp.route('/payments')
@admin_required
def payments_audit():
    """Renders payment and subscription audit ledger."""
    payments = query_db("""
        SELECT p.*, u.name AS user_name, u.email AS user_email
        FROM payments p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.id DESC
    """)
    subscriptions = query_db("""
        SELECT s.*, u.name AS user_name, u.email AS user_email
        FROM subscriptions s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.id DESC
    """)
    return render_template('admin/payments.html', payments=payments, subscriptions=subscriptions)

@admin_bp.route('/api/payments/<int:payment_id>/verify', methods=['POST'])
@admin_required
def verify_payment_api(payment_id):
    """
    Administrator verifies payment transaction reference and activates candidate Pro subscription.
    Enforces safe state transition: PENDING -> VERIFIED -> ACTIVE (or FAILED).
    """
    admin_id = session['user_id']
    data = request.json or {}
    new_status = data.get('status', '').upper()  # 'ACTIVE', 'FAILED', 'CANCELLED'

    payment = query_db("SELECT * FROM payments WHERE id = %s", (payment_id,), one=True)
    if not payment:
        return jsonify({"success": False, "error": "Payment record not found."}), 404

    if payment['status'] == 'ACTIVE' and new_status == 'ACTIVE':
        return jsonify({"success": False, "error": "Payment is already ACTIVE and verified."}), 400

    if new_status not in ('ACTIVE', 'FAILED', 'CANCELLED', 'EXPIRED'):
        return jsonify({"success": False, "error": "Invalid target status. Must be ACTIVE, FAILED, or CANCELLED."}), 400

    if new_status == 'ACTIVE':
        # Calculate subscription validity
        plan_name = payment['plan_name']
        days = 30
        if '180' in plan_name or 'Career Pro' in plan_name:
            days = 180
        elif 'Lifetime' in plan_name:
            days = 3650  # 10 years

        expires_at = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

        # Atomic transaction: Update payment, activate subscription, update candidate profile
        ops = [
            ("UPDATE payments SET status = 'ACTIVE', verified_at = CURRENT_TIMESTAMP, verified_by = %s WHERE id = %s", (admin_id, payment_id)),
            ("""
                INSERT INTO subscriptions (user_id, payment_id, plan_name, amount, upi_id, utr_number, candidate_email, status, starts_at, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Active', CURRENT_TIMESTAMP, %s)
            """, (payment['user_id'], payment_id, payment['plan_name'], payment['amount'], payment['upi_id'], payment['utr_number'], payment['user_id'], expires_at)),
            ("UPDATE candidate_profile SET is_premium = 1 WHERE user_id = %s", (payment['user_id'],))
        ]
        execute_transaction(ops)

        log_audit(admin_id, 'PAYMENT_VERIFIED_ACTIVE', 'PAYMENT', str(payment_id), f"UTR: {payment['utr_number']}, Amount: {payment['amount']}")
        return jsonify({"success": True, "message": f"Payment {payment['utr_number']} successfully verified! Pro subscription activated."})
    else:
        query_db("UPDATE payments SET status = %s WHERE id = %s", (new_status, payment_id), commit=True)
        log_audit(admin_id, f'PAYMENT_STATUS_{new_status}', 'PAYMENT', str(payment_id), f"Set to {new_status}")
        return jsonify({"success": True, "message": f"Payment status set to {new_status}."})

@admin_bp.route('/employers')
@admin_required
def employer_verification_queue():
    """Renders employer verification queue."""
    employers = query_db("SELECT * FROM employers ORDER BY is_verified ASC, id DESC")
    return render_template('admin/employers.html', employers=employers)

@admin_bp.route('/api/employers/<int:emp_id>/verify', methods=['POST'])
@admin_required
def verify_employer(emp_id):
    """Approves or revokes employer verification badge."""
    admin_id = session['user_id']
    data = request.json or {}
    verify = bool(data.get('verify', True))

    val = 1 if verify else 0
    query_db("UPDATE employers SET is_verified = %s WHERE id = %s", (val, emp_id), commit=True)
    # Also sync verified status to jobs from this employer
    query_db("UPDATE jobs SET is_verified = %s WHERE employer_id = %s", (val, emp_id), commit=True)

    status_str = "Verified" if verify else "Unverified"
    log_audit(admin_id, f'EMPLOYER_{status_str.upper()}', 'EMPLOYER', str(emp_id), f"Employer ID {emp_id} set to {status_str}")
    return jsonify({"success": True, "message": f"Employer successfully set to {status_str}."})

@admin_bp.route('/reports')
@admin_required
def reports_queue():
    """Renders job reports queue."""
    reports = query_db("""
        SELECT r.*, j.title AS job_title, j.company AS job_company, u.email AS reporter_email
        FROM job_reports r
        JOIN jobs j ON r.job_id = j.id
        LEFT JOIN users u ON r.reporter_id = u.id
        ORDER BY r.id DESC
    """)
    return render_template('admin/reports.html', reports=reports)

@admin_bp.route('/api/reports/<int:report_id>/resolve', methods=['POST'])
@admin_required
def resolve_report(report_id):
    """Resolves or dismisses a job fraud report."""
    admin_id = session['user_id']
    data = request.json or {}
    action = data.get('action', 'dismiss')  # 'dismiss' or 'take_down'

    report = query_db("SELECT * FROM job_reports WHERE id = %s", (report_id,), one=True)
    if not report:
        return jsonify({"success": False, "error": "Report not found"}), 404

    if action == 'take_down':
        query_db("UPDATE jobs SET status = 'Rejected' WHERE id = %s", (report['job_id'],), commit=True)
        query_db("UPDATE job_reports SET status = 'Action Taken' WHERE id = %s", (report_id,), commit=True)
        msg = "Job listing removed from public search and marked Rejected."
    else:
        query_db("UPDATE job_reports SET status = 'Dismissed' WHERE id = %s", (report_id,), commit=True)
        msg = "Report marked as Dismissed."

    log_audit(admin_id, f'REPORT_{action.upper()}', 'JOB_REPORT', str(report_id), msg)
    return jsonify({"success": True, "message": msg})

@admin_bp.route('/audit-logs')
@admin_required
def view_audit_logs():
    """Renders system security audit logs."""
    logs = query_db("""
        SELECT a.*, u.email AS user_email, u.role AS user_role
        FROM audit_logs a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.id DESC
        LIMIT 100
    """)
    return render_template('admin/audit_logs.html', logs=logs)
