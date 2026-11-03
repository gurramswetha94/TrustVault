"""
TrustVault Authentication Service
Handles session-based identity management, bcrypt password verification,
and route-level authentication/authorization decorators.
"""

from functools import wraps
from flask import session, redirect, url_for, abort, request, jsonify
from models import db, User
from services.audit_service import log_event

def get_current_user():
    """
    Retrieves the currently authenticated user from the server-side session.
    Returns User instance or None.
    """
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    if not user or not user.is_active:
        session.clear()
        return None
    return user


def authenticate_user(username_or_email, password):
    """
    Validates user credentials against stored bcrypt hash.
    Records successful logins and failed login attempts in the audit trail.
    """
    identifier = username_or_email.strip()
    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()
    
    if not user or not user.check_password(password):
        log_event(
            action='LOGIN',
            status='DENIED',
            reason=f"Failed login attempt for identifier '{identifier}'"
        )
        return None, "Invalid username or password"
        
    if not user.is_active:
        log_event(
            action='LOGIN',
            status='DENIED',
            user=user,
            reason="Account is deactivated"
        )
        return None, "This account has been deactivated"
        
    # Set server-side session
    session.clear()
    session['user_id'] = user.id
    session['user_role'] = user.role
    session['username'] = user.username
    session.permanent = True
    
    log_event(
        action='LOGIN',
        status='ALLOWED',
        user=user,
        reason=f"User '{user.username}' logged in successfully with role '{user.role}'"
    )
    return user, "Login successful"


def logout_current_user():
    """
    Terminates the session and logs the logout event.
    """
    user = get_current_user()
    if user:
        log_event(
            action='LOGOUT',
            status='ALLOWED',
            user=user,
            reason="User logged out"
        )
    session.clear()


def login_required(f):
    """
    Decorator requiring an active authenticated user session.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required', 'code': 'UNAUTHORIZED'}), 401
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    """
    Decorator enforcing role-based access control (RBAC).
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required', 'code': 'UNAUTHORIZED'}), 401
                return redirect(url_for('auth.login', next=request.url))
                
            if user.role not in allowed_roles:
                log_event(
                    action='SUSPICIOUS_PROBE',
                    status='DENIED',
                    user=user,
                    reason=f"Role violation: user has role '{user.role}', required: {allowed_roles}"
                )
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Forbidden: Insufficient role privileges', 'code': 'FORBIDDEN'}), 403
                abort(403, description="Forbidden: Insufficient role privileges")
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
