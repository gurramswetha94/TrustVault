"""
TrustVault Permission Decision Engine
The single source of truth for authorization.
Enforces real-time access checks, instant revocation, and permission delegation.
"""

from models import db, Document, DocumentPermission, User
from services.audit_service import log_event

def check_document_access(user, doc_id, required_permission='read'):
    """
    Evaluates whether a given user is authorized to perform required_permission on doc_id.
    required_permission: 'read' (view/download) or 'edit' (update metadata/upload new version) or 'manage' (grant/revoke/delete)
    
    Returns (has_access: bool, reason: str, document: Document or None)
    """
    if not user or not hasattr(user, 'id'):
        return False, "Unauthenticated caller", None
        
    doc = db.session.get(Document, doc_id)
    if not doc:
        return False, "Document does not exist", None
        
    # Owner always has full access (read, edit, manage)
    if doc.owner_id == user.id:
        return True, "Caller is Document Owner", doc
        
    # Management operations (grant, revoke, delete) are strictly reserved for the owner
    if required_permission == 'manage':
        # Admin can manage if system emergency, but standard management belongs to owner
        if user.is_admin():
            return True, "Caller is System Administrator", doc
        return False, "Only Document Owner can manage permissions or delete this document", doc
        
    # Check explicit named grant in database (LIVE QUERY - No caching ensures instant revocation)
    perm_entry = DocumentPermission.query.filter_by(
        document_id=doc.id,
        user_id=user.id
    ).first()
    
    if not perm_entry:
        return False, f"User '{user.username}' has not been granted access to this document", doc
        
    # Check permission level hierarchy
    # 'edit' grants both edit and read
    # 'read' grants read only
    if required_permission == 'read':
        if perm_entry.permission in ('read', 'edit'):
            return True, f"User has explicit '{perm_entry.permission}' grant", doc
    elif required_permission == 'edit':
        if perm_entry.permission == 'edit':
            return True, "User has explicit 'edit' grant", doc
        else:
            return False, "User only has 'read' grant; 'edit' is required", doc
            
    return False, "Permission level unrecognized or denied", doc


def grant_permission(granter, doc_id, target_username, permission_level):
    """
    Grants read or edit permission on doc_id to target_username.
    Only the document owner (or admin) can grant permissions.
    """
    can_manage, reason, doc = check_document_access(granter, doc_id, required_permission='manage')
    if not can_manage:
        log_event(
            action='GRANT_PERMISSION',
            status='DENIED',
            user=granter,
            document=doc,
            doc_id=doc_id,
            reason=f"Unauthorized grant attempt: {reason}"
        )
        return False, f"Permission denied: {reason}"
        
    if permission_level not in ('read', 'edit'):
        return False, "Invalid permission level. Must be 'read' or 'edit'"
        
    target_user = User.query.filter_by(username=target_username.strip()).first()
    if not target_user:
        return False, f"User '{target_username}' not found in system"
        
    if target_user.id == doc.owner_id:
        return False, "Target user is already the document owner"
        
    # Upsert permission
    perm = DocumentPermission.query.filter_by(document_id=doc.id, user_id=target_user.id).first()
    if perm:
        perm.permission = permission_level
        perm.granted_by = granter.id
    else:
        perm = DocumentPermission(
            document_id=doc.id,
            user_id=target_user.id,
            permission=permission_level,
            granted_by=granter.id
        )
        db.session.add(perm)
        
    db.session.commit()
    
    log_event(
        action='GRANT_PERMISSION',
        status='ALLOWED',
        user=granter,
        document=doc,
        reason=f"Granted '{permission_level}' to user '{target_user.username}'"
    )
    return True, f"Successfully granted '{permission_level}' access to {target_user.username}"


def revoke_permission(revoker, doc_id, target_user_id):
    """
    Instantly revokes access to doc_id from target_user_id.
    Deletes the database grant immediately.
    """
    can_manage, reason, doc = check_document_access(revoker, doc_id, required_permission='manage')
    if not can_manage:
        log_event(
            action='REVOKE_PERMISSION',
            status='DENIED',
            user=revoker,
            document=doc,
            doc_id=doc_id,
            reason=f"Unauthorized revocation attempt: {reason}"
        )
        return False, f"Permission denied: {reason}"
        
    perm = DocumentPermission.query.filter_by(document_id=doc.id, user_id=target_user_id).first()
    if not perm:
        return False, "Permission grant does not exist or was already revoked"
        
    target_username = perm.user.username if perm.user else f"User #{target_user_id}"
    db.session.delete(perm)
    db.session.commit()
    
    # Non-Negotiable #3: Instant Revocation logged
    log_event(
        action='REVOKE_PERMISSION',
        status='ALLOWED',
        user=revoker,
        document=doc,
        reason=f"Instantly revoked access from user '{target_username}'"
    )
    return True, f"Successfully revoked access from {target_username}"


def get_accessible_documents_query(user):
    """
    Returns an SQLAlchemy query filtered strictly to documents the user has rights to see.
    Prevents metadata leakage in search or catalog views.
    """
    if not user or not hasattr(user, 'id'):
        return Document.query.filter(db.false()) # Empty query for unauthenticated
        
    if user.is_admin():
        # Admin can view all document metadata for governance oversight
        return Document.query
        
    # Return documents owned by user OR explicitly shared with user
    return Document.query.filter(
        db.or_(
            Document.owner_id == user.id,
            Document.id.in_(
                db.session.query(DocumentPermission.document_id).filter_by(user_id=user.id)
            )
        )
    )
