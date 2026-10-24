"""
Job Mitra - Authentication Routes
Registration, Login, Logout, Session Management, and Role Authorization.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import query_db, execute_transaction
from security import (
    hash_password, verify_password, is_rate_limited, record_failed_attempt,
    clear_failed_attempts, generate_csrf_token, log_audit, validate_email_format,
    validate_phone_format, sanitize_text
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            role = session.get('user_role')
            if role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif role == 'recruiter':
                return redirect(url_for('recruiter.dashboard'))
            return redirect(url_for('candidate.dashboard'))
        return render_template('auth/login.html')

    # POST handling
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    next_url = request.form.get('next') or request.args.get('next')

    # Check brute-force lockout
    ip = request.remote_addr or '127.0.0.1'
    if is_rate_limited(ip) or is_rate_limited(email):
        err_msg = "Too many failed login attempts. Please wait 15 minutes before trying again."
        if request.is_json:
            return jsonify({"success": False, "error": err_msg}), 429
        flash(err_msg, "error")
        return render_template('auth/login.html', email=email), 429

    if not email or not password:
        err_msg = "Please provide both email and password."
        if request.is_json:
            return jsonify({"success": False, "error": err_msg}), 400
        flash(err_msg, "error")
        return render_template('auth/login.html', email=email), 400

    user = query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)
    if not user or not verify_password(user['password_hash'], password):
        record_failed_attempt(ip)
        record_failed_attempt(email)
        log_audit(None, 'LOGIN_FAILED', 'USER', email, f"Failed login attempt from IP {ip}")
        err_msg = "Invalid email or password. Please verify credentials."
        if request.is_json:
            return jsonify({"success": False, "error": err_msg}), 401
        flash(err_msg, "error")
        return render_template('auth/login.html', email=email), 401

    if not user.get('is_active', 1):
        err_msg = "This account has been deactivated. Please contact support."
        if request.is_json:
            return jsonify({"success": False, "error": err_msg}), 403
        flash(err_msg, "error")
        return render_template('auth/login.html', email=email), 403

    # Successful login
    clear_failed_attempts(ip)
    clear_failed_attempts(email)

    session.clear()
    session['user_id'] = user['id']
    session['user_email'] = user['email']
    session['user_name'] = user['name']
    session['user_role'] = user['role']
    generate_csrf_token()

    log_audit(user['id'], 'LOGIN_SUCCESS', 'USER', str(user['id']), f"Role: {user['role']}")

    # Determine redirect destination
    dest = next_url
    if not dest or dest.startswith('/auth'):
        if user['role'] == 'admin':
            dest = url_for('admin.dashboard')
        elif user['role'] == 'recruiter':
            dest = url_for('recruiter.dashboard')
        else:
            dest = url_for('candidate.dashboard')

    if request.is_json:
        return jsonify({
            "success": True,
            "message": "Signed in successfully!",
            "redirect": dest,
            "user": {"id": user['id'], "name": user['name'], "email": user['email'], "role": user['role']}
        })

    return redirect(dest)

@auth_bp.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('jobs.index'))
        return render_template('auth/register.html')

    name = sanitize_text(request.form.get('name', ''))
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm_pw = request.form.get('confirm_password', '')
    role = request.form.get('role', 'candidate').strip().lower()
    phone = sanitize_text(request.form.get('phone', ''))

    # Candidate specific
    stream = sanitize_text(request.form.get('stream', 'Computer Science / IT'))
    education = sanitize_text(request.form.get('education', 'B.Tech / Graduate'))

    # Recruiter specific
    company_name = sanitize_text(request.form.get('company_name', ''))
    designation = sanitize_text(request.form.get('designation', 'HR Manager'))

    # Security rule: Users cannot register as 'admin'
    if role not in ('candidate', 'recruiter'):
        role = 'candidate'

    errors = []
    if not name or len(name) < 2:
        errors.append("Please provide a valid full name.")
    if not validate_email_format(email):
        errors.append("Please provide a valid email address.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if password != confirm_pw:
        errors.append("Passwords do not match.")
    if phone and not validate_phone_format(phone):
        errors.append("Please provide a valid phone number (at least 10 digits).")
    if role == 'recruiter' and not company_name:
        errors.append("Company name is required for recruiter registration.")

    if errors:
        if request.is_json:
            return jsonify({"success": False, "errors": errors}), 400
        for err in errors:
            flash(err, "error")
        return render_template('auth/register.html', form_data=request.form), 400

    # Check email uniqueness
    existing = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
    if existing:
        err = "An account with this email address already exists. Please log in."
        if request.is_json:
            return jsonify({"success": False, "errors": [err]}), 400
        flash(err, "error")
        return render_template('auth/register.html', form_data=request.form), 400

    hashed_pw = hash_password(password)

    try:
        # Atomic registration
        user_id = query_db("""
            INSERT INTO users (email, password_hash, role, name)
            VALUES (%s, %s, %s, %s)
        """, (email, hashed_pw, role, name), commit=True)

        if role == 'candidate':
            query_db("""
                INSERT INTO candidate_profile (user_id, name, email, phone, stream, education, skills, is_premium)
                VALUES (%s, %s, %s, %s, %s, %s, '', 0)
            """, (user_id, name, email, phone or '+91 9800000000', stream, education), commit=True)
        elif role == 'recruiter':
            query_db("""
                INSERT INTO recruiter_profiles (user_id, company_name, designation, phone, is_verified)
                VALUES (%s, %s, %s, %s, 0)
            """, (user_id, company_name, designation, phone or '+91 9800000000'), commit=True)

        log_audit(user_id, 'USER_REGISTERED', 'USER', str(user_id), f"Role: {role}, Email: {email}")

        # Auto login upon registration
        session.clear()
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = name
        session['user_role'] = role
        generate_csrf_token()

        dest = url_for('recruiter.dashboard') if role == 'recruiter' else url_for('candidate.dashboard')

        if request.is_json:
            return jsonify({
                "success": True,
                "message": "Account created successfully!",
                "redirect": dest
            })

        flash(f"Welcome to Job Mitra, {name}! Your account has been created.", "success")
        return redirect(dest)

    except Exception as e:
        print(f"[Register Error] {e}")
        err = "An unexpected error occurred during account creation. Please try again."
        if request.is_json:
            return jsonify({"success": False, "errors": [err]}), 500
        flash(err, "error")
        return render_template('auth/register.html', form_data=request.form), 500

@auth_bp.route('/auth/logout', methods=['GET', 'POST'])
def logout():
    uid = session.get('user_id')
    if uid:
        log_audit(uid, 'LOGOUT', 'USER', str(uid), "User logged out.")
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for('jobs.index'))

@auth_bp.route('/auth/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')
    
    email = request.form.get('email', '').strip().lower()
    if not validate_email_format(email):
        flash("Please enter a valid registered email address.", "error")
        return render_template('auth/forgot_password.html')

    user = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
    # Generic message to avoid email enumeration
    flash("If that email is registered with Job Mitra, password recovery instructions have been sent.", "info")
    return render_template('auth/forgot_password.html', submitted=True)

@auth_bp.route('/api/me', methods=['GET'])
def get_current_user():
    """Returns currently authenticated user session state."""
    if 'user_id' not in session:
        return jsonify({"authenticated": False})
    
    user_id = session['user_id']
    user = query_db("SELECT id, email, name, role, is_active FROM users WHERE id = %s", (user_id,), one=True)
    if not user:
        session.clear()
        return jsonify({"authenticated": False})

    profile_data = {}
    if user['role'] == 'candidate':
        cand = query_db("SELECT * FROM candidate_profile WHERE user_id = %s", (user_id,), one=True)
        if cand:
            profile_data = cand
    elif user['role'] == 'recruiter':
        rec = query_db("SELECT * FROM recruiter_profiles WHERE user_id = %s", (user_id,), one=True)
        if rec:
            profile_data = rec

    return jsonify({
        "authenticated": True,
        "user": user,
        "profile": profile_data
    })
