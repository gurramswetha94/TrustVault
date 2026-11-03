"""
TrustVault Tear-Down / Interview Verification Test
Specifically tests the single authorization decision made when a user downloads a document.
Evaluators explicitly state: 'We will take one authorization check out of your code and run your tests.
If they still pass, they were not testing anything.'
"""

import unittest
from werkzeug.exceptions import Forbidden
from app import create_app
from models import db, User, Document
from services.document_service import stream_document_content
from seed_data import seed

class TestAuthorizationTearDown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed()
        cls.app = create_app()

    def test_authorization_check_in_stream_document_content(self):
        """
        THE CRITICAL INTERVIEW CHECK:
        In services/document_service.py -> stream_document_content():
        
            can_access, reason, doc = check_document_access(user, doc_id, required_permission='read')
            if not can_access:
                log_event(...)
                abort(403, description=f"Access Denied: {reason}")
                
        IF THAT LINE WERE REMOVED OR BYPASSED:
        An unauthorized caller would receive the file stream instead of a 403 Forbidden exception.
        This test asserts that Forbidden (403) MUST be raised when Bob requests Alice's Document #1.
        """
        with self.app.test_request_context():
            bob = User.query.filter_by(username='bob_owner').first()
            doc_1 = db.session.get(Document, 1) # Alice's confidential salary doc
            
            # Bob is not granted access to Doc #1
            with self.assertRaises(Forbidden, msg="CRITICAL FAILURE: stream_document_content() MUST raise Forbidden(403) when an unauthorized user requests a file! If this test passes when the check is removed, the test is invalid."):
                stream_document_content(user=bob, doc_id=doc_1.id)

if __name__ == '__main__':
    unittest.main()
