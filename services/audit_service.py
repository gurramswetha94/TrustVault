"""
TrustVault Audit Service
Handles append-only logging of all events (allowed & denied) with SHA-256 cryptographic hash chaining.
Provides tamper-evidence verification across the complete ledger.
"""

from datetime import datetime, timezone
from flask import request
from models import db, AuditLog

def log_event(action, status, user=None, document=None, doc_id=None, doc_title=None, reason=None, ip_address=None, user_agent=None):
    """
    Appends an immutable audit log record linked to the previous record's hash.
    Records BOTH successful access (ALLOWED) and blocked/unauthorized attempts (DENIED).
    """
    try:
        # Determine user identity
        user_id = user.id if user and hasattr(user, 'id') else None
        username = user.username if user and hasattr(user, 'username') else 'ANONYMOUS_OR_SYSTEM'
        
        # Determine document identity
        if document:
            target_doc_id = document.id
            target_doc_title = document.title
        elif doc_id:
            target_doc_id = doc_id
            target_doc_title = doc_title or f"Document #{doc_id}"
        else:
            target_doc_id = None
            target_doc_title = None
            
        # Determine client network metadata
        client_ip = ip_address
        client_ua = user_agent
        if request:
            try:
                client_ip = client_ip or request.headers.get('X-Forwarded-For', request.remote_addr)
                client_ua = client_ua or request.headers.get('User-Agent', '')[:250]
            except RuntimeError:
                pass # Outside request context (e.g. background task / CLI)
                
        now = datetime.now(timezone.utc)
        
        # Use ISO-8601 second precision timestamp string for database-agnostic hash stability
        timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Get latest audit entry to establish cryptographic chain
        last_log = AuditLog.query.order_by(AuditLog.id.desc()).first()
        prev_hash = last_log.record_hash if last_log else "GENESIS_BLOCK_000000000000000000000000000000000000000000000000000"
        
        # Placeholder hash for initial flush to get auto-increment ID
        new_log = AuditLog(
            user_id=user_id,
            username=username,
            document_id=target_doc_id,
            document_title=target_doc_title,
            action=action,
            status=status,
            reason=reason,
            ip_address=client_ip,
            user_agent=client_ua,
            timestamp=now,
            previous_hash=prev_hash,
            record_hash="PENDING"
        )
        db.session.add(new_log)
        db.session.flush() # Allocates new_log.id
        
        # Compute true cryptographic hash
        new_log.record_hash = AuditLog.calculate_hash(
            record_id=new_log.id,
            user_id=new_log.user_id,
            doc_id=new_log.document_id,
            action=new_log.action,
            status=new_log.status,
            timestamp_iso=timestamp_str,
            prev_hash=prev_hash
        )
        db.session.commit()
        return new_log
    except Exception as e:
        db.session.rollback()
        # Fallback logging to console to ensure failure is visible
        print(f"[CRITICAL AUDIT FAILURE] Failed to write audit log: {e}")
        return None


def verify_chain_integrity():
    """
    Audits the entire audit log database to detect if any records were modified,
    inserted, or deleted out-of-band (e.g., direct SQL tampering by an attacker).
    Returns (is_valid: bool, compromised_records: list)
    """
    logs = AuditLog.query.order_by(AuditLog.id.asc()).all()
    if not logs:
        return True, []
        
    expected_prev = "GENESIS_BLOCK_000000000000000000000000000000000000000000000000000"
    compromised = []
    
    for log in logs:
        # Check 1: Does previous_hash match the record before it?
        if log.previous_hash != expected_prev:
            compromised.append({
                'record_id': log.id,
                'issue': 'Broken hash chain link',
                'expected_prev': expected_prev,
                'found_prev': log.previous_hash
            })
            
        # Check 2: Does current record_hash match content recalculation?
        timestamp_str = log.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
        recomputed_hash = AuditLog.calculate_hash(
            record_id=log.id,
            user_id=log.user_id,
            doc_id=log.document_id,
            action=log.action,
            status=log.status,
            timestamp_iso=timestamp_str,
            prev_hash=log.previous_hash
        )
        
        if log.record_hash != recomputed_hash:
            compromised.append({
                'record_id': log.id,
                'issue': 'Data content altered after recording',
                'expected_hash': recomputed_hash,
                'recorded_hash': log.record_hash
            })
            
        expected_prev = log.record_hash
        
    is_valid = len(compromised) == 0
    return is_valid, compromised
