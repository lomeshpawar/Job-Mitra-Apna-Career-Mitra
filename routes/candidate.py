"""
Job Mitra - Candidate Management Routes
Personalized Candidate Dashboard, Profile Management, Skills, Saved Jobs, and Application Tracker.
"""
from flask import Blueprint, render_template, request, jsonify, session, abort
from database import query_db
from security import candidate_required, sanitize_text, log_audit, validate_phone_format
from matching import compute_job_match

candidate_bp = Blueprint('candidate', __name__)

def calculate_profile_completion(cand: dict) -> int:
    """Calculates true profile completion percentage based on non-empty fields."""
    if not cand:
        return 0
    fields = [
        cand.get('name'), cand.get('email'), cand.get('phone'),
        cand.get('city'), cand.get('stream'), cand.get('education'),
        cand.get('skills'), cand.get('bio'), cand.get('graduation_year')
    ]
    completed = sum(1 for f in fields if f and str(f).strip())
    return int((completed / len(fields)) * 100)

@candidate_bp.route('/dashboard')
@candidate_required
def dashboard():
    """Renders Candidate Dashboard."""
    user_id = session['user_id']
    cand = query_db("SELECT * FROM candidate_profile WHERE user_id = %s", (user_id,), one=True)
    if not cand:
        # Auto-create empty profile if somehow missing
        cand_id = query_db("""
            INSERT INTO candidate_profile (user_id, name, email, phone, stream, education, skills, is_premium)
            VALUES (%s, %s, %s, '+91 9800000000', 'Computer Science / IT', 'B.Tech / Graduate', '', 0)
        """, (user_id, session['user_name'], session['user_email']), commit=True)
        cand = query_db("SELECT * FROM candidate_profile WHERE id = %s", (cand_id,), one=True)

    profile_pct = calculate_profile_completion(cand)

    # Candidate metrics
    app_count = query_db("SELECT COUNT(*) AS c FROM applications WHERE candidate_id = %s", (cand['id'],), one=True)['c']
    saved_count = query_db("SELECT COUNT(*) AS c FROM bookmarks WHERE user_id = %s", (user_id,), one=True)['c']
    
    # Recent applications
    applications = query_db("""
        SELECT a.*, j.title, j.company, j.city, j.salary_min, j.salary_max, j.is_urgent
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.candidate_id = %s
        ORDER BY a.applied_at DESC
        LIMIT 10
    """, (cand['id'],))

    # Saved jobs
    saved_jobs = query_db("""
        SELECT j.*, b.created_at AS bookmarked_at
        FROM bookmarks b
        JOIN jobs j ON b.job_id = j.id
        WHERE b.user_id = %s
        ORDER BY b.created_at DESC
    """, (user_id,))

    # Recommended jobs
    all_published = query_db("SELECT * FROM jobs WHERE status = 'Published' LIMIT 30")
    recommended = []
    for j in all_published:
        match_info = compute_job_match(cand, j)
        j['match_pct'] = match_info['score']
        j['match_reasons'] = match_info['reasons']
        recommended.append(j)

    recommended.sort(key=lambda x: x['match_pct'], reverse=True)
    top_recommended = recommended[:6]

    return render_template(
        'candidate/dashboard.html',
        candidate=cand,
        profile_pct=profile_pct,
        app_count=app_count,
        saved_count=saved_count,
        applications=applications,
        saved_jobs=saved_jobs,
        recommended_jobs=top_recommended
    )

@candidate_bp.route('/api/profile', methods=['GET', 'POST'])
@candidate_required
def candidate_profile_api():
    """Fetches or securely updates the authenticated candidate's profile."""
    user_id = session['user_id']
    cand = query_db("SELECT * FROM candidate_profile WHERE user_id = %s", (user_id,), one=True)

    if request.method == 'GET':
        return jsonify(cand or {})

    # POST: Update profile safely
    # SECURITY: Strip is_premium, role, user_id from client input!
    data = request.json or {}
    name = sanitize_text(data.get('name', cand['name'] if cand else session['user_name']), 150)
    phone = sanitize_text(data.get('phone', cand['phone'] if cand else ''), 50)
    city = sanitize_text(data.get('city', cand['city'] if cand else 'Bengaluru'), 100)
    stream = sanitize_text(data.get('stream', cand['stream'] if cand else 'Computer Science / IT'), 100)
    education = sanitize_text(data.get('education', cand['education'] if cand else 'B.Tech / Graduate'), 255)
    graduation_year = sanitize_text(data.get('graduation_year', cand['graduation_year'] if cand else '2026'), 20)
    bio = sanitize_text(data.get('bio', cand['bio'] if cand else ''), 1000)
    skills = sanitize_text(data.get('skills', cand['skills'] if cand else ''), 1000)

    if phone and not validate_phone_format(phone):
        return jsonify({"success": False, "error": "Please provide a valid contact number (min 10 digits)."}), 400

    query_db("""
        UPDATE candidate_profile
        SET name = %s, phone = %s, city = %s, stream = %s, education = %s,
            graduation_year = %s, bio = %s, skills = %s, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = %s
    """, (name, phone, city, stream, education, graduation_year, bio, skills, user_id), commit=True)

    # Also update user's name
    query_db("UPDATE users SET name = %s WHERE id = %s", (name, user_id), commit=True)
    session['user_name'] = name

    log_audit(user_id, 'PROFILE_UPDATED', 'CANDIDATE_PROFILE', str(cand['id'] if cand else user_id), "Candidate profile updated.")

    return jsonify({"success": True, "message": "Profile updated successfully!"})

@candidate_bp.route('/api/skills', methods=['POST'])
@candidate_required
def manage_skills():
    """Adds or removes a technical skill from the candidate's profile."""
    user_id = session['user_id']
    cand = query_db("SELECT id, skills FROM candidate_profile WHERE user_id = %s", (user_id,), one=True)
    if not cand:
        return jsonify({"success": False, "error": "Candidate profile not found."}), 400

    data = request.json or {}
    skill = sanitize_text(data.get('skill', ''), 100)
    action = data.get('action', 'add').lower()

    if not skill:
        return jsonify({"success": False, "error": "Skill name cannot be empty."}), 400

    cur_skills = [s.strip() for s in (cand['skills'] or '').split(',') if s.strip()]

    if action == 'add':
        if not any(s.lower() == skill.lower() for s in cur_skills):
            cur_skills.append(skill)
    elif action == 'remove':
        cur_skills = [s for s in cur_skills if s.lower() != skill.lower()]

    updated_str = ", ".join(cur_skills)
    query_db("UPDATE candidate_profile SET skills = %s WHERE id = %s", (updated_str, cand['id']), commit=True)

    return jsonify({"success": True, "skills": updated_str, "count": len(cur_skills)})

@candidate_bp.route('/api/applications', methods=['GET'])
@candidate_required
def get_my_applications():
    """Returns candidate's submitted applications with live status."""
    user_id = session['user_id']
    cand = query_db("SELECT id FROM candidate_profile WHERE user_id = %s", (user_id,), one=True)
    if not cand:
        return jsonify([])

    apps = query_db("""
        SELECT a.*, j.title, j.company, j.city, j.salary_min, j.salary_max, j.is_urgent, j.hr_email, j.hr_phone
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.candidate_id = %s
        ORDER BY a.applied_at DESC
    """, (cand['id'],))
    return jsonify(apps)

@candidate_bp.route('/api/bookmarks', methods=['GET'])
@candidate_required
def get_my_bookmarks():
    """Returns candidate's saved job vacancies."""
    user_id = session['user_id']
    bookmarks = query_db("""
        SELECT j.*, b.created_at AS bookmarked_at
        FROM bookmarks b
        JOIN jobs j ON b.job_id = j.id
        WHERE b.user_id = %s
        ORDER BY b.created_at DESC
    """, (user_id,))
    return jsonify(bookmarks)
