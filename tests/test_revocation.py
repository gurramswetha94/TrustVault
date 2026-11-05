"""
TrustVault Instant Revocation Tests
Proves Non-Negotiable Rule #3: Taking access away works immediately.
"""

import unittest
from datetime import datetime, timezone, timedelta
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

    def test_expiring_permission_self_revocation(self):
        """
        SELF-REVOKING ACCESS TEST:
        1. Alice grants Carol 'read' access to Doc #2 with an expiration window of 1 hour.
        2. Carol downloads Doc #2 -> SUCCESS (200 OK).
        3. Expiration threshold is crossed (grant passes its expires_at timestamp).
        4. Carol requests Doc #2 again -> IMMEDIATELY BLOCKED (403 Forbidden).
        5. Doc #2 is automatically removed from Carol's accessible search/dashboard catalog.
        """
        # Step 1: Alice grants temporary 1-hour access to Carol for Doc #2
        self.login('alice_owner', 'Alice@TrustVault2026!')
        res_grant = self.client.post('/documents/2/permissions/grant', data={
            'username': 'carol_viewer',
            'permission': 'read',
            'duration_hours': '1'
        }, follow_redirects=True)
        self.assertEqual(res_grant.status_code, 200)
        self.logout()

        # Step 2: Carol accesses document while grant is active
        self.login('carol_viewer', 'Carol@TrustVault2026!')
        res_active = self.client.get('/documents/2/download')
        self.assertEqual(res_active.status_code, 200, "Carol must have access while grant is valid")
        self.logout()

        # Step 3: Simulate time elapsing past the expiration window
        with self.app.app_context():
            carol = User.query.filter_by(username='carol_viewer').first()
            perm = DocumentPermission.query.filter_by(document_id=2, user_id=carol.id).first()
            self.assertIsNotNone(perm)
            self.assertIsNotNone(perm.expires_at)
            # Set expiration to 10 minutes in the past
            perm.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
            db.session.commit()

        # Step 4: Carol attempts download after expiration - MUST BE SELF-REVOKED (403)
        self.login('carol_viewer', 'Carol@TrustVault2026!')
        res_expired = self.client.get('/documents/2/download')
        self.assertEqual(res_expired.status_code, 403, "Expired grant must self-revoke and return 403 Forbidden")
        
        # Step 5: Verify Doc #2 no longer appears in dashboard
        res_dash = self.client.get('/dashboard')
        self.assertNotIn(b"Master Services Agreement - Enterprise Corp", res_dash.data, "Expired doc must disappear from dashboard")
        self.logout()

    def test_single_use_burn_after_reading_grant(self):
        """
        SINGLE-USE / BURN-AFTER-READING REVOCATION TEST:
        1. Alice grants Carol access to Doc #2 with max_downloads=1.
        2. Carol downloads Doc #2 once -> SUCCESS (200 OK).
        3. Carol immediately attempts to download Doc #2 a 2nd time -> BLOCKED (403 Forbidden).
        4. Carol attempts to view Doc #2 detail page -> BLOCKED (403 Forbidden).
        5. Doc #2 is automatically removed from Carol's dashboard and search catalog.
        """
        # Step 1: Alice grants 1-time single-use access to Carol for Doc #2
        self.login('alice_owner', 'Alice@TrustVault2026!')
        res_grant = self.client.post('/documents/2/permissions/grant', data={
            'username': 'carol_viewer',
            'permission': 'read',
            'max_downloads': '1'
        }, follow_redirects=True)
        self.assertEqual(res_grant.status_code, 200)
        self.logout()

        # Step 2: Carol performs 1st download - MUST SUCCEED (200 OK)
        self.login('carol_viewer', 'Carol@TrustVault2026!')
        res_dl1 = self.client.get('/documents/2/download')
        self.assertEqual(res_dl1.status_code, 200, "Carol must succeed on 1st download")
        self.assertTrue(res_dl1.data.startswith(b'%PDF-'))

        # Step 3: Carol attempts 2nd download - MUST BE BLOCKED (403 Forbidden)
        res_dl2 = self.client.get('/documents/2/download')
        self.assertEqual(res_dl2.status_code, 403, "Burned grant must reject 2nd download attempt with 403")

        # Step 4: Carol attempts to view metadata detail - MUST BE BLOCKED (403 Forbidden)
        res_detail = self.client.get('/documents/2')
        self.assertEqual(res_detail.status_code, 403, "Exhausted quota must block document detail access")

        # Step 5: Verify Doc #2 disappeared from Carol's catalog
        res_dash = self.client.get('/dashboard')
        self.assertNotIn(b"Master Services Agreement - Enterprise Corp", res_dash.data, "Burned doc must vanish from catalog")
        self.logout()

if __name__ == '__main__':
    unittest.main()

