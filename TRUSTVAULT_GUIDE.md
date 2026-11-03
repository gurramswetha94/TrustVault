# TrustVault: The Plain-English Master Guide & Attack Defense Blueprint

> **"This is a security problem wearing the clothes of a CRUD application."**  
> — *The core philosophy of the TrustVault evaluation.*

---

## 1. What TrustVault Actually Is (In Plain English)

On the surface, TrustVault looks like a simplified Dropbox or Google Drive:
- Users log in.
- Users upload files (PDFs, contracts, payroll records).
- Owners share files with specific colleagues.
- Users search and download documents.

**Under the hood, it is completely different.**
In a regular CRUD app, if you accidentally leave an API open or if someone accesses a file link, people say "oops, a minor bug". In TrustVault, **that is an immediate failure**.

TrustVault is an **uncompromising digital vault & black-box recorder**:
1. **Zero Leaks:** A person who was not explicitly granted access cannot reach a file through *any route* (modifying URLs, guessing file paths, or calling endpoints directly).
2. **Mathematical Accountability:** You can prove from tamper-evident audit logs *who* accessed a document, *when*, and from what IP — and crucially, **every single denied attempt** when an unauthorized person tried to get in.
3. **Instant Kill Switch:** The millisecond an owner clicks "Revoke", that user's access stops *immediately*.

---

## 2. The 3 Non-Negotiable Rules

These three rules are strict. Violating any of them fails the core system:

| # | Non-Negotiable Rule | Why It Matters | The Fatal Trap to Avoid |
|---|---------------------|----------------|--------------------------|
| **1** | **Server-Side Decides Every Time** | Security cannot live in the frontend. Hiding a download button is cosmetic. | Checking `can_download` in React/Vue/HTML. A judge will use `curl` or Postman directly against `/api/documents/42/download`. The server must check the database before returning a single byte. |
| **2** | **Provable Audit Trail of All Attempts (Success & Refused)** | When a document leaks, leadership asks: *"Who opened this, and who tried to open this?"* | Only logging successful 200 OK downloads. If Alice tries to reach Bob's salary slip and receives HTTP 403 Forbidden, **that denied attempt must be permanently recorded** in `audit_logs`. |
| **3** | **Instant Revocation (Zero Latency Window)** | If someone is fired or a contract ends, their access must die that exact millisecond. | Using 1-hour JWT tokens that contain permissions in the payload. If you revoke access in the DB, a stateless JWT will still let them download for 59 minutes! You must check the DB on every single file fetch. |

---

## 3. The 10 Baseline Features Checklist

- [ ] **1. Authentication with 3 Roles:** Admin, Document Owner, Viewer.
- [ ] **2. Document Management:** Upload, organise, view, search, and manage files.
- [ ] **3. Granular Permissions:** Read and Edit permissions granted to specific named users.
- [ ] **4. Owner Delegation:** Owners can grant access to named users and take it back at will.
- [ ] **5. Strict Access Walls:** Unauthorized users cannot read, download, change, or delete a document.
- [ ] **6. Comprehensive Audit Trail:** Permanent logging of uploads, downloads, changes, deletions, permission changes, and **refused attempts**.
- [ ] **7. Multi-Parameter Search:** Search by document name, owner, category, and date range.
- [ ] **8. Strict Upload Validation:** Magic bytes inspection, size limits, and filename sanitization.
- [ ] **9. Administrative Oversight View:** Admin dashboard showing document activity, permission modifications, and security anomalies.
- [ ] **10. Automated Security Tests:** Automated test suite proving that one user cannot reach another user's documents.

---

## 4. The 100-Point Marking Rubric

| Marks | Band | Evaluator's Focus | How to Guarantee Full Marks |
|:---:|:---|:---|:---|
| **35** | **Security** | A judge will actively attack your live deployed system. | Block every BOLA/IDOR attempt, hide static storage paths, ensure instant revocation. |
| **15** | **Threat Thinking** | Your `THREATS.md` vs. the judges' master threat list. | Document 8–12 threats honestly. Explain how you mitigated each, and defend accepted trade-offs. |
| **15** | **Core Functionality** | The 10 required features operating end-to-end. | Clean, functional UI and REST API. |
| **15** | **AI Directing (PROMPTS.md)** | At least 5 dated entries showing you catching AI errors. | Show where AI suggested insecure code (e.g., missing auth checks) and how you caught and fixed it. |
| **10** | **Engineering Quality** | Code readability, architecture, and defensive design. | Clean modular structure, parameterized queries, robust error handling. |
| **10** | **Documentation & Demo** | README, seed credentials, clean clone deploy, 5-min demo video. | Single setup command, clear 5-minute video walkthrough. |

> **Warning:** *"One document reached by someone who should not have reached it costs most of the first band (35 marks), whatever else works."*

---

## 5. The Judges' Secret Attack Playbook

A judge will execute these 7 attacks against your deployed system:

### Attack 1: BOLA / IDOR (Insecure Direct Object Reference)
- **The Vector:** User Alice is granted Document 1. Alice inspects network traffic, sees `GET /api/documents/1/download`, and changes the URL to `GET /api/documents/2/download` (Bob's private document).
- **The Defense:** Query `DocumentPermission` joined with `current_user.id` on every single download. If no row exists, log a `DENIED` attempt and return `HTTP 403 Forbidden`.

### Attack 2: Direct Static Storage Guessing
- **The Vector:** Attacker guesses `https://your-domain.com/static/uploads/salary_bob.pdf` or views the direct S3 storage link.
- **The Defense:** Store files **outside the public web root** with randomized UUID filenames (e.g. `storage/vault/e4b2...bin`). Stream bytes exclusively through an authenticated API endpoint.

### Attack 3: Delayed Token Revocation
- **The Vector:** Charlie is granted access. The owner clicks "Revoke". Charlie immediately triggers a download using his existing token or session.
- **The Defense:** Never cache document permissions inside a stateless JWT. Query live database permission rows on every single download.

### Attack 4: Privilege Escalation on Permissions Endpoint
- **The Vector:** A Viewer sends `POST /api/documents/1/permissions` attempting to grant themselves `edit` access.
- **The Defense:** Verify that `current_user.id == document.owner_id` (or user is system admin) before executing any permission alteration.

### Attack 5: Malicious File Upload (XSS & Directory Traversal)
- **The Vector:** Attacker uploads `../../etc/passwd` or an SVG containing `<script>alert(1)</script>`.
- **The Defense:** Sanitize filenames, inspect magic bytes (verify PDF begins with `%PDF-`), store as UUIDs, and force download with `Content-Disposition: attachment`.

### Attack 6: Metadata Leakage via Global Search
- **The Vector:** Unauthorized user searches for "Acquisition" or observes 404 vs 403 status codes to deduce document existence.
- **The Defense:** The search SQL query must filter strictly by `WHERE user_id = current_user OR doc_id IN (permitted_docs)`.

### Attack 7: Audit Log Tampering
- **The Vector:** Attacker executes SQL injection or calls an admin endpoint to delete the log of their unauthorized access.
- **The Defense:** Parameterized queries, append-only `audit_logs` table, zero `DELETE` or `UPDATE` endpoints in the code.

---

## 6. What Makes a Winning `THREATS.md`

`THREATS.md` is submitted alongside your code. The judges have their own list of threats and will compare yours to theirs.

### The Key to Scoring 15/15:
- **Honesty:** Saying *"I know this system is vulnerable to memory-exhaustion DoS if a user uploads ten 25MB files simultaneously; I accepted this risk for a 7-day prototype and enforced a 25MB file ceiling"* is worth full marks. Pretending there are no flaws gets zero.
- **Structure for Each Entry:**
  1. **Threat Title & OWASP Category**
  2. **Attack Vector (Exact HTTP request / route)**
  3. **Mitigation Implemented (Exact code and logic)**
  4. **Automated Test Proving It Works (Test function name)**
  5. **Residual / Accepted Risk & Justification**

---

## 7. What Makes a Winning `PROMPTS.md`

`PROMPTS.md` proves that you directed the AI and understood security better than the LLM.

### Non-Negotiable Requirements:
1. **At least 5 dated entries** created across the week (not written all on the final day).
2. **At least 2 entries specifically about Authorization, Access Control, or the Audit Trail.**
3. **Mandatory 4-Part Structure for each entry:**
   - **What you asked the tool to do:** (The prompt)
   - **What it produced:** (The AI's code/output)
   - **What was wrong with it specifically:** (The security flaw you caught)
   - **What you did instead:** (Your fixed code + Git commit link)

---

## 8. The Technical Interview: The "One Question"

Shortlisted candidates walk through their code live. The interviewer will ask:

> **"Show me where the authorization decision is made when someone downloads a file. What would happen if that line were removed?"**

### How to Ace This Question:
1. **Immediate Precision:** Jump directly to `services/auth_service.py` -> `can_access_document()`.
2. **Explain the Failure Mode:** *"If this line is removed, the check passes by default and an unauthorized user receives the file stream."*
3. **The Proof:** *"However, our automated test suite has `test_unauthorized_download_denied()`. If we comment out this check right now and run `pytest`, the test fails immediately with an assertion error expecting 403 but getting 200."*
4. **Demonstrate:** Comment out the check live and run the tests. The red failure proves your test suite is genuine.

---

## 9. 7-Day Execution Blueprint

```
Day 1: Setup database schema, Bcrypt authentication, 3 roles, initial git commits.
Day 2: File upload validation (magic bytes), UUID storage, safe streaming endpoint.
Day 3: Granular permissions table, Grant/Revoke API, instant revocation (zero caching).
Day 4: Append-only audit logging (including HTTP 403 denied attempts) & Admin UI.
Day 5: Comprehensive security test suite (IDOR, path traversal, revocation tests).
Day 6: Deploy early to Render/Railway; verify live URL; write THREATS.md & PROMPTS.md.
Day 7: Record 5-minute video demo, verify seed credentials in README, final tag.
```

---

## 10. Deliverables Checklist

- [ ] **Public Git Repository:** Commits distributed across the week.
- [ ] **Live Working URL:** Seed data loaded and accessible online.
- [ ] **README.md:** Seed credentials for Admin, Document Owner, and Viewer.
- [ ] **THREATS.md:** 8–12 documented threats, mitigations, and accepted risks.
- [ ] **PROMPTS.md:** 5+ dated entries (2+ on auth/audit) with commit hashes.
- [ ] **Automated Tests:** Comprehensive unit & integration tests covering permission isolation.
- [ ] **Database Schema & Setup Script:** Single command initialization.
- [ ] **API Documentation:** Endpoint list with required roles/permissions.
- [ ] **5-Minute Demo Video:** Walkthrough of upload, sharing, denial, and audit logging.
- [ ] **Short Architecture Write-up:** Design decisions, omitted features, and model explanation.

---

*A printable, high-resolution PDF version of this guide is available at:*  
**`c:\Users\Swetha\Trustvault\TrustVault_Executive_Guide.pdf`**

