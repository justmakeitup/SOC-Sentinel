# Sentinel SOC Platform — Formal Threat Model

**Document Version:** 1.0.0  
**Framework Alignment:** STRIDE Threat Classification, NIST SP 800-61 Rev 2, OWASP Top 10  
**Target Application:** Sentinel — Security Monitoring & Incident Response Platform  

---

## 1. Executive Summary & Purpose

This threat model identifies high-value assets, threat actors, attack surfaces, and trust boundaries across the **Sentinel** security operations platform. Sentinel is designed to ingest raw telemetry, evaluate detection rules, generate alerts, manage incident cases, and export compliance reports. Because security monitoring tools are high-value targets for adversaries seeking to blind detection capabilities or tamper with evidence, defensive controls are implemented at each layer.

---

## 2. Primary Assets & Sensitivity Classification

| Asset Category | Data Elements | Impact of Compromise (C-I-A) | Security Controls Implemented |
| :--- | :--- | :--- | :--- |
| **Authentication & Credentials** | Passwords, JWT secret keys, HTTP session tokens | **Critical** (Loss of Confidentiality & Integrity) | Bcrypt (cost=12), HS256 HMAC JWT, `HttpOnly` + `SameSite=Lax` cookies, brute-force lockout (5 attempts $\rightarrow$ 15m lockout). |
| **Telemetry & Normalized Events** | Event timestamps, source/destination IPs, usernames, raw payloads | **High** (Integrity & Non-Repudiation) | SHA-256 cryptographic idempotency hashes (`event_hash`), credential scrubbing (`sanitize_raw_payload`), Pydantic schema validation. |
| **Detection Rules & Logic** | Rule thresholds, sliding time windows, MITRE techniques | **High** (Integrity & Availability) | RBAC restrictions (tuning restricted to Detection Engineers & Admins), parameter bounds validation, rule execution error isolation. |
| **Security Alerts & Evidence** | Triaged alerts, context data, entity bindings, supporting event IDs | **High** (Integrity & Confidentiality) | Deduplication keys preventing alert storms, strict state machine transitions (`new` $\rightarrow$ `triaged` $\rightarrow$ `escalated` / `resolved`). |
| **Incident Dossiers & Notes** | Containment actions, lessons learned, analyst notes, evidence linkage | **Critical** (Integrity & Confidentiality) | Strict RBAC (Tier 1 cannot close cases), transaction-wrapped status updates, foreign key referential integrity. |
| **Audit Ledger** | Historical actions, actor usernames, IP addresses, resource IDs | **Critical** (Non-Repudiation & Governance) | Dedicated `audit_events` ledger populated on all administrative and state-changing actions; no public endpoints permit mutation or deletion. |

---

## 3. Trust Boundaries & Attack Surfaces

```
                              TRUST BOUNDARY 1 (Public / Network Boundary)
      [ Untrusted Client / External Sensor ]
                        │
                        ▼ (HTTPS / TLS 1.3)
      [ Reverse Proxy / React Frontend (SPA) ]
                        │
                        ▼ TRUST BOUNDARY 2 (API Gateway & Ingestion Boundary)
      [ FastAPI Backend Application ]
         ├── SecurityHeadersMiddleware (nosniff, DENY, HSTS, XSS)
         ├── RequestSizeLimitMiddleware (10MB body limit)
         ├── Auth Dependency (JWT bearer / HttpOnly cookie)
         ├── RBAC Authorizer (Role-based access verification)
         └── Normalization & Sanitization Engine
                        │
                        ▼ TRUST BOUNDARY 3 (Internal Data Persistence Boundary)
      [ PostgreSQL / SQLAlchemy Database Engine ]
         ├── Normalized Events (dedup hash unique constraint)
         ├── Security Alerts & Incidents
         └── Immutable Audit Events Ledger
                        │
                        ▼ TRUST BOUNDARY 4 (Client-Side Export Boundary)
      [ Analyst Workstation Spreadsheet Application (Excel / Calc) ]
         └── CWE-1236 Formula Neutralization (Prepends `'` to trigger characters)
```

---

## 4. STRIDE Threat Analysis & Implemented Mitigations

### 4.1 Spoofing (Identity Impersonation)
- **Threat:** An adversary forges requests claiming to be an administrator or valid analyst to gain unauthorized access.
- **Implemented Mitigations:**
  - Standardized JWT sessions with cryptographic HS256 signing using server-side `SECRET_KEY`.
  - Passwords hashed using `bcrypt` (12 rounds) with salt; plaintexts never persisted.
  - Browser session tokens transmitted via `HttpOnly` and `SameSite=Lax` cookies, defending against token exfiltration via Cross-Site Scripting (XSS).
  - Brute-force account defense: 5 failed consecutive attempts triggers an automatic 15-minute account lock.

### 4.2 Tampering (Data Modification)
- **Threat 1: Ingestion Tampering:** Ingesting duplicate batches or altered timestamps to corrupt historical telemetry.
  - *Mitigation:* Cryptographic SHA-256 fingerprinting calculated over `(source_id + timestamp + raw_payload)`. Unique database constraint rejects duplicate batches idempotently without inflating metrics.
- **Threat 2: Detection Logic Tampering:** Modifying detection rule parameters to suppress legitimate alerts.
  - *Mitigation:* Role-Based Access Control (RBAC) restricts `PATCH /api/v1/rules/{id}` to `detection_engineer` and `admin` roles. Tier 1 analysts receive `HTTP 403 Forbidden`.
- **Threat 3: Audit Trail Modification:** Altering investigation notes or incident history to conceal analyst mistakes.
  - *Mitigation:* The `audit_events` table has no `UPDATE` or `DELETE` API endpoints. Incident timeline events are generated automatically during database transactions.

### 4.3 Repudiation (Denial of Actions)
- **Threat:** An analyst claims they did not close a critical alert, escalate a false-positive incident, or export sensitive data.
- **Implemented Mitigations:**
  - Automated audit instrumentation (`record_audit_event`) logs actor ID, actor username, actor IP address, action verb, resource type, resource ID, and ISO-8601 UTC timestamp.
  - All CSV export endpoints (`/api/v1/reports/export`) record an audit trail event documenting the export parameters and requesting analyst.

### 4.4 Information Disclosure (Data Leakage)
- **Threat 1: Credential Leakage in Telemetry:** Telemetry containing cleartext passwords or bearer tokens inadvertently indexed in search.
  - *Mitigation:* Ingestion normalizer applies `sanitize_raw_payload` and `sanitize_dict_fields`, regex-masking password fields (`password=***`, `"token": "***"`) before persistence.
- **Threat 2: Stack Trace & Environment Leakage:** Unhandled exceptions exposing SQL queries, library versions, or filesystem paths.
  - *Mitigation:* Global FastAPI exception handlers intercept `HTTPException`, `RequestValidationError`, and generic `Exception`, returning a uniform JSON envelope (`{"error": true, "status_code": ..., "detail": "..."}`).
- **Threat 3: Browser Cache & Sniffing:** Browsers caching sensitive incident dossiers.
  - *Mitigation:* `SecurityHeadersMiddleware` injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Permissions-Policy`.

### 4.5 Denial of Service (DoS & Resource Exhaustion)
- **Threat 1: Large Payload Memory Exhaustion:** Flooding ingestion endpoints with multi-gigabyte files to crash the backend process.
  - *Mitigation:* `RequestSizeLimitMiddleware` inspects `Content-Length` headers and stream size, immediately returning `HTTP 413 Content Too Large` if requests exceed 10MB.
- **Threat 2: Unbounded Batch Sizes:** Submitting millions of records in a single CSV/JSON payload.
  - *Mitigation:* `MAX_RECORDS_PER_IMPORT = 10000` enforced at the parser level.
- **Threat 3: Engine Pipeline Stalling:** A malformed rule or regex causing catastrophic backtracking (ReDoS).
  - *Mitigation:* Each detection rule executes within an isolated `try/except` boundary. Exceptions are captured in `engine.last_errors` without aborting evaluation for other active rules.

### 4.6 Elevation of Privilege
- **Threat 1: Self-Assigned Administrator Privileges:** A new user supplying `role="admin"` during self-registration.
  - *Mitigation:* Self-registration endpoint (`POST /api/v1/auth/register`) enforces `role = UserRole.ANALYST_TIER_1` regardless of client request parameters.
- **Threat 2: Analyst Modifying Incident Status:** A Tier-1 analyst prematurely resolving a SEV-1 incident.
  - *Mitigation:* Incident lifecycle state changes (`open` $\rightarrow$ `containment` $\rightarrow$ `resolved`) require `incident_responder`, `soc_manager`, or `admin` roles (`require_roles` dependency).

### 4.7 Spreadsheet Formula Injection (CWE-1236)
- **Threat:** An attacker inputs malicious strings (e.g. `=cmd|' /C calc'!A0` or `-2+3+cmd|...`) into usernames or log payloads. When an analyst exports a CSV report and opens it in Excel or LibreOffice, the application executes the formula.
- **Implemented Mitigation:**
  - [`sanitize_csv_cell`](file:///c:/Users/hp/Downloads/SOC%20Sentinel/backend/app/core/csv_exporter.py) evaluates every cell string. If the value begins with `=`, `+`, `-`, `@`, `\t`, or `\r`, an apostrophe (`'`) is prepended, neutralizing dynamic formula execution and rendering it as an inert string literal.

---

## 5. Residual Risks & Recommended Future Hardening

1. **Multi-Factor Authentication (MFA / WebAuthn):**
   - *Current State:* Schema contains `is_mfa_enabled` flag; password authentication is fully operational with bcrypt.
   - *Recommendation:* Implement TOTP (RFC 6238) or FIDO2/WebAuthn for administrative and responder accounts.
2. **Distributed Rate Limiting:**
   - *Current State:* Account-level lockout occurs after 5 failed attempts in the database.
   - *Recommendation:* Deploy a Redis token-bucket rate limiter at the reverse proxy layer to absorb Layer 7 volumetric HTTP floods.
3. **Database Field-Level Encryption:**
   - *Current State:* Data at rest relies on PostgreSQL disk-level encryption (TDE) or cloud volume encryption.
   - *Recommendation:* Introduce application-level AES-256-GCM encryption for investigation notes containing sensitive PII.
