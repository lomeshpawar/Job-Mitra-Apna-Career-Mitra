"""
Job Mitra - Recruiter Management Routes
Recruiter Dashboard, Vacancy Posting, Applicant Review, and Application Status Management.
"""
from flask import Blueprint, render_template, request, jsonify, session, abort, flash, redirect, url_for
from database import query_db
from security import recruiter_required, sanitize_text, log_audit, validate_email_format, validate_phone_format

recruiter_bp = Blueprint('recruiter', __name__)

@recruiter_bp.route('/dashboard')
@recruiter_required
def dashboard():
    """Renders Recruiter Dashboard with posting statistics and applicant counts."""
    user_id = session['user_id']
    is_admin = session.get('user_role') == 'admin'

    rec_profile = query_db("SELECT * FROM recruiter_profiles WHERE user_id = %s", (user_id,), one=True)
    if not rec_profile and not is_admin:
        # Create empty recruiter profile if missing
        rec_id = query_db("""
            INSERT INTO recruiter_profiles (user_id, company_name, designation, is_verified)
            VALUES (%s, 'My Company', 'Recruitment Specialist', 0)
        """, (user_id,), commit=True)
        rec_profile = query_db("SELECT * FROM recruiter_profiles WHERE id = %s", (rec_id,), one=True)

    # Recruiters only see their own jobs; admins see all
    if is_admin:
        jobs = query_db("SELECT * FROM jobs ORDER BY id DESC")
        total_apps = query_db("SELECT COUNT(*) AS c FROM applications", one=True)['c']
    else:
        jobs = query_db("SELECT * FROM jobs WHERE recruiter_id = %s ORDER BY id DESC", (user_id,))
        total_apps = query_db("""
            SELECT COUNT(*) AS c
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE j.recruiter_id = %s
        """, (user_id,), one=True)['c']

    # Metrics
    total_posted = len(jobs)
    published_count = sum(1 for j in jobs if j.get('status') == 'Published')
    pending_count = sum(1 for j in jobs if j.get('status') == 'Pending Review')
    closed_count = sum(1 for j in jobs if j.get('status') == 'Closed')

    return render_template(
        'recruiter/dashboard.html',
        recruiter=rec_profile,
        jobs=jobs,
        total_posted=total_posted,
        published_count=published_count,
        pending_count=pending_count,
        closed_count=closed_count,
        total_apps=total_apps
    )

@recruiter_bp.route('/post-job', methods=['GET', 'POST'])
@recruiter_required
def post_job():
    """Renders job posting form and handles new vacancy submissions."""
    user_id = session['user_id']
    is_admin = session.get('user_role') == 'admin'
    rec = query_db("SELECT * FROM recruiter_profiles WHERE user_id = %s", (user_id,), one=True)

    if request.method == 'GET':
        return render_template('recruiter/post_job.html', recruiter=rec)

    # POST handling
    title = sanitize_text(request.form.get('title', ''))
    company = sanitize_text(request.form.get('company', rec['company_name'] if rec else 'Company'))
    stream = sanitize_text(request.form.get('stream', 'Computer Science / IT'))
    qualification = sanitize_text(request.form.get('qualification', 'B.Tech / Graduate'))
    city = sanitize_text(request.form.get('city', 'Bengaluru'))
    sal_min = int(request.form.get('salary_min', 25000))
    sal_max = int(request.form.get('salary_max', 40000))
    job_type = sanitize_text(request.form.get('job_type', 'Full Time'))
    work_mode = sanitize_text(request.form.get('work_mode', 'Onsite'))
    experience = sanitize_text(request.form.get('experience', 'Freshers / 0-1 yr'))
    skills_required = sanitize_text(request.form.get('skills_required', ''))
    hr_email = request.form.get('hr_email', session.get('user_email', '')).strip().lower()
    hr_phone = sanitize_text(request.form.get('hr_phone', ''))
    address = sanitize_text(request.form.get('address', 'Tech Park, India'))
    description = sanitize_text(request.form.get('description', ''), 4000)
    is_urgent = 1 if request.form.get('is_urgent') else 0
    is_premium = 1 if request.form.get('is_premium') else 0

    errors = []
    if not title: errors.append("Job title is required.")
    if not skills_required: errors.append("Required skills are required.")
    if not description: errors.append("Job description is required.")
    if not validate_email_format(hr_email): errors.append("Valid HR contact email is required.")
    if hr_phone and not validate_phone_format(hr_phone): errors.append("Valid HR phone number is required.")
    if sal_min > sal_max: errors.append("Minimum salary cannot exceed maximum salary.")

    if errors:
        for err in errors: flash(err, "error")
        return render_template('recruiter/post_job.html', recruiter=rec, form_data=request.form), 400

    # Normal recruiter jobs default to 'Pending Review' and is_verified=0
    # Admins can publish directly
    status = 'Published' if is_admin else 'Pending Review'
    is_verified = 1 if is_admin else 0
    is_demo = 0

    job_id = query_db("""
        INSERT INTO jobs (
            title, company, stream, qualification, city, salary_min, salary_max,
            job_type, work_mode, experience, skills_required, is_premium, is_urgent,
            is_verified, is_demo, status, hr_email, hr_phone, address, description, recruiter_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        title, company, stream, qualification, city, sal_min, sal_max,
        job_type, work_mode, experience, skills_required, is_premium, is_urgent,
        is_verified, is_demo, status, hr_email, hr_phone, address, description, user_id
    ), commit=True)

    log_audit(user_id, 'JOB_CREATED', 'JOB', str(job_id), f"Title: {title}, Status: {status}")

    msg = "Job vacancy published successfully!" if status == 'Published' else "Job submitted for review. An administrator will verify and approve it shortly."
    flash(msg, "success")
    return redirect(url_for('recruiter.dashboard'))

@recruiter_bp.route('/jobs/<int:job_id>/applicants')
@recruiter_required
def view_applicants(job_id):
    """Lists applicants for a specific job. Strictly verifies ownership."""
    user_id = session['user_id']
    is_admin = session.get('user_role') == 'admin'

    job = query_db("SELECT * FROM jobs WHERE id = %s", (job_id,), one=True)
    if not job:
        abort(404, "Job not found")

    # Recruiter ownership check
    if not is_admin and job.get('recruiter_id') != user_id:
        abort(403, "You do not have permission to view applicants for this job vacancy.")

    applicants = query_db("""
        SELECT a.*, c.education, c.stream AS candidate_stream, c.city AS candidate_city
        FROM applications a
        LEFT JOIN candidate_profile c ON a.candidate_id = c.id
        WHERE a.job_id = %s
        ORDER BY a.applied_at DESC
    """, (job_id,))

    return render_template('recruiter/applicants.html', job=job, applicants=applicants)

@recruiter_bp.route('/api/applications/<int:app_id>/status', methods=['POST'])
@recruiter_required
def update_application_status(app_id):
    """
    Updates applicant status (Submitted, Under Review, Shortlisted, Interviewing, Rejected, Hired).
    Validates recruiter ownership of the associated job posting.
    """
    user_id = session['user_id']
    is_admin = session.get('user_role') == 'admin'

    app_record = query_db("""
        SELECT a.*, j.recruiter_id, j.title
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.id = %s
    """, (app_id,), one=True)

    if not app_record:
        return jsonify({"success": False, "error": "Application not found"}), 404

    # Strict ownership check
    if not is_admin and app_record['recruiter_id'] != user_id:
        return jsonify({"success": False, "error": "Forbidden: You are not authorized to manage this application."}), 403

    data = request.json or {}
    new_status = data.get('status', '').strip()
    valid_statuses = ('Submitted', 'Under Review', 'Shortlisted', 'Interviewing', 'Rejected', 'Hired')

    if new_status not in valid_statuses:
        return jsonify({"success": False, "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    query_db("UPDATE applications SET status = %s WHERE id = %s", (new_status, app_id), commit=True)
    log_audit(user_id, 'APPLICATION_STATUS_UPDATED', 'APPLICATION', str(app_id), f"New status: {new_status}")

    return jsonify({"success": True, "message": f"Application status updated to '{new_status}'."})
