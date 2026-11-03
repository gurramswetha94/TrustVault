"""
TrustVault Instant Revocation Tests
Proves Non-Negotiable Rule #3: Taking access away works immediately.
"""

import unittest
from app import create_app
from models import db, User, Document, DocumentPermission
from seed_data import seed

class TestInstantRevocation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def login(self, username, password):
        return self.client.post('/login', data={'identifier': username, 'password': password}, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_instant_revocation_lifecycle(self):
        """
        CYCLE:
        1. Dave initially has NO access to Document #1 (Alice's Salary).
        2. Alice grants 'read' access to Dave.
        3. Dave downloads Document #1 -> SUCCESS (200 OK).
        4. Alice revokes Dave's access.
        5. Dave IMMEDIATELY requests Document #1 again -> DENIED (403 Forbidden).
        """
        # Step 1: Verify Dave blocked initially
        self.login('dave_external', 'Dave@TrustVault2026!')
        res = self.client.get('/documents/1/download')
        self.assertEqual(res.status_code, 403, "Dave initially has no access to Doc #1")
        self.logout()

        # Step 2: Alice logs in and grants Dave access
        self.login('alice_owner', 'Alice@TrustVault2026!')
        res_grant = self.client.post('/documents/1/permissions/grant', data={
            'username': 'dave_external',
            'permission': 'read'
        }, follow_redirects=True)
        self.assertEqual(res_grant.status_code, 200)
        self.logout()

        # Step 3: Dave logs in and downloads file successfully
        self.login('dave_external', 'Dave@TrustVault2026!')
        res_dl = self.client.get('/documents/1/download')
        self.assertEqual(res_dl.status_code, 200, "Dave must now have access to Doc #1")
        self.assertTrue(res_dl.data.startswith(b'%PDF-'))
        self.logout()

        # Step 4: Alice logs in and revokes Dave's access
        with self.app.app_context():
            dave_user = User.query.filter_by(username='dave_external').first()
            dave_id = dave_user.id

        self.login('alice_owner', 'Alice@TrustVault2026!')
        res_revoke = self.client.post(f'/documents/1/permissions/revoke/{dave_id}', follow_redirects=True)
        self.assertEqual(res_revoke.status_code, 200)
        self.logout()

        # Step 5: Dave immediately attempts download - MUST BE BLOCKED INSTANTLY
        self.login('dave_external', 'Dave@TrustVault2026!')
        res_after = self.client.get('/documents/1/download')
        self.assertEqual(res_after.status_code, 403, "Zero-latency check: Dave must be blocked immediately upon revocation")
        self.logout()

if __name__ == '__main__':
    unittest.main()
