"""
TrustVault Administrative Oversight Routes
Provides system administrators with real-time audit ledger inspection,
security anomaly alerts, and cryptographic hash chain verification.
"""

from flask import Blueprint, render_template, request, jsonify
from models import AuditLog, User, Document
from services.auth_service import login_required, role_required, get_current_user
from services.audit_service import verify_chain_integrity

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
@role_required('admin')
def dashboard():
    user = get_current_user()
    
    # Filter parameters
    status_filter = request.args.get('status', '').strip()
    action_filter = request.args.get('action', '').strip()
    username_filter = request.args.get('username', '').strip()
    
    # Base query
    query = AuditLog.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if action_filter:
        query = query.filter_by(action=action_filter)
    if username_filter:
        query = query.filter(AuditLog.username.ilike(f"%{username_filter}%"))
        
    logs = query.order_by(AuditLog.id.desc()).limit(100).all()
    
    # Verify cryptographic ledger integrity
    is_ledger_intact, compromised_records = verify_chain_integrity()
    
    # Calculate security metrics
    total_logs = AuditLog.query.count()
    denied_attempts_count = AuditLog.query.filter_by(status='DENIED').count()
    total_users = User.query.count()
    total_documents = Document.query.count()
    
    # Recent security alerts (refused attempts / probes)
    recent_security_alerts = AuditLog.query.filter_by(status='DENIED').order_by(AuditLog.id.desc()).limit(10).all()
    
    return render_template(
        'admin.html',
        user=user,
        logs=logs,
        is_ledger_intact=is_ledger_intact,
        compromised_records=compromised_records,
        total_logs=total_logs,
        denied_attempts_count=denied_attempts_count,
        total_users=total_users,
        total_documents=total_documents,
        recent_security_alerts=recent_security_alerts,
        status_filter=status_filter,
        action_filter=action_filter,
        username_filter=username_filter
    )


@admin_bp.route('/admin/verify-integrity', methods=['GET'])
@login_required
@role_required('admin')
def verify_integrity_api():
    """API endpoint to run on-demand cryptographic verification of the audit trail."""
    is_valid, compromised = verify_chain_integrity()
    return jsonify({
        'is_valid': is_valid,
        'compromised_count': len(compromised),
        'compromised_records': compromised,
        'status': 'SECURE' if is_valid else 'COMPROMISED'
    })
