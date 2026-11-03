"""
TrustVault Document Management Routes
Handles document listing, uploading, detail inspection, metadata editing,
deletion, and authorized file streaming.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from models import db, Document, DocumentPermission, AuditLog
from services.auth_service import login_required, get_current_user
from services.permission_service import check_document_access, get_accessible_documents_query
from services.document_service import store_and_register_document, stream_document_content, delete_document_record
from services.audit_service import log_event

document_bp = Blueprint('documents', __name__)

@document_bp.route('/')
@document_bp.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    category_filter = request.args.get('category', '').strip()
    
    # Filter documents strictly by accessibility (Zero Metadata Leakage)
    base_query = get_accessible_documents_query(user)
    
    if category_filter:
        base_query = base_query.filter_by(category=category_filter)
        
    docs = base_query.order_by(Document.created_at.desc()).all()
    
    # Extract distinct categories from accessible documents
    categories = sorted(list(set(d.category for d in docs if d.category)))
    if not categories:
        categories = ['Contracts', 'Financials', 'Legal', 'HR', 'Engineering', 'General']
        
    # Split into owned vs shared for clearer UI
    owned_docs = [d for d in docs if d.owner_id == user.id]
    shared_docs = [d for d in docs if d.owner_id != user.id]
    
    return render_template(
        'dashboard.html',
        user=user,
        owned_docs=owned_docs,
        shared_docs=shared_docs,
        all_docs=docs,
        categories=categories,
        current_category=category_filter
    )


@document_bp.route('/documents/upload', methods=['POST'])
@login_required
def upload():
    user = get_current_user()
    
    # Enforce role permission: Viewers cannot upload documents
    if user.role == 'viewer':
        log_event(
            action='UPLOAD',
            status='DENIED',
            user=user,
            reason="Role violation: Viewers are not authorized to upload new documents"
        )
        flash("Viewers are not permitted to upload documents. Request an Owner account.", "danger")
        return redirect(url_for('documents.dashboard'))
        
    if 'document_file' not in request.files:
        flash("No file part provided in upload form", "danger")
        return redirect(url_for('documents.dashboard'))
        
    file = request.files['document_file']
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', 'General').strip()
    
    success, message, doc = store_and_register_document(
        uploader=user,
        file_storage=file,
        title=title,
        description=description,
        category=category
    )
    
    if success:
        flash(f"Document '{doc.title}' uploaded and encrypted successfully.", "success")
        return redirect(url_for('documents.detail', doc_id=doc.id))
    else:
        flash(f"Upload rejected: {message}", "danger")
        return redirect(url_for('documents.dashboard'))


@document_bp.route('/documents/<int:doc_id>', methods=['GET'])
@login_required
def detail(doc_id):
    user = get_current_user()
    can_read, reason, doc = check_document_access(user, doc_id, required_permission='read')
    
    if not can_read:
        # Non-Negotiable #2: Refused attempt logged
        log_event(
            action='VIEW_METADATA',
            status='DENIED',
            user=user,
            document=doc,
            doc_id=doc_id,
            reason=f"Unauthorized detail access probe: {reason}"
        )
        abort(403, description=f"Access Denied: {reason}")
        
    # Check if user can manage (owner or admin)
    can_manage, _, _ = check_document_access(user, doc_id, required_permission='manage')
    can_edit, _, _ = check_document_access(user, doc_id, required_permission='edit')
    
    # Fetch active grants if owner/admin
    permissions = []
    audit_history = []
    if can_manage:
        permissions = DocumentPermission.query.filter_by(document_id=doc.id).all()
        audit_history = AuditLog.query.filter_by(document_id=doc.id).order_by(AuditLog.id.desc()).limit(30).all()
        
    return render_template(
        'document_detail.html',
        user=user,
        doc=doc,
        can_manage=can_manage,
        can_edit=can_edit,
        permissions=permissions,
        audit_history=audit_history
    )


@document_bp.route('/documents/<int:doc_id>/download', methods=['GET'])
@login_required
def download(doc_id):
    """
    CRITICAL AUTHORIZATION ENDPOINT:
    Validates permissions on the server before transmitting any file bytes.
    Logs both ALLOWED and DENIED attempts.
    """
    user = get_current_user()
    return stream_document_content(user, doc_id)


@document_bp.route('/documents/<int:doc_id>/edit', methods=['POST'])
@login_required
def edit(doc_id):
    user = get_current_user()
    can_edit, reason, doc = check_document_access(user, doc_id, required_permission='edit')
    
    if not can_edit:
        log_event(
            action='EDIT',
            status='DENIED',
            user=user,
            document=doc,
            doc_id=doc_id,
            reason=f"Unauthorized edit attempt: {reason}"
        )
        abort(403, description=f"Access Denied: {reason}")
        
    new_title = request.form.get('title', '').strip()
    new_description = request.form.get('description', '').strip()
    new_category = request.form.get('category', '').strip()
    
    if new_title:
        doc.title = new_title
    if new_description is not None:
        doc.description = new_description
    if new_category:
        doc.category = new_category
        
    db.session.commit()
    
    log_event(
        action='EDIT',
        status='ALLOWED',
        user=user,
        document=doc,
        reason=f"Updated metadata: title='{doc.title}', category='{doc.category}'"
    )
    flash("Document metadata updated successfully.", "success")
    return redirect(url_for('documents.detail', doc_id=doc.id))


@document_bp.route('/documents/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete(doc_id):
    user = get_current_user()
    success, message = delete_document_record(user, doc_id)
    
    if not success:
        # Strict HTTP 403 for unauthorized deletion attempts
        abort(403, description=message)
        
    flash(message, "success")
    return redirect(url_for('documents.dashboard'))
