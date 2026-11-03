"""
TrustVault Database Models
Defines schema for Users, Documents, Permissions, and Tamper-Evident Audit Logs.
"""

from datetime import datetime, timezone
import hashlib
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='viewer') # admin, owner, viewer
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    owned_documents = db.relationship('Document', backref='owner', lazy=True, cascade='all, delete-orphan')
    permissions_received = db.relationship('DocumentPermission', foreign_keys='DocumentPermission.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
        
    def is_owner(self):
        return self.role in ('owner', 'admin')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }


class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, default='General', index=True)
    
    # Secure storage references
    original_filename = db.Column(db.String(255), nullable=False)
    storage_uuid = db.Column(db.String(64), unique=True, nullable=False, index=True)
    file_size = db.Column(db.Integer, nullable=False) # bytes
    mime_type = db.Column(db.String(100), nullable=False)
    sha256_checksum = db.Column(db.String(64), nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    permissions = db.relationship('DocumentPermission', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'owner_id': self.owner_id,
            'owner_username': self.owner.username if self.owner else None,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'sha256_checksum': self.sha256_checksum,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class DocumentPermission(db.Model):
    __tablename__ = 'document_permissions'
    __table_args__ = (
        db.UniqueConstraint('document_id', 'user_id', name='uq_doc_user_permission'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    permission = db.Column(db.String(20), nullable=False, default='read') # read, edit
    
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    granter = db.relationship('User', foreign_keys=[granted_by])

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'permission': self.permission,
            'granted_by': self.granter.username if self.granter else None,
            'granted_at': self.granted_at.isoformat()
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True, index=True) # Nullable for unauthenticated attacks
    username = db.Column(db.String(80), nullable=False)
    document_id = db.Column(db.Integer, nullable=True, index=True)
    document_title = db.Column(db.String(200), nullable=True)
    
    action = db.Column(db.String(50), nullable=False, index=True) 
    # UPLOAD, DOWNLOAD, EDIT, DELETE, GRANT_PERMISSION, REVOKE_PERMISSION, LOGIN, LOGOUT, SUSPICIOUS_PROBE
    
    status = db.Column(db.String(20), nullable=False, index=True) # ALLOWED, DENIED
    reason = db.Column(db.String(255), nullable=True)
    
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Tamper-Evident Cryptographic Hash Chaining
    # Each record signs its contents concatenated with the previous record's hash
    previous_hash = db.Column(db.String(64), nullable=False, default='GENESIS_HASH')
    record_hash = db.Column(db.String(64), nullable=False)

    @staticmethod
    def calculate_hash(record_id, user_id, doc_id, action, status, timestamp_iso, prev_hash):
        content = f"{record_id}|{user_id}|{doc_id}|{action}|{status}|{timestamp_iso}|{prev_hash}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'document_id': self.document_id,
            'document_title': self.document_title,
            'action': self.action,
            'status': self.status,
            'reason': self.reason,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat(),
            'previous_hash': self.previous_hash,
            'record_hash': self.record_hash
        }
