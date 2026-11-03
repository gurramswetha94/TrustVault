"""
TrustVault Upload Security Tests
Verifies magic bytes inspection, filename path-traversal sanitization,
and extension whitelisting.
"""

import unittest
import io
from app import create_app
from seed_data import seed

class TestUploadSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def login(self, username, password):
        return self.client.post('/login', data={'identifier': username, 'password': password}, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_extension_spoofing_blocked_by_magic_bytes(self):
        """
        ATTACK SCENARIO: File disguised as PDF (e.g. executable or shell script).
        Attacker renames a binary file to 'exploit.pdf', but bytes start with 'MZ' or '#!/bin/bash'.
        VERIFICATION: Magic byte sniffing detects mismatch and rejects upload.
        """
        self.login('alice_owner', 'Alice@TrustVault2026!')
        fake_pdf = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00WindowsExecutablePayload")
        
        response = self.client.post('/documents/upload', data={
            'title': 'Fake PDF Attack',
            'category': 'General',
            'document_file': (fake_pdf, 'fake.pdf')
        }, follow_redirects=True)
        
        # Flash message contains rejection
        self.assertIn(b"File header signature does not match", response.data)
        self.logout()

    def test_prohibited_extension_blocked(self):
        """
        ATTACK SCENARIO: Uploading raw executable or script (.exe, .sh, .py).
        VERIFICATION: Extension whitelist rejects upload.
        """
        self.login('alice_owner', 'Alice@TrustVault2026!')
        bad_file = io.BytesIO(b"echo 'malicious script'")
        
        response = self.client.post('/documents/upload', data={
            'title': 'Script Attack',
            'category': 'General',
            'document_file': (bad_file, 'exploit.sh')
        }, follow_redirects=True)
        
        self.assertIn(b"is prohibited", response.data)
        self.logout()

    def test_path_traversal_filename_sanitized(self):
        """
        ATTACK SCENARIO: Path Traversal
        Attacker sets filename to '../../../../etc/passwd' or '..\\..\\windows\\system32\\cmd.exe'.
        VERIFICATION: secure_filename sanitizes it to safe basename.
        """
        self.login('alice_owner', 'Alice@TrustVault2026!')
        valid_pdf = io.BytesIO(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
        
        response = self.client.post('/documents/upload', data={
            'title': 'Path Traversal Test',
            'category': 'General',
            'document_file': (valid_pdf, '../../../../safe_report.pdf')
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        # Should not throw path error, securely saved as UUID
        self.assertIn(b"uploaded and encrypted successfully", response.data)
        self.logout()

if __name__ == '__main__':
    unittest.main()

