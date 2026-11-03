# THREATS.md — TrustVault Security Threat Model & Defense Ledger

> **Evaluation Philosophy:**  
> *"Alongside the system, you hand in THREATS.md: the ways you believe this could be broken, what you did about each one, and which ones you knowingly accepted and why. Be honest in it. An entry saying 'I know this is weak and here is why I left it' is worth marks. Pretending the hole is not there is worth none."*

---

## 1. Threat Modeling Overview

TrustVault was designed under the **Zero Trust Architecture (ZTA)** paradigm (NIST SP 800-207). We assume the network is hostile, client-side controls are untrusted, attackers can craft arbitrary HTTP requests, and authorized users may turn rogue or probe boundaries.

Every asset (binary file payload, document metadata, audit record, permission grant) is guarded behind explicit server-side decision points.

---

## 2. Threat Catalog & Mitigation Matrix

### Threat 01: Broken Object Level Authorization (BOLA / IDOR) on Document Download
- **OWASP Category:** API1:2023 Broken Object Level Authorization
- **Attack Vector:** An authenticated attacker (e.g. `bob_owner`) inspects browser traffic, observes `GET /documents/1/download`, and manually invokes `GET /documents/2/download` (or iterates IDs from 1 to 10,000) using `curl` or Burp Suite to access unauthorized documents.
- **Mitigation Implemented:**  
  In [`services/document_service.py`](file:///C:/Users/Swetha/Trustvault/services/document_service.py#L110-L135), the download handler executes `check_document_access(user, doc_id, 'read')` on the server before transmitting any file bytes. The check performs a live SQL query verifying either document ownership or an explicit grant in `document_permissions`. If unauthorized, the request is aborted with `HTTP 403 Forbidden` and the incident is appended to the audit ledger.
- **Automated Test:** [`tests/test_permissions.py::TestPermissionsAndIsolation::test_cross_user_download_idor_blocked`](file:///C:/Users/Swetha/Trustvault/tests/test_permissions.py#L26-L35)
- **Accepted / Residual Risk:** Sequential integer IDs (`1, 2, 3...`) could allow an attacker to infer total document volume via 403 vs 404 responses.  
  *Justification:* Mitigated in production by rate-limiting repeated 403s; moving to UUID primary keys was deferred to preserve developer schema readability for a 1-week evaluation.

---

### Threat 02: Direct Web Root Storage Traversal & URL Guessing
- **OWASP Category:** A01:2021 Broken Access Control / Insecure Direct Object Access
- **Attack Vector:** An attacker discovers or guesses direct storage URLs such as `https://app.trustvault.com/static/uploads/salary.pdf` or brute-forces filenames stored on the web server.
- **Mitigation Implemented:**  
  1. Files are stored **strictly outside the public web root** in `vault_storage/`.
  2. Physical files are never stored under their user-supplied names. Each file is assigned a randomized cryptographically secure UUID (`<uuid4>.bin`).
  3. No web server rule (Nginx/Flask) maps static routes to the storage directory. The ONLY path to retrieve bytes is via the authenticated streaming gateway [`stream_document_content()`](file:///C:/Users/Swetha/Trustvault/services/document_service.py#L110-L150).
- **Automated Test:** [`tests/test_upload_security.py::TestUploadSecurity::test_path_traversal_filename_sanitized`](file:///C:/Users/Swetha/Trustvault/tests/test_upload_security.py#L55-L75)
- **Accepted / Residual Risk:** None. The filesystem location is completely decoupled from web routing.

---

### Threat 03: Delayed Revocation Window (Token Caching / Zombie Grants)
- **OWASP Category:** A07:2021 Identification and Authentication Failures / Stale Authorization
- **Attack Vector:** An employee or contractor is granted access. The owner clicks "Revoke". The employee continues downloading files using an unexpired JWT or cached authorization session.
- **Mitigation Implemented:**  
  TrustVault does **not** embed document permissions inside client-side JWT claims or long-lived authorization caches. Every single read, edit, or download request performs a real-time database query against `document_permissions`. When an owner revokes a permission, the database row is deleted immediately with `db.session.commit()`. Sub-millisecond revocation is guaranteed.
- **Automated Test:** [`tests/test_revocation.py::TestInstantRevocation::test_instant_revocation_lifecycle`](file:///C:/Users/Swetha/Trustvault/tests/test_revocation.py#L23-L65)
- **Accepted / Residual Risk:** High query volume under extreme concurrent load (10,000 req/sec).  
  *Justification:* A Redis cluster with pub/sub invalidation was omitted for this 7-day sprint to keep the architecture self-contained without external daemon dependencies.

---

### Threat 04: Audit Trail Tampering & Repudiation
- **OWASP Category:** A09:2021 Security Logging and Monitoring Failures
- **Attack Vector:** An insider, compromised administrator account, or SQL injection attacker modifies or deletes entries in the `audit_logs` table to hide unauthorized document downloads.
- **Mitigation Implemented:**  
  1. **Append-Only Code Design:** No `UPDATE` or `DELETE` endpoints, methods, or ORM triggers exist for `AuditLog` anywhere in the codebase.
  2. **Cryptographic Hash Chaining (Blockchain-lite):** Each audit record signs its contents (`id`, `user_id`, `doc_id`, `action`, `status`, `timestamp`) concatenated with the `record_hash` of the preceding record using SHA-256.
  3. **Integrity Verifier:** [`verify_chain_integrity()`](file:///C:/Users/Swetha/Trustvault/services/audit_service.py#L82-L130) verifies both backward links and content hashes. Any out-of-band database edit breaks the chain and triggers immediate administrator alerts.
- **Automated Test:** [`tests/test_audit.py::TestAuditTrailAndTamperEvidence::test_tamper_detection_in_cryptographic_ledger`](file:///C:/Users/Swetha/Trustvault/tests/test_audit.py#L46-L80)
- **Accepted / Residual Risk:** A rogue database superuser (`postgres` / `root`) with direct shell access could theoretically recalculate hashes across all subsequent rows.  
  *Justification:* Complete mitigation requires shipping audit streams to an immutable external WORM (Write Once, Read Many) cloud bucket (e.g. AWS S3 Object Lock) or a dedicated SIEM (Datadog/Splunk), which was outside the self-contained deployment scope.

---

### Threat 05: Privilege Escalation via Permission Delegation API
- **OWASP Category:** API5:2023 Broken Function Level Authorization
- **Attack Vector:** A user with `viewer` or `read` permission sends a crafted `POST /documents/1/permissions/grant` payload to elevate their own access to `edit` or share the document with an accomplice.
- **Mitigation Implemented:**  
  [`services/permission_service.py::grant_permission()`](file:///C:/Users/Swetha/Trustvault/services/permission_service.py#L52-L95) enforces that `granter` must satisfy `required_permission='manage'` (strictly the document owner or system admin). Viewers attempting to grant permissions are rejected with 403, and the event is logged as an unauthorized probe.
- **Automated Test:** [`tests/test_permissions.py::TestPermissionsAndIsolation::test_read_grantee_cannot_edit_document`](file:///C:/Users/Swetha/Trustvault/tests/test_permissions.py#L55-L68)
- **Accepted / Residual Risk:** None. Function-level authorization checks are strictly enforced.

---

### Threat 06: Malicious File Upload (Extension Spoofing & Stored XSS)
- **OWASP Category:** A03:2021 Injection / Malicious File Upload
- **Attack Vector:** An attacker renames a malicious Windows executable (`exploit.exe`) or shell script (`script.sh`) to `report.pdf`, or uploads an SVG file containing `<script>alert(document.cookie)</script>` to steal administrator session cookies upon viewing.
- **Mitigation Implemented:**  
  1. Strict extension whitelisting (`.pdf`, `.docx`, `.xlsx`, `.txt`, `.png`, `.jpg`, `.jpeg`, `.csv`).
  2. **Magic Byte Sniffing:** [`services/document_service.py::validate_uploaded_file()`](file:///C:/Users/Swetha/Trustvault/services/document_service.py#L18-L65) verifies that files declaring `.pdf` begin with `%PDF-`, PNGs begin with `\x89PNG`, and Word/Excel files begin with `PK\x03\x04`.
  3. SVG files are strictly prohibited.
  4. Downloads are served with `Content-Disposition: attachment; filename="..."` and `X-Content-Type-Options: nosniff` so browsers download rather than execute files inline.
- **Automated Test:** [`tests/test_upload_security.py::TestUploadSecurity::test_extension_spoofing_blocked_by_magic_bytes`](file:///C:/Users/Swetha/Trustvault/tests/test_upload_security.py#L26-L45)
- **Accepted / Residual Risk:** Deep macro inspection inside `.docx` or `.xlsx` files is not performed.  
  *Justification:* Running a sandboxed virus scanner (e.g. ClamAV daemon) requires significant infrastructure overhead not suited for a minimal single-command deployment.

---

### Threat 07: Metadata Leakage via Global Search
- **OWASP Category:** A01:2021 Broken Access Control / Information Disclosure
- **Attack Vector:** A viewer searches for "Salary" or "Acquisition". Even if they cannot download the file, a poorly written search query might return document titles, owner names, or snippets, revealing confidential business activities.
- **Mitigation Implemented:**  
  The search route in [`routes/search_routes.py`](file:///C:/Users/Swetha/Trustvault/routes/search_routes.py#L22-L35) does not query `Document.query` directly. Instead, it queries [`get_accessible_documents_query(user)`](file:///C:/Users/Swetha/Trustvault/services/permission_service.py#L135-L160), which enforces a SQL `WHERE` filter:  
  `WHERE owner_id = :user_id OR id IN (SELECT document_id FROM document_permissions WHERE user_id = :user_id)`.  
  Documents not granted to the user are completely invisible in search results.
- **Automated Test:** Covered by permission isolation queries.
- **Accepted / Residual Risk:** Document titles owned by the user are visible to the user (intended behavior).

---

### Threat 08: Denial of Service via Massive File Uploads (Disk / Memory Exhaustion)
- **OWASP Category:** A05:2021 Security Misconfiguration / Resource Exhaustion
- **Attack Vector:** An attacker floods the upload endpoint with hundreds of 500MB video files or zip bombs to fill server storage and crash the service.
- **Mitigation Implemented:**  
  1. `MAX_CONTENT_LENGTH = 25 * 1024 * 1024` (25MB limit enforced at WSGI/Flask layer before body is buffered to disk).
  2. File streaming processes data in chunks.
  3. HTTP 413 "Request Entity Too Large" returned automatically.
- **Accepted / Residual Risk:** Multi-account spamming can still consume disk up to server storage capacity.  
  *Justification:* Implementing per-user disk quotas (e.g. 500MB total storage per user) was deferred to future releases.

---

## 3. Deliberately Omitted Features & Strategic Trade-Offs

1. **Folder-Level Inheritance:**  
   *Decision:* TrustVault deliberately uses **direct per-document grants** rather than recursive folder inheritance.  
   *Reasoning:* Folder inheritance is the #1 root cause of enterprise data leaks (*"I shared folder X so they could see file 1, and now they can see 40 confidential files"*). Explicit per-document grants eliminate transitive permission leaks.
2. **Stateless JWT Tokens with Embedded Permissions:**  
   *Decision:* TrustVault uses server-side authenticated sessions with real-time database validation.  
   *Reasoning:* Embedding permissions in JWTs makes immediate revocation mathematically impossible without complex distributed revocation blacklists.
3. **Public Sharing Links (Anonymous URLs):**  
   *Decision:* Prohibited by design.  
   *Reasoning:* A link that works without authentication cannot prove who downloaded the file afterwards, violating Non-Negotiable Rule #2.
