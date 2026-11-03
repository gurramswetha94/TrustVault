"""
TrustVault Configuration Module
Defines security constants, file size ceilings, and environment settings.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Application Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'trustvault-super-secure-dev-key-change-in-prod-883921048')
    
    # Session Configuration (HTTP-only, SameSite strict, secure cookies in production)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Database Configuration (Defaults to SQLite; supports PostgreSQL in production)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'trustvault.db')}")
    # Render/Railway postgres url fix (postgres:// -> postgresql://)
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secure Vault Storage Configuration
    # CRITICAL: Files are stored OUTSIDE any public or static web directory.
    VAULT_STORAGE_DIR = os.environ.get('VAULT_STORAGE_DIR', os.path.join(BASE_DIR, 'vault_storage'))
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB max upload ceiling
    
    # Allowed File Extensions & MIME Signatures
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'txt', 'png', 'jpg', 'jpeg', 'csv'}
    
    # File Magic Signatures (First N bytes)
    MAGIC_SIGNATURES = {
        'pdf': [b'%PDF-'],
        'png': [b'\x89PNG\r\n\x1a\n'],
        'jpg': [b'\xff\xd8\xff'],
        'jpeg': [b'\xff\xd8\xff'],
        'docx': [b'PK\x03\x04'],
        'xlsx': [b'PK\x03\x04'],
    }
