"""
TrustVault Audit Trail & Tamper-Evidence Tests
Proves Non-Negotiable Rule #2: You can prove who reached it, including refused attempts,
and the audit ledger cannot be quietly altered.
"""

import unittest
from app import create_app
from models import db, AuditLog
from services.audit_service import verify_chain_integrity
from seed_data import seed

class TestAuditTrailAndTamperEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def login(self, username, password):
        return self.client.post('/login', data={'identifier': username, 'password': password}, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_refused_attempt_is_logged_in_audit_trail(self):
        """
        NON-NEGOTIABLE RULE #2:
        When Bob attempts to download Alice's salary document (#1) and is denied (403),
        an audit record with status='DENIED' and action='DOWNLOAD' MUST be created.
        """
        with self.app.app_context():
            initial_denied_count = AuditLog.query.filter_by(status='DENIED').count()

        # Execute unauthorized attempt
        self.login('bob_owner', 'Bob@TrustVault2026!')
        res = self.client.get('/documents/1/download')
        self.assertEqual(res.status_code, 403)
        self.logout()

        with self.app.app_context():
            new_denied_count = AuditLog.query.filter_by(status='DENIED').count()
            self.assertEqual(new_denied_count, initial_denied_count + 1, "Refused attempt must be logged in audit trail")
            
            latest_denied = AuditLog.query.filter_by(status='DENIED').order_by(AuditLog.id.desc()).first()
            self.assertEqual(latest_denied.username, 'bob_owner')
            self.assertEqual(latest_denied.document_id, 1)
            self.assertEqual(latest_denied.action, 'DOWNLOAD')

    def test_tamper_detection_in_cryptographic_ledger(self):
        """
        NON-NEGOTIABLE RULE #2 PROOF:
        If an attacker or rogue administrator modifies an audit log entry in the database
        (e.g., changes status from 'DENIED' to 'ALLOWED' to conceal an intrusion),
        the cryptographic hash chain breaks and verify_chain_integrity() detects it.
        """
        with self.app.app_context():
            # Initial state: Ledger is 100% valid
            is_valid, errors = verify_chain_integrity()
            self.assertTrue(is_valid, "Initial ledger must be cryptographically intact")

            # Simulate an attacker altering an audit record in the database
            target_record = AuditLog.query.filter_by(status='DENIED').first()
            self.assertIsNotNone(target_record)
            
            original_status = target_record.status
            # Malicious alteration
            target_record.status = 'ALLOWED'
            db.session.commit()

            # Now verify integrity: MUST DETECT COMPROMISE
            is_tampered_valid, tampered_errors = verify_chain_integrity()
            self.assertFalse(is_tampered_valid, "Tampered ledger must be flagged as invalid")
            self.assertTrue(any(e['record_id'] == target_record.id for e in tampered_errors))

            # Restore original state to keep subsequent tests clean
            target_record.status = original_status
            db.session.commit()
            
            is_restored_valid, _ = verify_chain_integrity()
            self.assertTrue(is_restored_valid, "Restored ledger must be valid again")

if __name__ == '__main__':
    unittest.main()

