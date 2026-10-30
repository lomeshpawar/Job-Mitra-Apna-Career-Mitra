"""
Job Mitra - Apna Career Mitra
Modern, Secure, High-Performance Job Portal for Freshers and IT Job Seekers.
Stack: Python Flask, SQLite/MySQL, HTML5, CSS3, JavaScript.
"""
import os
from flask import Flask, render_template, jsonify, session, request
from config import Config, is_configured_upi_id, is_usable_secret_key
from routes import register_blueprints
from security import generate_csrf_token, validate_csrf
from database import query_db

def create_app(config_class=Config):
    """Application factory for Job Mitra."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get('TESTING') and not is_usable_secret_key(app.config.get('SECRET_KEY')):
        raise RuntimeError(
            "SECRET_KEY must be configured with a non-placeholder value of at least 32 characters; "
            "example placeholders are not accepted."
        )

    # Register blueprints
    register_blueprints(app)

    # Security: CSRF validation before state-changing requests
    @app.before_request
    def before_request_hook():
        validate_csrf()

    # Template context processor: inject global variables & helpers
    @app.context_processor
    def inject_context():
        user_role = session.get('user_role')
        user_name = session.get('user_name')
        user_email = session.get('user_email')
        is_logged_in = 'user_id' in session
        
        # Check premium status if candidate
        is_premium = False
        if is_logged_in and user_role == 'candidate':
            cand = query_db("SELECT is_premium FROM candidate_profile WHERE user_id = %s", (session['user_id'],), one=True)
            if cand:
                is_premium = bool(cand['is_premium'])

        upi_id = app.config.get('UPI_ID', '')

        return {
            'csrf_token': generate_csrf_token,
            'current_user': {
                'id': session.get('user_id'),
                'name': user_name,
                'email': user_email,
                'role': user_role,
                'is_premium': is_premium
            },
            'is_logged_in': is_logged_in,
            'app_upi_id': upi_id if is_configured_upi_id(upi_id) else '',
            'gateway_live': app.config.get('PAYMENT_GATEWAY_LIVE', False)
        }

    # Centralized error handlers
    @app.errorhandler(400)
    def bad_request(e):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({"error": str(e.description if hasattr(e, 'description') else "Bad request"), "code": "BAD_REQUEST"}), 400
        return render_template('errors/400.html', error=e), 400

    @app.errorhandler(403)
    def forbidden(e):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({"error": "Forbidden: You do not have permission to access this resource.", "code": "FORBIDDEN"}), 403
        return render_template('errors/403.html', error=e), 403

    @app.errorhandler(404)
    def not_found(e):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({"error": "Resource not found", "code": "NOT_FOUND"}), 404
        return render_template('errors/404.html', error=e), 404

    @app.errorhandler(500)
    def internal_error(e):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({"error": "An internal server error occurred.", "code": "SERVER_ERROR"}), 500
        return render_template('errors/500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1')
    print("=" * 60)
    print(f"[*] Job Mitra Portal running on http://127.0.0.1:{port}")
    print(f"[*] Mode: {'Development (Debug ON)' if debug_mode else 'Production (Debug OFF)'}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
