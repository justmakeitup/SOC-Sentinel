# Sentinel — Security Monitoring & Incident Response Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791.svg)](https://www.postgresql.org/)
[![Alembic](https://img.shields.io/badge/Alembic-Migrations-red.svg)](https://alembic.sqlalchemy.org/)
[![Pytest](https://img.shields.io/badge/Pytest-85%20Passed-brightgreen.svg)](https://docs.pytest.org/)
[![Vitest](https://img.shields.io/badge/Vitest-11%20Passed-green.svg)](https://vitest.dev/)
[![Ruff](https://img.shields.io/badge/Code%20Style-Ruff%20Clean-black.svg)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

Sentinel is a full-stack **Security Operations Center (SOC) platform** engineered for real-time telemetry ingestion, correlation-based detection engineering, alert triage deduplication, and NIST SP 800-61 Rev 2 incident response case management.

Built with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, **Alembic**, and **React (TypeScript + Vite)**, Sentinel provides an end-to-end operational platform for security teams to ingest heterogeneous telemetry, evaluate sliding-window behavioral detection rules, investigate security incidents, and generate formula-safe compliance reports.

---

## Table of Contents

- [Architectural Overview](#architectural-overview)
- [Technology Stack](#technology-stack)
- [Project Directory Structure](#project-directory-structure)
- [Core Subsystems](#core-subsystems)
- [Prerequisites & Installation](#prerequisites--installation)
- [Database Initialization & Migrations](#database-initialization--migrations)
- [Repeatable Demo Dataset & Seeding](#repeatable-demo-dataset--seeding)
- [Testing & Quality Verification](#testing--quality-verification)
- [Complete API Endpoint Reference](#complete-api-endpoint-reference)
- [End-to-End Analyst Workflow](#end-to-end-analyst-workflow)
- [Threat Model & Security Controls](#threat-model--security-controls)
- [Deployment Specifications](#deployment-specifications)
- [Known Limitations & Future Roadmap](#known-limitations--future-roadmap)

---

## Architectural Overview

```
                                      +---------------------------------------------+
                                      |            Browser / Analyst Client         |
                                      |         React 19 + TypeScript + Vite        |
                                      |     Dark Charcoal UI + SVG Telemetry Charts |
                                      +----------------------+----------------------+
                                                             |
                                           HTTPS / JSON REST | HttpOnly Session Cookies
                                           CORS Whitelisted  | JWT Bearer Authorization
                                                             |
                                                             v
+-------------------------------------------------------------------------------------------------------------------------+
|                                                   FastAPI Backend Service                                               |
|                                                                                                                         |
|  +---------------------------+   +---------------------------+   +---------------------------+   +-------------------+  |
|  |  Defensive Middleware     |   |   Authentication & RBAC   |   |   Telemetry Ingestion     |   | Detection Engine  |  |
|  |  • nosniff, DENY, HSTS    |   |   • Bcrypt password hash  |   |   • Multi-format parsers  |   | • Sliding windows |  |
|  |  • 10MB payload ceiling   |   |   • 5-Tier RBAC roles     |   |   • Sensitive data scrub  |   | • Rule registry   |  |
|  |  • Trace-free exceptions  |   |   • Brute-force lockout   |   |   • SHA-256 deduplication |   | • Storm cooldown  |  |
|  +-------------+-------------+   +-------------+-------------+   +-------------+-------------+   +---------+---------+  |
|                |                               |                               |                           |            |
|                +-------------------------------+-------------------------------+---------------------------+            |
|                                                                |                                                        |
|                                                                v                                                        |
|  +---------------------------+   +---------------------------+   +---------------------------+   +-------------------+  |
|  |    Incident Management    |   |   Forensic Audit Trail    |   |   Operational Analytics   |   | Subsystem Health  |  |
|  |    • NIST SP 800-61 Rev 2 |   |   • Append-only ledger    |   |   • MTTR exact query      |   | • DB latency ping |  |
|  |    • Chronological notes  |   |   • Action non-repudiation|   |   • Daily bucket volume   |   | • Component check |  |
|  |    • Evidence chaining    |   |   • Structured metadata   |   |   • CWE-1236 CSV safety   |   | • Graceful degrade|  |
|  +---------------------------+   +---------------------------+   +---------------------------+   +-------------------+  |
|                                                                |                                                        |
|                                              SQLAlchemy 2.0 ORM Engine & Alembic                                        |
+----------------------------------------------------------------+--------------------------------------------------------+
                                                                 |
                                                    Connection Pool (QueuePool)
                                                                 |
                                                                 v
+-------------------------------------------------------------------------------------------------------------------------+
|                                                  PostgreSQL 15+ Database                                                |
|                                                                                                                         |
|  • users & user_roles                 • detection_rules (MITRE ATT&CK)     • investigation_notes (Analysis/Evidence)   |
|  • log_sources & ingestion_jobs       • security_alerts (Deduplication)     • audit_events (Immutable non-repudiation)  |
|  • normalized_security_events (ECS)   • incidents (NIST SP 800-61 phases)  • alembic_version (Schema revisions)        |
+-------------------------------------------------------------------------------------------------------------------------+
```

---

## Technology Stack

| Layer | Component | Version | Role in Architecture |
| :--- | :--- | :--- | :--- |
| **Frontend** | React | 19.0 | Reactive component-based SOC analyst single-page interface |
| **Frontend** | TypeScript | 5.7 | Strict static typing mirroring backend schemas and API contracts |
| **Frontend** | Vite | 6.4 | High-performance build tool, dev server, and production bundler |
| **Frontend** | Tailwind CSS | 3.4 | Dark charcoal SOC design system with custom status tokens and accessibility |
| **Frontend** | Lucide React | 1.16 | Standardized iconography across navigation, severity badges, and actions |
| **Backend** | Python | 3.11 – 3.13 | Core runtime execution environment |
| **Backend** | FastAPI | 0.115+ | High-performance asynchronous REST API framework with automatic OpenAPI docs |
| **Backend** | Pydantic | 2.10+ | Strict request/response payload validation, schema serialization, and settings |
| **Backend** | SQLAlchemy | 2.0+ | Object Relational Mapper (ORM) with connection pooling and type hints |
| **Backend** | Alembic | 1.14+ | Declarative database migration engine for versioned schema evolution |
| **Backend** | Passlib & Bcrypt | 1.7+ | Industry-standard password hashing with individual salt rounds |
| **Backend** | PyJWT | 2.10+ | Cryptographic HS256 authentication tokens for session verification |
| **Database** | PostgreSQL | 15+ | Enterprise relational database for structured security telemetry and alerts |
| **Testing** | Pytest | 8.3+ | Backend automated unit, integration, and security test suite (85 tests) |
| **Testing** | Vitest & Testing Library | 3.2+ | Frontend unit and integration test suite with DOM simulation (11 tests) |
| **Linter** | Ruff | 0.8+ | Fast Python linter and formatter enforcing PEP 8 and import standards |

---

## Project Directory Structure

```
SOC Sentinel/
├── .gitignore                         # Excludes secrets, .env files, node_modules, .venv, caches
├── .env.example                       # Unified root environment template
├── README.md                          # Comprehensive project documentation
├── THREAT_MODEL.md                    # STRIDE threat model, assets, and implemented mitigations
├── DEPLOYMENT.md                      # Production deployment guide (Docker, Systemd, Nginx)
│
├── backend/                           # Python / FastAPI Backend Subsystem
│   ├── alembic/                       # Schema migration scripts
│   │   ├── versions/
│   │   │   ├── 0001_initial_schema.py # Initial DDL creating all 7 core domain tables & indexes
│   │   │   └── 0002_add_ingestion_rejected_records.py # Adds rejected_records column
│   │   ├── env.py                     # Alembic runner wired to SQLAlchemy Base
│   │   └── script.py.mako             # Revision template
│   ├── alembic.ini                    # Alembic CLI configuration (supports root & local paths)
│   ├── pyproject.toml                 # Ruff linter rules and Pytest configuration
│   ├── requirements.txt               # Production dependencies
│   ├── .env.example                   # Backend-specific environment template
│   │
│   ├── app/
│   │   ├── api/v1/                    # API Routing Layer
│   │   │   ├── endpoints/
│   │   │   │   ├── alerts.py          # Alert listing, evidence triage, status transitions
│   │   │   │   ├── audit.py           # Immutable audit ledger inspection
│   │   │   │   ├── auth.py            # Login, registration, token issuance, user provisioning
│   │   │   │   ├── dashboard.py       # Live summary aggregations (events, alerts, incidents)
│   │   │   │   ├── events.py          # Paginated normalized event querying and filters
│   │   │   │   ├── health.py          # Subsystem health check with database ping latency
│   │   │   │   ├── incidents.py       # NIST incident lifecycle, notes, timeline, alert linkage
│   │   │   │   ├── ingestion.py       # Multipart upload, parsing, validation, and error quarantine
│   │   │   │   ├── reports.py         # Telemetry aggregations, MTTR metrics, CSV/Markdown export
│   │   │   │   └── rules.py           # Detection rule tuning, status toggle, and dataset replay
│   │   │   └── router.py              # Aggregated v1 API router
│   │   │
│   │   ├── auth/                      # Authentication & Access Control
│   │   │   ├── dependencies.py        # get_current_user, require_roles (RBAC authorization)
│   │   │   └── token.py               # JWT creation, decoding, expiration validation
│   │   │
│   │   ├── core/                      # Platform Foundations
│   │   │   ├── csv_exporter.py        # RFC 4180 CSV builder + CWE-1236 formula sanitization
│   │   │   ├── logging.py             # Structured console logging
│   │   │   └── security.py            # Bcrypt password hashing and token generation
│   │   │
│   │   ├── engine/                    # Detection Engine Subsystem
│   │   │   ├── correlator.py          # Evaluation engine, sliding window tracking, cooldowns
│   │   │   ├── registry.py            # Extensible detection rule plugin registry
│   │   │   ├── base.py                # BaseDetectionRule abstract base class
│   │   │   ├── schemas.py             # Detection result and rule schemas
│   │   │   └── rules/                 # Built-in Detection Rules
│   │   │       ├── repeated_failed_logins.py # RULE-AUTH-001 (Threshold failed logins)
│   │   │       ├── login_after_failures.py   # RULE-AUTH-002 (Correlation success after fails)
│   │   │       ├── port_scan.py              # RULE-SCAN-001 (Multi-port sweep detection)
│   │   │       └── unusual_auth.py           # RULE-AUTH-003 (Off-hours / multi-IP velocity)
│   │   │
│   │   ├── ingestion/                 # Telemetry Normalization Subsystem
│   │   │   ├── normalizer.py          # ECS schema normalization & SHA-256 deduplication
│   │   │   ├── sanitizer.py           # Credential scrubbing (passwords, tokens masked)
│   │   │   └── parsers/               # Telemetry Parsers (CSV, JSON, Syslog, Zeek)
│   │   │
│   │   ├── models/                    # Declarative SQLAlchemy ORM Models
│   │   │   ├── alert.py               # SecurityAlert (deduplication key, context evidence)
│   │   │   ├── audit.py               # AuditEvent (immutable action trail)
│   │   │   ├── base.py                # Base, PrimaryKeyUUIDMixin, TimestampMixin
│   │   │   ├── event.py               # NormalizedSecurityEvent (SHA-256 event_hash)
│   │   │   ├── incident.py            # Incident, InvestigationNote (NIST phases)
│   │   │   ├── log_source.py          # LogSource, IngestionJob
│   │   │   ├── rule.py                # DetectionRule (MITRE ATT&CK mapping)
│   │   │   └── user.py                # User, UserRole (Bcrypt hash, lockout counter)
│   │   │
│   │   ├── schemas/                   # Pydantic Schemas for Validation
│   │   ├── services/                  # Business Logic Layer (Audit, Incident, Reports)
│   │   ├── config.py                  # Pydantic BaseSettings loading from .env
│   │   ├── database.py                # Engine, SessionLocal, get_db dependency
│   │   └── main.py                    # FastAPI entrypoint, defensive middleware, CORS
│   │
│   ├── scripts/
│   │   ├── seed_demo_data.py          # Comprehensive, idempotent data seeder
│   │   └── seed_users.py              # User-only provisioning script
│   │
│   └── tests/                         # Pytest Automated Test Suite (85 tests)
│
└── frontend/                          # React / TypeScript Frontend Subsystem
    ├── src/
    │   ├── api/                       # API Clients (Alerts, Dashboard, Events, Incidents, Reports)
    │   ├── components/
    │   │   ├── common/                # Reusable UI components (SeverityBadge, StatusBadge)
    │   │   ├── dashboard/             # Overview widgets (SummaryCard, EventVolumeChart)
    │   │   ├── incidents/             # Incident modals (CreateIncidentModal, IncidentDetailModal)
    │   │   ├── ingestion/             # Import modals (ImportLogModal)
    │   │   ├── layout/                # Shell, AppHeader, Sidebar, GlobalSearchModal
    │   │   └── views/                 # Full Page Modules
    │   │       ├── EventsView.tsx     # Telemetry exploration, search, raw JSON drawer
    │   │       ├── DetectionRulesView.tsx # Rule inspection, threshold tuning, replay
    │   │       ├── LogSourcesView.tsx # Log collectors, active sensors, ingestion jobs
    │   │       └── ReportsView.tsx    # Operational reports, MTTR, sanitized CSV exports
    │   ├── types/                     # TypeScript domain models mirroring backend schemas
    │   ├── __tests__/                 # Vitest test suite (11 tests)
    │   ├── App.tsx                    # Main application router and state coordinator
    │   └── main.tsx                   # React root entrypoint
    ├── vite.config.ts                 # Vite configuration
    └── package.json                   # Dependencies and scripts
```

---

## Core Subsystems

### 1. Ingestion & Normalization Subsystem
- **Supported Dialects**: Generic JSON events, Windows Security Event Logs (Event IDs 4624, 4625), Zeek network connection logs, and structured CSV with header mappings.
- **Credential Scrubbing**: Automatically detects and masks passwords, authorization headers, and secret keys using [`sanitizer.py`](file:///c:/Users/hp/Downloads/SOC%20Sentinel/backend/app/ingestion/sanitizer.py) prior to persistence.
- **Idempotency & Deduplication**: Calculates a cryptographic SHA-256 fingerprint:
  $$\text{event\_hash} = \text{SHA256}(\text{log\_source\_id} + \text{timestamp} + \text{raw\_payload})$$
  Enforces a `UNIQUE` database constraint, guaranteeing that repeated log uploads never inflate telemetry volume.
- **Error Quarantine**: Malformed rows are isolated into `ingestion_jobs.rejected_records` with line numbers and failure reasons rather than failing silently.

### 2. Correlation Detection Engine
- **Extensible Registry**: Detection rules are implemented as self-contained plugins implementing [`BaseDetectionRule`](file:///c:/Users/hp/Downloads/SOC%20Sentinel/backend/app/engine/base.py).
- **Built-in Rules**:
  - `RULE-AUTH-001` (Repeated Failed Logins): Flags $\ge 5$ failed attempts against an entity within a sliding 300s window.
  - `RULE-AUTH-002` (Login Following Failures): Correlates failed attempts followed by a successful authentication within 600s without assuming every sequence is malicious.
  - `RULE-SCAN-001` (Multi-Port Reconnaissance Sweep): Flags probes contacting $\ge 8$ distinct destination ports on a single host within 60s.
  - `RULE-AUTH-003` (Unusual Authentication Deviation): Flags off-hours administrative access or rapid multi-IP authentication velocity.
- **Alert Storm Mitigation**: Generates a composite deduplication key:
  $$\text{dedup\_key} = \text{rule\_code} : \text{entity\_ip} : \text{entity\_user} : \text{hour\_bucket}$$
  Repeated findings increment the existing alert's `event_count` and update evidence context rather than spawning alert fatigue.
- **Error Isolation**: Individual rule failures are logged in `engine.last_errors` without halting evaluation for remaining rules.

### 3. NIST SP 800-61 Rev 2 Incident Response Workflow
- **Lifecycle Phases**: `OPEN` $\rightarrow$ `INVESTIGATING` $\rightarrow$ `CONTAINMENT` $\rightarrow$ `ERADICATION` $\rightarrow$ `RECOVERY` $\rightarrow$ `RESOLVED` $\rightarrow$ `CLOSED`.
- **Evidence Preservation**: Resolving or containing an incident updates the lifecycle record without deleting linked alerts or underlying telemetry.
- **Chronological Notes**: Analysts document findings using classified note types (`analysis`, `containment_action`, `forensic_evidence`, `communication`).
- **Interactive Dossier Modal**: Analysts can inspect chained alerts, review forensic evidence, record notes, update containment narratives, and export the incident dossier.

### 4. Operational Reporting & Formula-Safe CSV Export
- **True Database Metrics**: Every metric derives from real database queries (`NormalizedSecurityEvent`, `SecurityAlert`, `Incident`).
- **Mean Time to Resolution (MTTR)**:
  $$\text{MTTR} = \frac{1}{N} \sum_{i=1}^{N} (\text{updated\_at}_i - \text{created\_at}_i) \quad \text{strictly for } \text{status} \in \{\text{RESOLVED}, \text{CLOSED}\}$$
  If $N = 0$, MTTR evaluates to `null` accompanied by an explicit sample size notice (`"0 resolved cases in period"`) rather than an invented benchmark.
- **CWE-1236 Defense**: Cells beginning with formula triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) are automatically prepended with an apostrophe (`'`), preventing Dynamic Data Exchange (DDE) and command execution when opened in Microsoft Excel or LibreOffice Calc.
- **Incident Dossier Markdown Export**: Exports complete NIST incident forensic dossiers including metadata, chained alerts, investigation notes, and evidence references.

### 5. Security & Access Control
- **5-Tier Role-Based Access Control (RBAC)**:
  - `admin`: Full administrative control, user provisioning, role customization.
  - `soc_manager`: Incident closure, escalation approvals, compliance reporting.
  - `detection_engineer`: Detection rule parameter tuning, sliding window adjustments, engine replay.
  - `incident_responder`: Incident escalation, containment execution, forensic notes.
  - `analyst_tier_1`: Alert triage, evidence inspection, telemetry search.
- **Authentication Defense**: Passwords hashed with `bcrypt` (12 rounds). Failed logins increment a lockout counter; 5 failed attempts locks the account for 15 minutes.
- **Defensive Headers**: Enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`.

---

## Prerequisites & Installation

### System Requirements
- **Python**: 3.11, 3.12, or 3.13
- **Node.js**: 20.x or 24.x LTS
- **PostgreSQL**: 15+ (or SQLite for isolated local testing)
- **Git**

### 1. Clone & Environment Configuration

```bash
git clone https://github.com/your-username/soc-sentinel.git
cd soc-sentinel

# Copy root environment template
cp .env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

---

## Database Initialization & Migrations

Sentinel uses **Alembic** for schema migrations.

```bash
# Run migrations from root workspace
backend\.venv\Scripts\alembic -c backend/alembic.ini upgrade head

# OR run from the backend directory
cd backend
alembic upgrade head
```

*Migrations applied:*
1. `0001_initial_schema`: Provisions all 7 domain tables (`users`, `log_sources`, `normalized_security_events`, `detection_rules`, `security_alerts`, `incidents`, `investigation_notes`, `audit_events`) with indexes and unique constraints.
2. `0002_add_ingestion_rejected_records`: Adds JSON error quarantine column to `ingestion_jobs`.

---

## Repeatable Demo Dataset & Seeding

Sentinel includes an idempotent data seeder that populates realistic demonstration accounts, heterogeneous log sensors, synthetic telemetry events, engine-evaluated alerts, and NIST incident investigation cases.

```bash
# Run seeder from root workspace
backend\.venv\Scripts\python backend/scripts/seed_demo_data.py

# Optional: Wipe and recreate schema cleanly
backend\.venv\Scripts\python backend/scripts/seed_demo_data.py --reset
```

### Demonstration Accounts & Default Credentials

| Username | Role | Assigned Responsibilities | Default Password |
| :--- | :--- | :--- | :--- |
| `admin` | `admin` | User management, security headers, system settings | `Sentinel@Demo2026!` |
| `lead_responder` | `incident_responder` | Incident lifecycle, containment, forensic notes | `Sentinel@Demo2026!` |
| `det_engineer` | `detection_engineer` | Detection rule tuning, threshold adjustment, replay | `Sentinel@Demo2026!` |
| `tier1_analyst` | `analyst_tier_1` | Alert triage queue, initial incident escalation | `Sentinel@Demo2026!` |
| `soc_manager` | `soc_manager` | Operational oversight, report sign-off, MTTR metrics | `Sentinel@Demo2026!` |

> [!NOTE]
> Passwords can be customized prior to seeding by setting environment variables (e.g. `INITIAL_ADMIN_PASSWORD=YourPassword`).

---

## Testing & Quality Verification

All features are covered by automated unit and integration tests.

### Backend Test Suite (Pytest)
```bash
backend\.venv\Scripts\pytest backend/tests -v
```
**Result:** **85 passed in 13.4s**
- `test_auth_and_security.py` (24 tests): Password complexity, JWT validation, cookie flags, brute-force lockout, RBAC restrictions, privilege escalation defense, sanitization.
- `test_detection_engine.py` (19 tests): Rules 1–4 true/false positives, sliding windows, deduplication, missing fields robustness, engine replay.
- `test_ingestion.py` (9 tests): CSV/JSON parsers, malformed record quarantine, 10MB upload ceiling, credential scrubbing.
- `test_incidents.py` (8 tests): NIST state machine, alert chaining, audit timeline, RBAC permissions.
- `test_reports.py` (12 tests): CWE-1236 formula sanitization, MTTR precision, date bounds, CSV streaming, Markdown dossier generation.
- `test_dashboard_api.py`, `test_health.py`, `test_models.py` (13 tests): Subsystem health, empty database handling, schema constraints.

### Backend Lint & Style Check (Ruff)
```bash
backend\.venv\Scripts\ruff check backend
```
**Result:** **All checks passed! (0 errors)**

### Frontend Test Suite (Vitest)
```bash
npm --prefix frontend run test
```
**Result:** **11 passed in 4.8s**
- Navigation between modules (Overview, Events, Alerts, Incidents, Log Sources, Detection Rules, Reports).
- Modal opening and lifecycle transitions.
- Offline banner and error retry behavior.
- Reports view metrics rendering, calculation rules toggle, and CSV export triggers.

### Frontend Production Build
```bash
npm --prefix frontend run build
```
**Result:** **Built in 2.9s** (`tsc` clean, Vite bundle generated with 0 errors).

---

## Complete API Endpoint Reference

All endpoints are prefixed with `/api/v1`. Interactive Swagger documentation is available at `http://localhost:8000/docs`.

### Authentication & RBAC (`/api/v1/auth`)
- `POST /auth/login`: Authenticates username/email and issues session cookie + JWT bearer token.
- `POST /auth/logout`: Clears session cookie and invalidates session.
- `GET /auth/me`: Returns current authenticated user profile and assigned role permissions.
- `POST /auth/register`: Public analyst self-registration (strictly enforced to `analyst_tier_1`).
- `GET /auth/users`: Lists provisioned users (requires `admin` role).
- `POST /auth/users`: Provisions custom user accounts and roles (requires `admin` role).

### Subsystem Health (`/api/v1/health`)
- `GET /health`: Comprehensive subsystem readiness probe inspecting database latency, detection engine state, and ingestion status.

### Dashboard Telemetry (`/api/v1/dashboard`)
- `GET /dashboard/summary`: High-level operational metrics (events processed, active alerts, open incidents, critical alert count, timeseries buckets, severity breakdown).

### Log Ingestion & Sensors (`/api/v1/ingestion` & `/api/v1/sources`)
- `POST /ingestion/import`: Multipart log upload accepting CSV, JSON, Syslog, or Zeek files. Validates schema and quarantines rejected records.
- `GET /sources`: Lists registered log sources and emitter sensors.
- `POST /sources`: Registers a new telemetry sensor.
- `GET /sources/jobs`: Lists historical ingestion jobs with error summaries.

### Detection Rules & Alerts (`/api/v1/rules` & `/api/v1/alerts`)
- `GET /rules`: Lists all registered detection rules with MITRE ATT&CK taxonomy tags.
- `PATCH /rules/{id}`: Tunes thresholds or evaluation time windows (requires `detection_engineer` or `admin`).
- `POST /rules/replay`: Replays historical telemetry through detection rules to evaluate coverage.
- `GET /alerts`: Paginated security alert queue with status and severity filters.
- `GET /alerts/{id}`: Full alert evidence detail with linked supporting event records.
- `PATCH /alerts/{id}/status`: Triages alert status (`triaged`, `investigating`, `closed_false_positive`).
- `POST /alerts/{id}/escalate`: Escalates an alert directly into a new NIST Incident case file.

### Incident Management (`/api/v1/incidents`)
- `GET /incidents`: Lists incidents with status, severity, and search filters.
- `POST /incidents`: Declares a new incident case file.
- `GET /incidents/{id}`: Complete incident dossier with chained alerts, notes, and chronological timeline.
- `PATCH /incidents/{id}`: Updates status, containment details, or lessons learned (requires `incident_responder`+).
- `POST /incidents/{id}/notes`: Adds an investigation note with forensic classification.
- `POST /incidents/{id}/alerts`: Chains additional alerts to an active incident.

### Operational Reports & Exports (`/api/v1/reports`)
- `GET /reports/summary`: Bounded operational telemetry, timeseries volume, rule attribution, and MTTR.
- `GET /reports/export`: Streaming CSV export for `summary`, `events`, `alerts`, or `incidents` with CWE-1236 formula sanitization.
- `GET /reports/incidents/{id}/export`: Exports a complete incident forensic dossier in structured Markdown.

### Audit Ledger (`/api/v1/audit`)
- `GET /audit`: Non-repudiation audit trail recording all administrative and state-changing actions (requires `admin` or `soc_manager`).

---

## End-to-End Analyst Workflow

Below is the standard analyst workflow supported by Sentinel:

```
[ Ingest Logs ] ──> [ Engine Detects ] ──> [ Alert Triage ] ──> [ Escalate Incident ] ──> [ Contain & Export ]
```

1. **Ingest Telemetry:**
   - Navigate to **Log Sources** or **Events**, click **Import Logs**, and upload a synthetic authentication or network log file (`.csv` or `.json`).
   - The ingestion pipeline scrubs credentials, validates schema, calculates SHA-256 deduplication hashes, and records ingestion metrics.
2. **Detection Evaluation:**
   - The correlation engine evaluates the newly ingested events against active detection rules (e.g. repeated failed logins or port sweeps).
   - Cooldown deduplication ensures repeated matches increment `event_count` on existing alerts instead of spamming duplicate notifications.
3. **Alert Triage:**
   - In **Alerts**, review the triage queue. Click an alert to inspect matched entities, affected IP addresses, usernames, and supporting raw event logs.
   - Update triage status or click **Escalate to Incident**.
4. **Incident Case Management:**
   - In **Incidents**, open the newly declared case.
   - Advance the incident lifecycle from `Open` $\rightarrow$ `Investigating` $\rightarrow$ `Containment`.
   - Add chronological investigation notes classifying actions as `Analysis`, `Containment Action`, or `Forensic Evidence`.
5. **Dossier Export & Operational Reporting:**
   - In the Incident Modal, click **Export Dossier** to download the complete forensic Markdown report.
   - In **Reports**, select a date window (`24h`, `7d`, `30d`), review daily telemetry trends and MTTR calculations, and export sanitized CSV reports.

---

## Threat Model & Security Controls

A formal STRIDE threat model is maintained in [`THREAT_MODEL.md`](file:///c:/Users/hp/Downloads/SOC%20Sentinel/THREAT_MODEL.md).

Key mitigations include:
- **CWE-1236 (Spreadsheet Formula Injection)**: Values beginning with `=`, `+`, `-`, `@`, `\t`, `\r` are prepended with an apostrophe (`'`).
- **CWE-307 (Brute-Force Authentication)**: Account lockout enforced after 5 failed login attempts.
- **CWE-284 (Improper Access Control)**: Backend RBAC dependency enforcement (`require_roles`).
- **CWE-400 (Resource Exhaustion)**: Request payload size ceiling enforced at 10MB via middleware.
- **CWE-532 (Sensitive Information in Logs)**: Automated credential masking for passwords and bearer tokens.

---

## Deployment Specifications

Complete bare-metal, systemd, and Docker Compose deployment instructions are provided in [`DEPLOYMENT.md`](file:///c:/Users/hp/Downloads/SOC%20Sentinel/DEPLOYMENT.md).

---

## Known Limitations & Future Roadmap

To maintain engineering transparency, the following design boundaries and future improvements are documented:

1. **Authentication:**
   - *Current:* Session-based JWT with secure HttpOnly cookies, bcrypt hashing, and brute-force lockout.
   - *Roadmap:* Integration with enterprise SSO (SAML 2.0 / OIDC) and hardware token WebAuthn/FIDO2 MFA.
2. **Real-Time Streaming:**
   - *Current:* High-frequency HTTP polling with reactive state management and graceful retry handling.
   - *Roadmap:* WebSocket / Server-Sent Events (SSE) streaming channel for instantaneous alert delivery.
3. **Database Scale:**
   - *Current:* PostgreSQL with B-tree indexes, UUID primary keys, and SHA-256 deduplication constraints.
   - *Roadmap:* TimescaleDB hypertable partitioning for petabyte-scale long-term historical telemetry archiving.
4. **Third-Party Integrations:**
   - *Current:* Standalone incident case management and sanitized file exports.
   - *Roadmap:* Webhook dispatchers for PagerDuty, Slack, and Jira Service Management.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
