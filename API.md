# API.md — TrustVault Endpoint & Authorization Specification

> **Specification Standard:**  
> Every endpoint in TrustVault is documented below with its required authentication level, permitted roles, and permission gates.

---

## 1. Authentication & Session Management

| Endpoint | Method | Required Auth | Permitted Roles | Description |
|---|---|---|---|---|
| `/login` | `GET` | Anonymous | Anyone | Renders login page with evaluator seed credentials. |
| `/login` | `POST` | Anonymous | Anyone | Authenticates username/email & password against Bcrypt hash. Returns session cookie. |
| `/logout` | `GET`, `POST` | Authenticated | Any logged-in role | Terminates active session; appends `LOGOUT` to audit ledger. |
| `/api/me` | `GET` | Authenticated | Any logged-in role | Returns JSON identity payload for the calling session. |

---

## 2. Document Operations

| Endpoint | Method | Required Auth | Permitted Roles & Grants | Description |
|---|---|---|---|---|
| `/` or `/dashboard` | `GET` | Authenticated | Any role (`admin`, `owner`, `viewer`) | Returns documents accessible to caller (owned + explicitly shared). Zero metadata leakage. |
| `/documents/upload` | `POST` | Authenticated | `owner`, `admin` only | Validates magic bytes, sanitizes filename, stores with UUID in vault storage, logs `UPLOAD`. |
| `/documents/<id>` | `GET` | Authenticated | Document Owner OR caller with `read`/`edit` grant OR `admin` | Returns document metadata. If caller is owner/admin, includes permission delegation panel & audit trail. If unauthorized, returns `403` and logs denied attempt. |
| `/documents/<id>/download` | `GET` | Authenticated | Document Owner OR caller with explicit `read`/`edit` grant | **Critical Authorization Gateway:** Validates permission in real-time. Returns file stream with `Content-Disposition: attachment`. If unauthorized, returns `403` and logs denied probe. |
| `/documents/<id>/edit` | `POST` | Authenticated | Document Owner OR caller with explicit `edit` grant | Updates document title, description, or category. Returns `403` for read-only callers. |
| `/documents/<id>/delete` | `POST` | Authenticated | Document Owner OR `admin` | Permanently destroys document record and deletes binary payload from vault storage. Returns `403` for non-owners. |

---

## 3. Permission Delegation & Revocation

| Endpoint | Method | Required Auth | Permitted Roles & Grants | Description |
|---|---|---|---|---|
| `/documents/<id>/permissions/grant` | `POST` | Authenticated | Document Owner OR `admin` | Grants `read` or `edit` permission to a named user. Logs `GRANT_PERMISSION`. Viewers calling this receive `403`. |
| `/documents/<id>/permissions/revoke/<user_id>` | `POST` | Authenticated | Document Owner OR `admin` | **Instant Revocation:** Deletes permission row immediately from database. Subsequent requests by revoked user fail with `403` instantly. |
| `/api/users/search` | `GET` | Authenticated | `owner`, `admin` | Returns user suggestions for permission delegation form. |

---

## 4. Search & Discovery

| Endpoint | Method | Required Auth | Permitted Roles & Grants | Description |
|---|---|---|---|---|
| `/search` | `GET` | Authenticated | Any role (`admin`, `owner`, `viewer`) | Multi-parameter search by keyword, owner, category, and date range. **Zero Metadata Leakage:** Filters results strictly to documents caller is authorized to view. |

---

## 5. Administrative Oversight & Governance

| Endpoint | Method | Required Auth | Permitted Roles | Description |
|---|---|---|---|---|
| `/admin` | `GET` | Authenticated | `admin` only | Comprehensive audit console showing complete activity stream, security anomaly flags (403 refused probes), and ledger integrity verification. Viewers and Owners receive `403`. |
| `/admin/verify-integrity` | `GET` | Authenticated | `admin` only | On-demand cryptographic verification of the SHA-256 audit hash chain. Returns `SECURE` (100% intact) or `COMPROMISED`. |
