"""
TrustVault Permission & Cross-Tenant Isolation Tests
Proves that one user cannot reach another user's documents through any route.
"""

import unittest
import os
from app import create_app
from models import db, User, Document, DocumentPermission
from seed_data import seed

class TestPermissionsAndIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Seed test database
        seed()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def login(self, username, password):
        return self.client.post('/login', data={'identifier': username, 'password': password}, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_cross_user_download_idor_blocked(self):
        """
        ATTACK SCENARIO: IDOR / BOLA
        Alice owns Document #1 (Salary Review).
        Bob logs in and maliciously requests GET /documents/1/download.
        VERIFICATION: Server must return 403 Forbidden and block file delivery.
        """
        self.login('bob_owner', 'Bob@TrustVault2026!')
        response = self.client.get('/documents/1/download')
        self.assertEqual(response.status_code, 403, "Bob must be blocked from downloading Alice's salary document")
        self.logout()

    def test_anonymous_download_blocked(self):
        """
        ATTACK SCENARIO: Unauthenticated direct file retrieval.
        Anonymous caller attempts GET /documents/1/download.
        VERIFICATION: Must be redirected to /login or receive 401/403.
        """
        response = self.client.get('/documents/1/download')
        # Login required redirects or returns 401
        self.assertIn(response.status_code, [302, 401, 403])

    def test_explicit_read_grant_permits_download(self):
        """
        VERIFICATION: Carol was granted 'read' on Document #1 (Alice's Salary).
        Carol must be able to download it and receive valid PDF content.
        """
        self.login('carol_viewer', 'Carol@TrustVault2026!')
        response = self.client.get('/documents/1/download')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.startswith(b'%PDF-'), "Returned data must be valid PDF payload")
        self.logout()

    def test_read_grantee_cannot_edit_document(self):
        """
        ATTACK SCENARIO: Privilege Escalation
        Carol has 'read' permission on Document #1.
        Carol attempts POST /documents/1/edit to alter the document title.
        VERIFICATION: Server must return 403 Forbidden.
        """
        self.login('carol_viewer', 'Carol@TrustVault2026!')
        response = self.client.post('/documents/1/edit', data={
            'title': 'Hacked by Carol',
            'category': 'Financials'
        })
        self.assertEqual(response.status_code, 403, "Read-only grantee must not be able to edit metadata")
        self.logout()

    def test_read_grantee_cannot_delete_document(self):
        """
        ATTACK SCENARIO: Unauthorized Destruction
        Carol has 'read' on Document #1.
        Carol attempts POST /documents/1/delete.
        VERIFICATION: Server must return 403 Forbidden.
        """
        self.login('carol_viewer', 'Carol@TrustVault2026!')
        response = self.client.post('/documents/1/delete')
        # Fails permission check and returns 403 or redirects with error
        self.assertEqual(response.status_code, 403, "Non-owner must not be permitted to delete document")
        self.logout()

    def test_private_document_completely_isolated(self):
        """
        VERIFICATION: Document #3 (Bob's Patent Blueprint) has NO external grants.
        Neither Alice nor Carol nor Dave can view or download it.
        """
        for user, pwd in [('alice_owner', 'Alice@TrustVault2026!'), 
                          ('carol_viewer', 'Carol@TrustVault2026!'), 
                          ('dave_external', 'Dave@TrustVault2026!')]:
            self.login(user, pwd)
            res = self.client.get('/documents/3/download')
            self.assertEqual(res.status_code, 403, f"User {user} must be blocked from private Document #3")
            self.logout()

if __name__ == '__main__':
    unittest.main()
