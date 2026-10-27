# Sentinel — Security Monitoring & Incident Response Platform

Sentinel is a security operations center (SOC) platform designed for real-time telemetry ingestion, correlation-based detection engineering, alert triage, and incident response management aligned with the NIST SP 800-61 Rev 2 framework and MITRE ATT&CK taxonomy.

---

## Architecture Overview

```
                                +-----------------------------+
                                |      Browser / Client       |
                                |  React + TypeScript + Vite  |
                                +--------------+--------------+
                                               |
                                     HTTP / REST (JSON)
                                  CORS Enabled / API v1
                                               |
                                               v
+-----------------------------------------------------------------------------------------+
|                                    Sentinel Backend                                     |
|                                     FastAPI Service                                     |
|                                                                                         |
|   +-------------------+   +--------------------+   +-------------------+   +--------+   |
|   |   Log Ingestion   |   |  Detection Engine  |   | Alert Management  |   | Health |   |
|   |  Taxonomy Normal. |   | Sliding Windows    |   | Dedup & Triage    |   | Checks |   |
|   +---------+---------+   +---------+----------+   +---------+---------+   +----+---+   |
|             |                       |                        |                  |       |
|             +-----------------------+------------------------+------------------+       |
|                                     |                                                   |
|                        SQLAlchemy 2.0 ORM & Alembic                                     |
+-------------------------------------+---------------------------------------------------+
                                      |
                           PostgreSQL Connection Pool
                                      |
                                      v
+-----------------------------------------------------------------------------------------+
|                                  PostgreSQL Database                                    |
|                                                                                         |
|  - users & user_roles                 - security_alerts (dedup key)                     |
|  - log_sources & ingestion_jobs       - incidents & investigation_notes (NIST lifecycle)|
|  - normalized_security_events         - audit_events (SOC 2 non-repudiation)            |
|    (SHA-256 event fingerprinting)                                                       |
+-----------------------------------------------------------------------------------------+
```

---

## Directory & File Structure

```
SOC Sentinel/
├── backend/
│   ├── alembic/                      # Database migration scripts and version history
│   │   ├── versions/
│   │   │   └── 0001_initial_schema.py# Initial DDL creating all 7 domain tables and indexes
│   │   ├── env.py                    # Alembic migration runner wired to SQLAlchemy Base
│   │   └── script.py.mako            # Migration file template
│   ├── app/
│   │   ├── api/                      # Routing layer
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   └── health.py     # Health & subsystem readiness inspection endpoint
│   │   │   │   └── router.py         # v1 router aggregator
│   │   ├── core/
│   │   │   ├── logging.py            # Structured console logging configuration
│   │   │   └── security.py           # Cryptographic primitives and token helpers
│   │   ├── engine/                   # Detection engine (sliding window & threshold evaluator)
│   │   ├── ingestion/                # Telemetry parsers (Syslog, Windows Event Log, Zeek)
│   │   ├── models/                   # Declarative SQLAlchemy ORM models
│   │   │   ├── base.py               # Base class, UUIDv4 PK mixin, UTC timestamp mixin
│   │   │   ├── user.py               # User and RBAC definitions
│   │   │   ├── log_source.py         # LogSource and IngestionJob models
│   │   │   ├── event.py              # NormalizedSecurityEvent with SHA-256 deduplication
│   │   │   ├── rule.py               # DetectionRule mapped to MITRE ATT&CK
│   │   │   ├── alert.py              # SecurityAlert with deduplication keys
│   │   │   ├── incident.py           # Incident and InvestigationNote (NIST lifecycle)
│   │   │   └── audit.py              # AuditEvent compliance and governance ledger
│   │   ├── schemas/                  # Pydantic v2 validation models
│   │   │   ├── common.py             # HealthResponse, SubsystemHealth, Pagination
│   │   │   ├── user.py               # User validation schemas
│   │   │   ├── log_source.py         # LogSource & IngestionJob schemas
│   │   │   ├── event.py              # Normalized event schemas
│   │   │   ├── rule.py               # Detection rule schemas
│   │   │   ├── alert.py              # Alert schemas
│   │   │   ├── incident.py           # Incident and Note schemas
│   │   │   └── audit.py              # Audit schemas
│   │   ├── config.py                 # Pydantic Settings reading .env configurations
│   │   ├── database.py               # Engine, SessionLocal, and DB connectivity checks
│   │   └── main.py                   # FastAPI app entrypoint, CORS, exception handlers
│   ├── tests/
│   │   ├── conftest.py               # Pytest SQLite in-memory engine and client fixtures
│   │   ├── test_health.py            # API health checks & response schema validation
│   │   └── test_models.py            # Database constraints, relations, and deduplication
│   ├── alembic.ini                   # Alembic CLI configuration
│   ├── pyproject.toml                # Python project metadata, Ruff linter, and Pytest config
│   ├── requirements.txt              # Production and development dependencies
│   └── .env.example                  # Backend environment variable template
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts             # Configurable HTTP client with error handling
│   │   │   └── health.ts             # Health check API queries
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   └── StatusBadge.tsx   # High-contrast accessible operational status pill
│   │   │   └── layout/
│   │   │       ├── AppHeader.tsx     # SOC top bar, UTC clock, environment, API status
│   │   │       ├── Sidebar.tsx       # Module navigation reflecting Phase readiness
│   │   │       └── Shell.tsx         # Unified dashboard shell container
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript interfaces mirroring backend schemas
│   │   ├── __tests__/
│   │   │   ├── setup.ts              # Jest-DOM matchers setup
│   │   │   └── App.test.tsx          # Shell rendering and offline handling tests
│   │   ├── App.tsx                   # Main SOC overview dashboard & subsystem matrix
│   │   ├── main.tsx                  # React DOM root entrypoint
│   │   └── index.css                 # Dark charcoal theme styling & custom scrollbars
│   ├── index.html                    # Single-page HTML container
│   ├── package.json                  # NPM scripts and dependencies
│   ├── postcss.config.js             # PostCSS Tailwind plugins
│   ├── tailwind.config.js            # SOC color palette (deep charcoal, restrained teal)
│   ├── tsconfig.json                 # TypeScript compiler configuration
│   ├── vite.config.ts                # Vite bundler configuration
│   ├── vitest.config.ts              # Vitest test runner configuration
│   └── .env.example                  # Frontend environment variable template
├── .gitignore                        # Global ignore for secrets, caches, and node_modules
└── README.md                         # Documentation
```

---

## How Components Communicate

1. **Frontend to Backend**:
   - The React frontend uses `fetch` encapsulated within `src/api/client.ts`.
   - The target backend is resolved dynamically from `VITE_API_BASE_URL` (defaults to `http://localhost:8000`).
   - Cross-Origin Resource Sharing (CORS) is configured on FastAPI via `BACKEND_CORS_ORIGINS` to allow authorized frontend origins while blocking arbitrary origins.

2. **Backend to Database**:
   - FastAPI handlers utilize SQLAlchemy 2.0 ORM sessions injected via the `get_db()` dependency.
   - Connection pooling (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`) ensures resilience and connection freshness.
   - Migrations are managed declaratively using Alembic, ensuring schema changes are tracked and reversible.

3. **Subsystem Resilience**:
   - The health endpoint (`/api/v1/health`) executes an isolated connectivity ping against PostgreSQL (`SELECT 1`) with execution latency measurement. If the database is momentarily unavailable or booting, the health response degrades gracefully rather than throwing an unhandled 500 error.

---

## Database Design & Deduplication Architecture

The platform models 7 foundational entities:

1. **Users & RBAC (`users`)**:
   - Role-Based Access Control: `ANALYST_TIER_1`, `ANALYST_TIER_2`, `INCIDENT_RESPONDER`, `DETECTION_ENGINEER`, `SOC_MANAGER`, `ADMIN`.
   - MFA readiness and failed login attempt tracking for brute-force defense.
2. **Log Sources & Jobs (`log_sources`, `ingestion_jobs`)**:
   - Log sources represent collectors (Syslog, Windows Event Log, Zeek, Suricata).
   - `IngestionJob` tracks batch ingestion runs with `batch_identifier` hashes to prevent reprocessing identical telemetry files or batch cursors.
3. **Normalized Security Events (`normalized_security_events`)**:
   - Unified telemetry schema based on Elastic Common Schema (ECS) and OSSEM.
   - **Duplicate Prevention**: Every event calculates an immutable SHA-256 fingerprint: `SHA256(log_source_id + timestamp + raw_payload)` stored in `event_hash` with a database `UNIQUE` constraint and index. Duplicate records are rejected at ingestion time.
4. **Detection Rules (`detection_rules`)**:
   - Mapped to MITRE ATT&CK tactics (e.g. Credential Access, Defense Evasion).
   - Configurable sliding evaluation windows (`time_window_seconds`) and thresholds.
5. **Security Alerts (`security_alerts`)**:
   - Triggered when telemetry satisfies a rule condition.
   - **Storm Prevention**: Employs a composite `deduplication_key` (`rule_code:entity_ip:entity_user:bucket_time`) preventing alert storms by incrementing `event_count` on existing alerts instead of spamming analysts.
6. **Incidents & Notes (`incidents`, `investigation_notes`)**:
   - Aligned with NIST SP 800-61 Rev 2 lifecycle phases: `OPEN`, `CONTAINMENT`, `ERADICATION`, `RECOVERY`, `POST_INCIDENT_REVIEW`, `CLOSED`.
   - Chronological, author-attributed investigation notes with classification (`ANALYSIS`, `CONTAINMENT_ACTION`, `FORENSIC_EVIDENCE`, `COMMUNICATION`).
7. **Audit Events (`audit_events`)**:
   - Immutable audit trail recording user and system actions (rule modifications, status overrides, containment executions) for SOC 2 and ISO 27001 compliance.

---

## Prerequisites

- **Python**: 3.11+ (Tested on Python 3.13)
- **Node.js**: 20+ (Tested on Node 24)
- **PostgreSQL**: 15+ (Local or Docker container)
- **Git**

---

## Setup & Development Instructions

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables template
cp .env.example .env

# Run database migrations (requires running PostgreSQL)
# alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be accessible at:
- API Base: `http://localhost:8000`
- Swagger Interactive Documentation: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/v1/health`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Copy environment variables template
cp .env.example .env

# Start Vite development server
npm run dev
```

Frontend will be accessible at `http://localhost:5173`.

---

## Testing & Quality Control Commands

### Backend Verification

```bash
# Run backend test suite (in-memory SQLite, isolated rollbacks)
pytest backend/tests -v

# Run code formatting & lint checks
ruff check backend --config backend/pyproject.toml
```

### Frontend Verification

```bash
# Run unit tests via Vitest
npm --prefix frontend run test

# Run TypeScript typecheck
npm --prefix frontend run lint

# Build frontend production bundle
npm --prefix frontend run build
```

---

## Current Scope & Limitations (Phase 1)

- **Foundation Only**: Focuses strictly on architectural layout, database models, Alembic migrations, environment templates, health checks, and communication between frontend and backend.
- **Active Endpoints**: Currently exposes `/` and `/api/v1/health`. Log ingestion APIs, detection rule engine execution, and authentication token issuance will be implemented in subsequent phases.
- **Database Fallback**: In automated unit tests, an in-memory SQLite engine is utilized to guarantee instant, isolated test execution without requiring an active PostgreSQL daemon. Production runtime targets PostgreSQL 15+.
