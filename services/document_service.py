"""
TrustVault Document Service
Handles file security validation (magic bytes, extension whitelist, size ceiling),
isolated storage outside public web roots, SHA-256 checksumming, and authorized streaming.
"""

import os
import uuid
import hashlib
from werkzeug.utils import secure_filename
from flask import current_app, send_file, abort
from models import db, Document
from services.audit_service import log_event
from services.permission_service import check_document_access

def validate_uploaded_file(file_storage, allowed_extensions, magic_signatures):
    """
    Performs deep validation of the uploaded file:
    1. Sanitizes filename
    2. Enforces extension whitelist
    3. Sniffs magic byte headers to prevent extension spoofing (e.g. executable disguised as pdf)
    4. Computes SHA-256 fingerprint
    """
    if not file_storage or file_storage.filename == '':
        return False, "No file selected", None, None, None, None
        
    filename = secure_filename(file_storage.filename)
    if not filename:
        return False, "Invalid or unsafe filename", None, None, None, None
        
    if '.' not in filename:
        return False, "File must have an explicit extension", None, None, None, None
        
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return False, f"File extension '.{ext}' is prohibited. Allowed: {', '.join(sorted(allowed_extensions))}", None, None, None, None
        
    # Read initial bytes to check magic signature
    header = file_storage.read(16)
    file_storage.seek(0) # Reset stream pointer
    
    if ext in magic_signatures:
        signatures = magic_signatures[ext]
        matches = any(header.startswith(sig) for sig in signatures)
        if not matches:
            return False, f"File header signature does not match declared type '.{ext}'. Possible disguised executable or corrupted file.", None, None, None, None
    elif ext in ('txt', 'csv'):
        # For plaintext/csv, verify it doesn't contain binary null bytes
        sample = file_storage.read(1024)
        file_storage.seek(0)
        if b'\x00' in sample:
            return False, "Plaintext file contains forbidden null/binary bytes", None, None, None, None
            
    # Read full file into memory/buffer to compute SHA-256 and get true size
    content = file_storage.read()
    file_size = len(content)
    file_storage.seek(0)
    
    if file_size == 0:
        return False, "Uploaded file is empty (0 bytes)", None, None, None, None
        
    sha256_hash = hashlib.sha256(content).hexdigest()
    mime_type = file_storage.mimetype or 'application/octet-stream'
    
    return True, "Valid", filename, ext, file_size, sha256_hash


def store_and_register_document(uploader, file_storage, title, description, category):
    """
    Saves the file into secure vault storage (outside web root) and records metadata.
    """
    cfg = current_app.config
    is_valid, err_msg, safe_name, ext, file_size, checksum = validate_uploaded_file(
        file_storage,
        cfg['ALLOWED_EXTENSIONS'],
        cfg['MAGIC_SIGNATURES']
    )
    
    if not is_valid:
        log_event(
            action='UPLOAD',
            status='DENIED',
            user=uploader,
            reason=f"Validation failed: {err_msg}"
        )
        return False, err_msg, None
        
    storage_dir = cfg['VAULT_STORAGE_DIR']
    os.makedirs(storage_dir, exist_ok=True)
    
    # Store with randomized UUID to eliminate any path traversal or filename collision
    storage_uuid = str(uuid.uuid4())
    disk_filename = f"{storage_uuid}.bin"
    file_path = os.path.join(storage_dir, disk_filename)
    
    try:
        file_storage.save(file_path)
    except Exception as e:
        log_event(
            action='UPLOAD',
            status='DENIED',
            user=uploader,
            reason=f"Disk I/O error during save: {str(e)}"
        )
        return False, f"Failed to persist file: {str(e)}", None
        
    doc = Document(
        owner_id=uploader.id,
        title=title.strip() if title else safe_name,
        description=description.strip() if description else '',
        category=category.strip() if category else 'General',
        original_filename=safe_name,
        storage_uuid=storage_uuid,
        file_size=file_size,
        mime_type=file_storage.mimetype or 'application/octet-stream',
        sha256_checksum=checksum
    )
    db.session.add(doc)
    db.session.commit()
    
    log_event(
        action='UPLOAD',
        status='ALLOWED',
        user=uploader,
        document=doc,
        reason=f"Uploaded '{safe_name}' ({file_size} bytes, SHA-256: {checksum[:12]}...)"
    )
    return True, "Document uploaded securely", doc


def stream_document_content(user, doc_id):
    """
    THE CRITICAL AUTHORIZATION GATEWAY:
    Evaluates permission in real-time before streaming any file bytes.
    Records BOTH allowed and refused/denied attempts in the audit trail.
    """
    can_access, reason, doc = check_document_access(user, doc_id, required_permission='read')
    
    if not can_access:
        # Non-Negotiable #2: Record refused attempt in the audit ledger
        log_event(
            action='DOWNLOAD',
            status='DENIED',
            user=user,
            document=doc,
            doc_id=doc_id,
            reason=reason
        )
        abort(403, description=f"Access Denied: {reason}")
        
    # User is authorized: Record allowed access
    log_event(
        action='DOWNLOAD',
        status='ALLOWED',
        user=user,
        document=doc,
        reason=reason
    )
    
    storage_dir = current_app.config['VAULT_STORAGE_DIR']
    file_path = os.path.join(storage_dir, f"{doc.storage_uuid}.bin")
    
    if not os.path.exists(file_path):
        abort(404, description="File payload missing from vault storage")
        
    # Stream bytes securely with original filename attachment
    return send_file(
        file_path,
        as_attachment=True,
        download_name=doc.original_filename,
        mimetype=doc.mime_type
    )


def delete_document_record(user, doc_id):
    """
    Deletes the document and removes its binary payload from disk.
    Strictly restricted to the document owner or system administrator.
    """
    can_delete, reason, doc = check_document_access(user, doc_id, required_permission='manage')
    
    if not can_delete:
        log_event(
            action='DELETE',
            status='DENIED',
            user=user,
            document=doc,
            doc_id=doc_id,
            reason=f"Unauthorized deletion attempt: {reason}"
        )
        return False, f"Permission denied: {reason}"
        
    doc_title = doc.title
    doc_storage_uuid = doc.storage_uuid
    storage_dir = current_app.config['VAULT_STORAGE_DIR']
    file_path = os.path.join(storage_dir, f"{doc_storage_uuid}.bin")
    
    # Remove database record
    db.session.delete(doc)
    db.session.commit()
    
    # Remove physical file
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"[WARNING] Failed to remove physical file {file_path}: {e}")
            
    log_event(
        action='DELETE',
        status='ALLOWED',
        user=user,
        doc_id=doc_id,
        doc_title=doc_title,
        reason=f"Permanently deleted document '{doc_title}'"
    )
    return True, f"Document '{doc_title}' deleted successfully"
