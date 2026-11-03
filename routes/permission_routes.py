"""
TrustVault Permission Management Routes
Allows document owners to grant named access and revoke it with immediate effect.
"""

from flask import Blueprint, request, redirect, url_for, flash, jsonify
from models import User
from services.auth_service import login_required, get_current_user
from services.permission_service import grant_permission, revoke_permission

permission_bp = Blueprint('permissions', __name__)

@permission_bp.route('/documents/<int:doc_id>/permissions/grant', methods=['POST'])
@login_required
def grant(doc_id):
    user = get_current_user()
    target_username = request.form.get('username') or (request.json.get('username') if request.is_json else None)
    permission_level = request.form.get('permission') or (request.json.get('permission') if request.is_json else 'read')
    
    if not target_username:
        if request.is_json:
            return jsonify({'error': 'Target username is required'}), 400
        flash("Username is required to grant permissions.", "danger")
        return redirect(url_for('documents.detail', doc_id=doc_id))
        
    success, message = grant_permission(user, doc_id, target_username, permission_level)
    
    if request.is_json:
        status_code = 200 if success else 400
        return jsonify({'success': success, 'message': message}), status_code
        
    flash(message, "success" if success else "danger")
    return redirect(url_for('documents.detail', doc_id=doc_id))


@permission_bp.route('/documents/<int:doc_id>/permissions/revoke/<int:user_id>', methods=['POST'])
@login_required
def revoke(doc_id, user_id):
    user = get_current_user()
    success, message = revoke_permission(user, doc_id, user_id)
    
    if request.is_json:
        status_code = 200 if success else 400
        return jsonify({'success': success, 'message': message}), status_code
        
    flash(message, "success" if success else "danger")
    return redirect(url_for('documents.detail', doc_id=doc_id))


@permission_bp.route('/api/users/search', methods=['GET'])
@login_required
def search_users():
    """Helper endpoint to find valid users to grant permissions to."""
    query = request.args.get('q', '').strip()
    current_user = get_current_user()
    
    users = User.query.filter(
        User.id != current_user.id,
        User.is_active == True,
        User.username.ilike(f"%{query}%")
    ).limit(10).all()
    
    return jsonify([{'id': u.id, 'username': u.username, 'role': u.role} for u in users])
