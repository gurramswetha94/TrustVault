# TrustVault 🛡️ — Provable Document Security Platform

> **"A security fortress wearing the clothes of a CRUD application."**  
> TrustVault is built for high-stakes enterprise document sharing where the wrong person cannot reach a document through any route, and where you can mathematically prove exactly who reached it, including failed intrusion attempts.

---

## 1. Quick Start from a Clean Clone

TrustVault has zero external daemon requirements (runs self-contained with Python 3.10+):

```bash
# 1. Clone repository
git clone https://github.com/your-username/Trustvault.git
cd Trustvault

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed database with test accounts & sample confidential documents
python seed_data.py

# 4. Start TrustVault
python app.py
```
Open **`http://localhost:5000`** in your browser.

---

## 2. Seed Credentials for Evaluator Testing

The database seeder (`python seed_data.py`) creates accounts representing all 3 required roles. The login screen also features **one-click evaluator quick-fill buttons**:

| Role | Username | Password | Access Scope & Purpose |
|---|---|---|---|
| **Administrator** | `admin` | `Admin@TrustVault2026!` | Access to `/admin` audit console, cryptographic hash chain verification, security anomaly monitor. |
| **Document Owner #1** | `alice_owner` | `Alice@TrustVault2026!` | Owns Document #1 (Executive Salary Review) & #2 (MSA Contract). Can grant/revoke access. |
| **Document Owner #2** | `bob_owner` | `Bob@TrustVault2026!` | Owns Document #3 (Private Algorithm Blueprint) & #4 (Audit Filings). |
| **Viewer #1** | `carol_viewer` | `Carol@TrustVault2026!` | Explicit `read` grant on Alice's Salary document. Cannot edit, cannot delete, cannot re-share. |
| **Viewer #2 (Partner)** | `dave_external` | `Dave@TrustVault2026!` | Explicit `read` grant on Alice's MSA Contract. |

---

## 3. How TrustVault Meets the 3 Non-Negotiable Standards

### Standard 1: Server Decides Every Time (Zero Trust UI)
- Security is strictly decoupled from the UI. Hiding buttons does not count as security.
- Every endpoint in [`services/document_service.py`](file:///C:/Users/Swetha/Trustvault/services/document_service.py) queries [`check_document_access()`](file:///C:/Users/Swetha/Trustvault/services/permission_service.py) on the server before transmitting any file bytes.
- Direct attacks via `curl` with manipulated IDs (e.g., Bob trying to download Alice's salary slip) receive `HTTP 403 Forbidden`.

### Standard 2: Provable Audit Trail (Successes AND Denied Attempts)
- When a document leaks, leadership asks: *"Who opened this, and who tried to open this?"*
- TrustVault logs every upload, download, metadata view, edit, deletion, grant, and revocation.
- **Denied Attempts Are Logged:** Unauthorized probes (HTTP 403) are permanently recorded in [`audit_logs`](file:///C:/Users/Swetha/Trustvault/models.py) with client IP and reason.
- **Cryptographic Tamper-Evidence:** Each record signs its contents concatenated with the prior record's hash (`SHA-256` hash chaining). An altered or deleted row breaks the chain and triggers immediate administrator alerts.

### Standard 3: Instant Revocation (Zero Latency Kill Switch)
- Taking access away works **immediately**.
- TrustVault rejects client-side permission caching in JWTs. Access is checked against live database state on every request.
- When an owner revokes permission, the next request from that user fails with 403 in sub-millisecond time.

---

## 4. Running Automated Tests

Run the complete test suite verifying cross-user isolation, revocation, upload validation, and audit tamper detection:

```bash
python -m unittest discover tests
```

### The Tear-Down / Interview Question Test:
Run the test that specifically verifies the authorization decision in [`services/document_service.py::stream_document_content()`](file:///C:/Users/Swetha/Trustvault/services/document_service.py#L110-L140):

```bash
python -m unittest tests/test_tear_down.py
```
> If the authorization check in `stream_document_content()` were removed or bypassed, this test suite immediately fails with a red assertion error.

---

## 5. Architectural Write-Up

### What We Built
1. **Role-Based & Discretionary Access Control (RBAC + DAC):** 3 core roles (`admin`, `owner`, `viewer`) paired with explicit per-document named grants (`read`, `edit`), plus **Time-Bound Self-Revoking Grants** (`1 hr`, `24 hrs`, `7 days`, `30 days`) to eliminate stale access.
2. **Isolated Vault Storage:** Files are stored outside the web root under randomized UUIDs (`vault_storage/<uuid>.bin`). No direct URL path exists to bypass the server.
3. **Deep File Validation:** Magic byte sniffing (verifying `%PDF-`, `\x89PNG`, `PK\x03\x04`), extension whitelisting, filename sanitization, and a 25MB ceiling.
4. **Tamper-Evident Audit Ledger:** Append-only SHA-256 hash chaining with automated integrity verification.
5. **Zero Metadata Leakage Search:** Search queries are bounded strictly to documents the caller is authorized to view.
6. **Administrator Anomaly Console:** Live visibility into refused access probes and ledger integrity.

### What We Deliberately Omitted & Why
1. **Recursive Folder Inheritance:** Deliberately omitted. Folder inheritance is the leading cause of enterprise leaks (*"I shared folder A so they could see file 1, and now they see 40 confidential files"*). Explicit per-document grants eliminate transitive leaks.
2. **Stateless JWT Permission Claims:** Deliberately omitted. Embedding permissions in client tokens introduces a 15–60 minute delay before revocation takes effect, violating Non-Negotiable Rule #3.
3. **Public / Anonymous Share Links:** Deliberately omitted. Anonymous links make non-repudiation impossible because the server cannot prove who downloaded the file.

### How We Used AI & Where It Was Confidently Wrong
AI was utilized to accelerate boilerplate scaffolding, but was **strictly monitored and corrected at every security boundary**:
- **Critical Catch #1 (BOLA/IDOR):** The AI generated a download controller that checked `@login_required` but omitted authorization, allowing any user to download other users' files. We rewrote it to enforce `check_document_access()`.
- **Critical Catch #2 (Delayed Revocation):** The AI proposed embedding document permissions into a 1-hour JWT. We rejected this design in favor of real-time database validation to guarantee instant revocation.
- **Critical Catch #3 (Missing Denied Audits):** The AI only logged successful 200 OK operations. We updated the logger to record 403 denied attempts and added SHA-256 hash chaining.
*(Full detailed prompts and commit links are documented in [PROMPTS.md](file:///C:/Users/Swetha/Trustvault/PROMPTS.md)).*

### What is Unfinished / Future Roadmap
- **WORM Storage Integration:** Shipping audit hashes to AWS S3 Object Lock or a decentralized timestamping service for hardware-enforced immutability.
- **Client-Side End-to-End Encryption (E2EE):** Encrypting document bytes in the browser using WebCrypto AES-GCM before transmission so even the database administrator cannot read file contents without the user's private key.

---




