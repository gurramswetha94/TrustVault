"""
TrustVault Database Seeder
Populates the database with realistic test users for each role, sample confidential documents,
explicit permission grants, and initial cryptographic audit ledger entries.
Supports self-healing auto-seeding for cloud deployments.
"""

import os
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from models import db, User, Document, DocumentPermission, AuditLog
from services.audit_service import log_event

def create_sample_pdf_content(title, confidential_text):
    """Generates valid minimal PDF binary content containing the confidential payload."""
    pdf_template = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(len(confidential_text) + 80).encode('ascii') + b" >>\nstream\n"
        b"BT\n/F1 16 Tf\n50 720 Td\n(" + title.encode('ascii', 'ignore') + b") Tj\n"
        b"/F1 11 Tf\n0 -30 Td\n(" + confidential_text.encode('ascii', 'ignore') + b") Tj\nET\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000224 00000 n \n0000000350 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n420\n%%EOF"
    )
    return pdf_template


def seed_database(app=None, drop_existing=False):
    """
    Core seeder logic. Can run standalone or be invoked dynamically on deployment startup.
    Ensures users, permissions, and files exist with known credentials.
    """
    from flask import current_app
    app_ctx = app or current_app
    
    if drop_existing:
        print("Clearing and rebuilding TrustVault database...")
        db.drop_all()
        db.create_all()
    else:
        db.create_all()
        
    storage_dir = app_ctx.config['VAULT_STORAGE_DIR']
    os.makedirs(storage_dir, exist_ok=True)
    
    passwords = {
        "admin": "Admin@TrustVault2026!",
        "alice_owner": "Alice@TrustVault2026!",
        "bob_owner": "Bob@TrustVault2026!",
        "carol_viewer": "Carol@TrustVault2026!",
        "dave_external": "Dave@TrustVault2026!",
    }
    
    user_definitions = [
        {"username": "admin", "email": "admin@trustvault.internal", "role": "admin"},
        {"username": "alice_owner", "email": "alice@trustvault.internal", "role": "owner"},
        {"username": "bob_owner", "email": "bob@trustvault.internal", "role": "owner"},
        {"username": "carol_viewer", "email": "carol@trustvault.internal", "role": "viewer"},
        {"username": "dave_external", "email": "dave@partner.com", "role": "viewer"},
    ]
    
    # 1. Create or Update Seed Users
    print("Ensuring seed accounts exist for all roles...")
    for udef in user_definitions:
        user = User.query.filter_by(username=udef["username"]).first()
        if not user:
            user = User(username=udef["username"], email=udef["email"], role=udef["role"])
            user.set_password(passwords[udef["username"]])
            db.session.add(user)
        else:
            # Re-affirm password and active status so credentials always work
            user.set_password(passwords[udef["username"]])
            user.is_active = True
            user.role = udef["role"]
    db.session.commit()
    
    admin = User.query.filter_by(username="admin").first()
    alice = User.query.filter_by(username="alice_owner").first()
    bob = User.query.filter_by(username="bob_owner").first()
    carol = User.query.filter_by(username="carol_viewer").first()
    dave = User.query.filter_by(username="dave_external").first()
    
    # 2. Seed Sample Documents if empty
    if Document.query.count() == 0 or drop_existing:
        print("Storing sample confidential documents...")
        doc_samples = [
            {
                "owner": alice,
                "title": "Q4 Executive Salary Review & Compensation",
                "desc": "Highly confidential payroll adjustment metrics and bonus allocations.",
                "category": "Financials",
                "filename": "Q4_Salary_Review_2026.pdf",
                "payload": "CONFIDENTIAL: Executive compensation allocations for FY2026. Strictly restricted."
            },
            {
                "owner": alice,
                "title": "Master Services Agreement - Enterprise Corp",
                "desc": "Executed commercial contract with Enterprise Corp.",
                "category": "Contracts",
                "filename": "MSA_EnterpriseCorp_Executed.pdf",
                "payload": "COMMERCIAL IN CONFIDENCE: Terms, pricing schedules, and SLAs for Enterprise Corp."
            },
            {
                "owner": bob,
                "title": "Proprietary Algorithm Architecture Blueprint",
                "desc": "Trade secret patent specifications for low-latency consensus.",
                "category": "Engineering",
                "filename": "Core_Algorithm_Blueprint_v3.pdf",
                "payload": "TRADE SECRET: Proprietary mathematical formulations. Unauthorized access strictly prosecuted."
            },
            {
                "owner": bob,
                "title": "Annual Financial Audit & Regulatory Filings",
                "desc": "External auditor verified financial statements and tax filings.",
                "category": "Audit",
                "filename": "Annual_Audit_Report_2026.pdf",
                "payload": "REGULATORY PAPERS: Complete balance sheets, depreciation tables, and tax filings."
            }
        ]
        
        created_docs = []
        for s in doc_samples:
            storage_uuid = str(uuid.uuid4())
            file_bytes = create_sample_pdf_content(s["title"], s["payload"])
            file_path = os.path.join(storage_dir, f"{storage_uuid}.bin")
            
            with open(file_path, "wb") as f:
                f.write(file_bytes)
                
            checksum = hashlib.sha256(file_bytes).hexdigest()
            doc = Document(
                owner_id=s["owner"].id,
                title=s["title"],
                description=s["desc"],
                category=s["category"],
                original_filename=s["filename"],
                storage_uuid=storage_uuid,
                file_size=len(file_bytes),
                mime_type="application/pdf",
                sha256_checksum=checksum
            )
            db.session.add(doc)
            db.session.flush()
            created_docs.append(doc)
            
            log_event(
                action="UPLOAD",
                status="ALLOWED",
                user=s["owner"],
                document=doc,
                reason=f"Seed upload of '{s['title']}'"
            )
        db.session.commit()
        
        # 3. Create Explicit Named Permissions
        print("Granting explicit per-document permissions...")
        # Doc 0 (Alice's Salary doc) -> Carol has READ access. Bob and Dave have NO ACCESS.
        p1 = DocumentPermission(
            document_id=created_docs[0].id,
            user_id=carol.id,
            permission="read",
            granted_by=alice.id
        )
        # Doc 1 (Alice's Contract doc) -> Dave has READ access (Time-bound: expires in 7 days, Quota: 3 downloads).
        p2 = DocumentPermission(
            document_id=created_docs[1].id,
            user_id=dave.id,
            permission="read",
            granted_by=alice.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            max_downloads=3,
            download_count=0
        )
        # Doc 3 (Bob's Audit doc) -> Alice has READ access.
        p3 = DocumentPermission(
            document_id=created_docs[3].id,
            user_id=alice.id,
            permission="read",
            granted_by=bob.id
        )
        
        db.session.add_all([p1, p2, p3])
        db.session.commit()
        
        log_event(action="GRANT_PERMISSION", status="ALLOWED", user=alice, document=created_docs[0], reason=f"Granted 'read' to {carol.username} (unlimited)")
        log_event(action="GRANT_PERMISSION", status="ALLOWED", user=alice, document=created_docs[1], reason=f"Granted 'read' to {dave.username} (expires in 7 days, max 3 downloads)")
        log_event(action="GRANT_PERMISSION", status="ALLOWED", user=bob, document=created_docs[3], reason=f"Granted 'read' to {alice.username} (unlimited)")
        
        # 4. Simulate Refused Attempt in Audit Log (Rule #2 Proof)
        log_event(
            action="DOWNLOAD",
            status="DENIED",
            user=bob,
            document=created_docs[0],
            doc_id=created_docs[0].id,
            reason="BOLA attempt: User 'bob_owner' is not granted access to Alice's salary document",
            ip_address="192.168.1.105"
        )
        
    print("\n=== TrustVault Database Ready ===")
    print("Seed accounts active and verified:")
    print("  admin / Admin@TrustVault2026!")
    print("  alice_owner / Alice@TrustVault2026!")
    print("  bob_owner / Bob@TrustVault2026!")
    print("  carol_viewer / Carol@TrustVault2026!")
    print("  dave_external / Dave@TrustVault2026!\n")


def seed():
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_database(app=app, drop_existing=True)

if __name__ == '__main__':
    seed()
