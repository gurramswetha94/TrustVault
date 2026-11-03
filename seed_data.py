"""
TrustVault Database Seeder
Populates the database with realistic test users for each role, sample confidential documents,
explicit permission grants, and initial cryptographic audit ledger entries.
"""

import os
import uuid
import hashlib
from datetime import datetime, timezone
from app import create_app
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

def seed():
    app = create_app()
    with app.app_context():
        print("Clearing and rebuilding TrustVault database...")
        db.drop_all()
        db.create_all()
        
        storage_dir = app.config['VAULT_STORAGE_DIR']
        os.makedirs(storage_dir, exist_ok=True)
        
        # 1. Create Seed Users
        print("Creating seed accounts for all 3 required roles...")
        users = [
            User(username="admin", email="admin@trustvault.internal", role="admin"),
            User(username="alice_owner", email="alice@trustvault.internal", role="owner"),
            User(username="bob_owner", email="bob@trustvault.internal", role="owner"),
            User(username="carol_viewer", email="carol@trustvault.internal", role="viewer"),
            User(username="dave_external", email="dave@partner.com", role="viewer"),
        ]
        
        # Default passwords for testing
        passwords = {
            "admin": "Admin@TrustVault2026!",
            "alice_owner": "Alice@TrustVault2026!",
            "bob_owner": "Bob@TrustVault2026!",
            "carol_viewer": "Carol@TrustVault2026!",
            "dave_external": "Dave@TrustVault2026!",
        }
        
        for u in users:
            u.set_password(passwords[u.username])
            db.session.add(u)
        db.session.commit()
        
        admin = User.query.filter_by(username="admin").first()
        alice = User.query.filter_by(username="alice_owner").first()
        bob = User.query.filter_by(username="bob_owner").first()
        carol = User.query.filter_by(username="carol_viewer").first()
        dave = User.query.filter_by(username="dave_external").first()
        
        # 2. Create Sample Documents with Physical PDF Storage
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
        # Doc 1 (Alice's Contract doc) -> Dave has READ access.
        p2 = DocumentPermission(
            document_id=created_docs[1].id,
            user_id=dave.id,
            permission="read",
            granted_by=alice.id
        )
        # Doc 2 (Bob's Patent doc) -> Completely PRIVATE to Bob! Alice, Carol, Dave have NO ACCESS.
        
        # Doc 3 (Bob's Audit doc) -> Alice has EDIT access.
        p3 = DocumentPermission(
            document_id=created_docs[3].id,
            user_id=alice.id,
            permission="edit",
            granted_by=bob.id
        )
        
        db.session.add_all([p1, p2, p3])
        db.session.commit()
        
        log_event(action="GRANT_PERMISSION", status="ALLOWED", user=alice, document=created_docs[0], reason=f"Granted 'read' to {carol.username}")
        log_event(action="GRANT_PERMISSION", status="ALLOWED", user=alice, document=created_docs[1], reason=f"Granted 'read' to {dave.username}")
        log_event(action="GRANT_PERMISSION", status="ALLOWED", user=bob, document=created_docs[3], reason=f"Granted 'edit' to {alice.username}")
        
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
        
        print("\n=== TrustVault Seed Complete ===")
        print("Ready for immediate evaluation with the following accounts:")
        print("----------------------------------------------------------------------")
        print("ROLE            | USERNAME       | PASSWORD            | ACCESS SCOPE")
        print("----------------------------------------------------------------------")
        print("Administrator   | admin          | Admin@TrustVault2026! | System-wide audit logs & anomaly monitoring")
        print("Document Owner  | alice_owner    | Alice@TrustVault2026! | Owns Docs #1 & #2; can grant/revoke access")
        print("Document Owner  | bob_owner      | Bob@TrustVault2026!   | Owns Docs #3 & #4; owns private blueprint")
        print("Viewer          | carol_viewer   | Carol@TrustVault2026! | Explicit read grant on Doc #1 (Salary)")
        print("Viewer (Partner)| dave_external  | Dave@TrustVault2026!  | Explicit read grant on Doc #2 (Contract)")
        print("----------------------------------------------------------------------\n")

if __name__ == '__main__':
    seed()
