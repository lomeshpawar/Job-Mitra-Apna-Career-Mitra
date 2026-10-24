"""
Job Mitra - Route Modules
"""
from flask import Blueprint

def register_blueprints(app):
    from routes.auth import auth_bp
    from routes.jobs import jobs_bp
    from routes.candidate import candidate_bp
    from routes.recruiter import recruiter_bp
    from routes.admin import admin_bp
    from routes.payments import payments_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(candidate_bp, url_prefix='/candidate')
    app.register_blueprint(recruiter_bp, url_prefix='/recruiter')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(payments_bp)
