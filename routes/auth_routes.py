"""
TrustVault Authentication Routes
Handles user sign-in, session termination, and identity inspection.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from services.auth_service import authenticate_user, logout_current_user, get_current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Auto-healing: Ensure seed accounts exist even on fresh or ephemeral cloud instances
    from models import User
    from seed_data import seed_database
    from flask import current_app
    if User.query.first() is None:
        try:
            seed_database(current_app, drop_existing=False)
        except Exception as e:
            print(f"[LOGIN AUTO-SEED] Error: {e}")

    if request.method == 'POST':
        identifier = request.form.get('identifier', '')
        password = request.form.get('password', '')
        
        user, message = authenticate_user(identifier, password)
        if user:
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('documents.dashboard'))
        else:
            flash(message, 'danger')
            
    current_user = get_current_user()
    if current_user:
        return redirect(url_for('documents.dashboard'))
        
    return render_template('login.html')


@auth_bp.route('/seed-db', methods=['GET', 'POST'])
def seed_db_route():
    """
    On-demand database seeder for cloud deployments.
    Visiting https://<deployed-url>/seed-db immediately provisions or resets seed accounts.
    """
    from seed_data import seed_database
    from flask import current_app
    force = request.args.get('force') == 'true'
    try:
        seed_database(current_app, drop_existing=force)
        flash("Database successfully seeded with default evaluator credentials! You can now log in.", "success")
    except Exception as e:
        flash(f"Seeding error: {str(e)}", "danger")
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_current_user()
    flash("You have been securely signed out.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/me', methods=['GET'])
def current_user_api():
    user = get_current_user()
    if not user:
        return jsonify({'authenticated': False}), 401
    return jsonify({
        'authenticated': True,
        'user': user.to_dict()
    })

