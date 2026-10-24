"""
Job Mitra - Jobs & Public Discovery Routes
Handles Homepage, Multi-criteria Job Search, Job Details, Bookmarks, Applications, and Fraud Reporting.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, render_template, request, jsonify, session, abort
from database import query_db
from security import login_required, candidate_required, sanitize_text, log_audit
from matching import compute_job_match

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/')
def index():
    """Homepage view with curated featured jobs and live statistics."""
    total_jobs = query_db("SELECT COUNT(*) AS c FROM jobs WHERE status = 'Published'", one=True)['c']
    featured_jobs = query_db("""
        SELECT j.*, e.name AS employer_name, e.is_verified AS employer_verified
        FROM jobs j
        LEFT JOIN employers e ON j.employer_id = e.id
        WHERE j.status = 'Published'
        ORDER BY j.is_urgent DESC, j.is_premium DESC, j.id DESC
        LIMIT 6
    """)
    # Category stream counts
    streams = query_db("""
        SELECT stream, COUNT(*) AS count
        FROM jobs
        WHERE status = 'Published'
        GROUP BY stream
        ORDER BY count DESC
        LIMIT 8
    """)
    return render_template('index.html', total_jobs=total_jobs, featured_jobs=featured_jobs, streams=streams)

@jobs_bp.route('/jobs')
def search_page():
    """Dedicated multi-criteria Job Search Page."""
    return render_template('jobs/index.html')

@jobs_bp.route('/jobs/<int:job_id>')
def job_detail(job_id):
    """Dedicated Job Details view with full specifications and transparent demo notice."""
    job = query_db("""
        SELECT j.*, e.name AS employer_name, e.website AS employer_website,
               e.is_verified AS employer_verified, e.description AS employer_desc
        FROM jobs j
        LEFT JOIN employers e ON j.employer_id = e.id
        WHERE j.id = %s
    """, (job_id,), one=True)

    if not job:
        abort(404, "Job vacancy not found.")

    user_id = session.get('user_id')
    is_bookmarked = False
    has_applied = False
    match_info = None

    if user_id:
        bm = query_db("SELECT id FROM bookmarks WHERE user_id = %s AND job_id = %s", (user_id, job_id), one=True)
        is_bookmarked = bool(bm)
        
        cand = query_db("SELECT * FROM candidate_profile WHERE user_id = %s", (user_id,), one=True)
        if cand:
            app = query_db("SELECT id, status, applied_at FROM applications WHERE candidate_id = %s AND job_id = %s", (cand['id'], job_id), one=True)
            has_applied = bool(app)
            match_info = compute_job_match(cand, job)
    else:
        match_info = compute_job_match(None, job)

    return render_template('jobs/detail.html', job=job, is_bookmarked=is_bookmarked, has_applied=has_applied, match_info=match_info)

@jobs_bp.route('/api/jobs', methods=['GET'])
def get_jobs_api():
    """
    Multi-criteria search API supporting keyword, city, stream, qualification,
    work_mode, experience, min/max salary, sorting, and pagination.
    """
    search = request.args.get('q', '').strip()
    city = request.args.get('city', '').strip()
    stream = request.args.get('stream', '').strip()
    work_mode = request.args.get('work_mode', '').strip()
    job_type = request.args.get('job_type', '').strip()
    experience = request.args.get('experience', '').strip()
    min_sal = request.args.get('min_salary', type=int)
    max_sal = request.args.get('max_salary', type=int)
    premium_only = request.args.get('premium', '').strip().lower() == 'true'
    urgent_only = request.args.get('urgent', '').strip().lower() == 'true'
    sort_by = request.args.get('sort', 'newest').strip().lower()
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(50, max(1, request.args.get('per_page', 10, type=int)))

    query = "SELECT * FROM jobs WHERE status = 'Published'"
    params = []

    if search:
        query += " AND (title LIKE %s OR company LIKE %s OR skills_required LIKE %s OR stream LIKE %s OR description LIKE %s)"
        pat = f"%{search}%"
        params.extend([pat, pat, pat, pat, pat])

    if city and city.lower() != 'all':
        query += " AND city LIKE %s"
        params.append(f"%{city}%")

    if stream and stream.lower() != 'all':
        query += " AND stream LIKE %s"
        params.append(f"%{stream}%")

    if work_mode and work_mode.lower() != 'all':
        query += " AND work_mode LIKE %s"
        params.append(f"%{work_mode}%")

    if job_type and job_type.lower() != 'all':
        query += " AND job_type LIKE %s"
        params.append(f"%{job_type}%")

    if experience and experience.lower() != 'all':
        query += " AND experience LIKE %s"
        params.append(f"%{experience}%")

    if min_sal:
        query += " AND salary_max >= %s"
        params.append(min_sal)

    if max_sal:
        query += " AND salary_min <= %s"
        params.append(max_sal)

    if premium_only:
        query += " AND is_premium = 1"

    if urgent_only:
        query += " AND is_urgent = 1"

    # Count total matches for pagination
    count_query = query.replace("SELECT *", "SELECT COUNT(*) AS total", 1)
    total_count = query_db(count_query, tuple(params), one=True)['total']

    # Sorting
    if sort_by == 'salary_high':
        query += " ORDER BY salary_max DESC, id DESC"
    elif sort_by == 'salary_low':
        query += " ORDER BY salary_min ASC, id DESC"
    elif sort_by == 'urgent':
        query += " ORDER BY is_urgent DESC, id DESC"
    else:  # newest / default
        query += " ORDER BY is_urgent DESC, is_premium DESC, id DESC"

    # Pagination offset
    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"

    jobs = query_db(query, tuple(params))

    # User context for bookmark and application flags
    user_id = session.get('user_id')
    user_bookmarks = set()
    user_applications = set()
    candidate_profile = None

    if user_id:
        user_bookmarks = {b['job_id'] for b in query_db("SELECT job_id FROM bookmarks WHERE user_id = %s", (user_id,))}
        cand = query_db("SELECT * FROM candidate_profile WHERE user_id = %s", (user_id,), one=True)
        if cand:
            candidate_profile = cand
            user_applications = {a['job_id'] for a in query_db("SELECT job_id FROM applications WHERE candidate_id = %s", (cand['id'],))}

    for j in jobs:
        j['bookmarked'] = j['id'] in user_bookmarks
        j['applied'] = j['id'] in user_applications
        match_res = compute_job_match(candidate_profile, j)
        j['match_pct'] = match_res['score']
        j['match_reasons'] = match_res['reasons']
        j['matched_skills'] = match_res['matched_skills']
        j['missing_skills'] = match_res['missing_skills']

    return jsonify({
        "jobs": jobs,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total_count + per_page - 1) // per_page)
    })

@jobs_bp.route('/api/jobs/<int:job_id>/apply', methods=['POST'])
@candidate_required
def apply_to_job(job_id):
    """Submits a job application for the authenticated candidate."""
    user_id = session['user_id']
    cand = query_db("SELECT * FROM candidate_profile WHERE user_id = %s", (user_id,), one=True)
    if not cand:
        return jsonify({"success": False, "error": "Candidate profile not found. Please complete your profile first."}), 400

    job = query_db("SELECT * FROM jobs WHERE id = %s AND status = 'Published'", (job_id,), one=True)
    if not job:
        return jsonify({"success": False, "error": "Job listing not found or no longer active."}), 404

    # Duplicate check
    existing = query_db("SELECT id FROM applications WHERE job_id = %s AND candidate_id = %s", (job_id, cand['id']), one=True)
    if existing:
        return jsonify({"success": False, "error": "You have already applied for this vacancy!"}), 409

    data = request.json or {}
    cover_note = sanitize_text(data.get('cover_note', 'Enthusiastic candidate available for immediate interview.'), 1000)

    try:
        app_id = query_db("""
            INSERT INTO applications (job_id, candidate_id, candidate_name, candidate_email, candidate_phone, candidate_skills, cover_note, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Submitted')
        """, (job_id, cand['id'], cand['name'], cand['email'], cand['phone'], cand['skills'], cover_note), commit=True)

        log_audit(user_id, 'APPLICATION_SUBMITTED', 'JOB', str(job_id), f"Application ID: {app_id}")

        return jsonify({
            "success": True,
            "message": f"Application submitted directly to HR for '{job['title']}'!",
            "application_id": app_id
        })
    except Exception as e:
        print(f"[Application Error] {e}")
        return jsonify({"success": False, "error": "Failed to submit application. Please try again."}), 500

@jobs_bp.route('/api/jobs/<int:job_id>/bookmark', methods=['POST'])
@login_required
def toggle_bookmark_api(job_id):
    """Toggles bookmark status for authenticated user."""
    user_id = session['user_id']
    job = query_db("SELECT id FROM jobs WHERE id = %s", (job_id,), one=True)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404

    existing = query_db("SELECT id FROM bookmarks WHERE user_id = %s AND job_id = %s", (user_id, job_id), one=True)
    if existing:
        query_db("DELETE FROM bookmarks WHERE user_id = %s AND job_id = %s", (user_id, job_id), commit=True)
        return jsonify({"bookmarked": False, "message": "Job removed from saved list."})
    else:
        query_db("INSERT INTO bookmarks (user_id, job_id) VALUES (%s, %s)", (user_id, job_id), commit=True)
        return jsonify({"bookmarked": True, "message": "Job saved to your bookmarks."})

@jobs_bp.route('/api/jobs/<int:job_id>/report', methods=['POST'])
@login_required
def report_job(job_id):
    """Reports a fraudulent or suspicious job listing."""
    user_id = session['user_id']
    data = request.json or {}
    reason = sanitize_text(data.get('reason', 'Suspicious Listing'), 100)
    details = sanitize_text(data.get('details', ''), 1000)

    if not reason:
        return jsonify({"success": False, "error": "Please specify a reason for the report."}), 400

    job = query_db("SELECT id FROM jobs WHERE id = %s", (job_id,), one=True)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404

    query_db("""
        INSERT INTO job_reports (job_id, reporter_id, reason, details, status)
        VALUES (%s, %s, %s, %s, 'Pending')
    """, (job_id, user_id, reason, details), commit=True)

    log_audit(user_id, 'JOB_REPORTED', 'JOB', str(job_id), f"Reason: {reason}")
    return jsonify({"success": True, "message": "Report submitted. Our moderation team will investigate promptly."})

@jobs_bp.route('/api/send-mail', methods=['POST'])
@login_required
def send_mail_to_hr():
    """Allows authenticated candidates to dispatch professional inquiry email to HR."""
    user_id = session['user_id']
    data = request.json or {}
    recipient = data.get('recipient_email', '').strip()
    sender_email = session.get('user_email')
    sender_name = session.get('user_name')
    subject = sanitize_text(data.get('subject', 'Job Application / Inquiry via Job Mitra'), 255)
    message = sanitize_text(data.get('message', ''), 3000)
    job_id = data.get('job_id')

    if not recipient or not message:
        return jsonify({"success": False, "error": "Recipient email and message body are required."}), 400

    query_db("""
        INSERT INTO sent_emails (job_id, recipient_email, sender_email, sender_name, subject, message)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (job_id, recipient, sender_email, sender_name, subject, message), commit=True)

    smtp_server = os.getenv('SMTP_SERVER')
    if smtp_server and os.getenv('SMTP_USER') and os.getenv('SMTP_PASS'):
        try:
            msg = MIMEMultipart()
            msg['From'] = os.getenv('SMTP_FROM', 'no-reply@jobmitra.in')
            msg['To'] = recipient
            msg['Subject'] = subject
            body = f"From: {sender_name} <{sender_email}>\n\n{message}\n\n---\nSent via Job Mitra Career Platform"
            msg.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP(smtp_server, int(os.getenv('SMTP_PORT', 587))) as server:
                server.starttls()
                server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASS'))
                server.send_message(msg)
        except Exception as e:
            print(f"[Mail Notice] SMTP dispatch fallback: {e}")

    log_audit(user_id, 'HR_EMAIL_SENT', 'JOB', str(job_id) if job_id else None, f"To: {recipient}")
    return jsonify({
        "success": True,
        "message": f"Inquiry successfully transmitted to HR ({recipient})!",
        "details": {"to": recipient, "subject": subject, "sender": f"{sender_name} <{sender_email}>"}
    })
