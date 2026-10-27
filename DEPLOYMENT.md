# Sentinel SOC Platform — Production Deployment Guide

This guide provides deployment instructions for provisioning **Sentinel** across standard enterprise environments (Docker Compose, Linux Systemd, or Cloud PaaS).

> [!IMPORTANT]
> **Deployment Status:** This repository provides complete deployment specifications, container definitions, migration scripts, and production configurations. If external cloud credentials and hosting services have not been provisioned in your specific environment, follow the step-by-step instructions below rather than assuming automated deployment.

---

## 1. System Architecture & Topology

```
                         [ Internet / Enterprise LAN ]
                                      │
                                      ▼ HTTPS (443)
                         [ Reverse Proxy (Nginx / Caddy) ]
                         ├── Serves /dist (Vite React SPA)
                         └── Proxies /api/v1 -> Backend (8000)
                                      │
                                      ▼ HTTP
                         [ FastAPI Backend (Uvicorn / Gunicorn) ]
                         ├── Workers: (2 x CPU Cores) + 1
                         ├── SecurityHeaders & BodySizeLimit Middleware
                         └── Connection Pool: NullPool (Alembic) / QueuePool (App)
                                      │
                                      ▼ TCP (5432)
                         [ PostgreSQL 15+ Database Engine ]
                         └── Schemas: alembic_version, users, log_sources,
                             normalized_security_events, detection_rules,
                             security_alerts, incidents, investigation_notes, audit_events
```

---

## 2. Production Environment Variables Reference

### 2.1 Backend Configuration (`backend/.env`)

```ini
# Core Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Server Bindings
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Strict CORS Whitelist (DO NOT use '*' in production with credentials)
BACKEND_CORS_ORIGINS=["https://sentinel.yourdomain.com"]

# Cryptographic Security (Generate with: openssl rand -hex 32)
SECRET_KEY=generate_a_cryptographically_secure_random_hex_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=480
ALGORITHM=HS256

# Request & Upload Ceilings
MAX_UPLOAD_SIZE_BYTES=10485760
MAX_RECORDS_PER_IMPORT=10000

# Database Connectivity (PostgreSQL 15+)
DATABASE_URL=postgresql+psycopg2://sentinel_user:YourStrongPassword@localhost:5432/sentinel_soc
```

### 2.2 Frontend Configuration (`frontend/.env`)

```ini
# Production API Endpoint (Reverse-proxied route recommended)
VITE_API_BASE_URL=https://sentinel.yourdomain.com
VITE_APP_TITLE=Sentinel SOC Platform
VITE_APP_VERSION=0.1.0
```

---

## 3. Deployment Option A: Docker & Containerized Stack

### 3.1 Docker Compose Specification (`docker-compose.yml`)

Create a root `docker-compose.yml` file:

```yaml
version: "3.8"

services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: sentinel_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-SentinelSuperSecret2026!}
      POSTGRES_DB: sentinel_soc
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sentinel_user -d sentinel_soc"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      ENVIRONMENT: production
      DEBUG: "false"
      DATABASE_URL: postgresql+psycopg2://sentinel_user:${DB_PASSWORD:-SentinelSuperSecret2026!}@db:5432/sentinel_soc
      SECRET_KEY: ${SECRET_KEY}
      BACKEND_CORS_ORIGINS: '["https://sentinel.yourdomain.com"]'
    ports:
      - "8000:8000"
    command: >
      sh -c "alembic upgrade head &&
             python scripts/seed_demo_data.py &&
             gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "80:80"

volumes:
  postgres_data:
```

---

## 4. Deployment Option B: Bare-Metal Linux (Ubuntu 22.04 / 24.04 LTS)

### Step 1: System Dependencies & Database Setup
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip postgresql postgresql-contrib nginx

# Configure PostgreSQL user and database
sudo -u postgres psql << EOF
CREATE USER sentinel_user WITH PASSWORD 'StrongDatabasePassword2026!';
CREATE DATABASE sentinel_soc OWNER sentinel_user;
GRANT ALL PRIVILEGES ON DATABASE sentinel_soc TO sentinel_user;
EOF
```

### Step 2: Backend Setup & Migration Execution
```bash
cd /opt/sentinel/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed initial administrative and telemetry dataset
python scripts/seed_demo_data.py
```

### Step 3: Configure Systemd Service (`/etc/systemd/system/sentinel-backend.service`)
```ini
[Unit]
Description=Sentinel SOC FastAPI Application Server
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/sentinel/backend
EnvironmentFile=/opt/sentinel/backend/.env
ExecStart=/opt/sentinel/backend/.venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 127.0.0.1:8000 \
    --access-logfile /var/log/sentinel/access.log \
    --error-logfile /var/log/sentinel/error.log \
    app.main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo mkdir -p /var/log/sentinel && sudo chown -R www-data:www-data /var/log/sentinel
sudo systemctl daemon-reload
sudo systemctl enable --now sentinel-backend
```

### Step 4: Build and Deploy Frontend
```bash
cd /opt/sentinel/frontend
npm ci
npm run build
sudo cp -r dist/* /var/www/sentinel/
```

### Step 5: Configure Nginx Reverse Proxy (`/etc/nginx/sites-available/sentinel`)
```nginx
server {
    listen 80;
    server_name sentinel.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name sentinel.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/sentinel.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sentinel.yourdomain.com/privkey.pem;

    root /var/www/sentinel;
    index index.html;

    # SPA Routing fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 12M;
    }
}
```

---

## 5. Health Monitoring & Verification

Once services are active, verify the deployment:

1. **Subsystem Health Check:**
   ```bash
   curl -s http://127.0.0.1:8000/api/v1/health | jq
   ```
   *Expected Response:*
   ```json
   {
     "status": "healthy",
     "environment": "production",
     "version": "0.1.0",
     "subsystems": {
       "database": { "status": "connected", "latency_ms": 1.2, "error": null },
       "ingestion_pipeline": { "status": "healthy", "latency_ms": 0.4, "error": null },
       "detection_engine": { "status": "healthy", "latency_ms": 0.2, "error": null }
     }
   }
   ```

2. **Security Headers Verification:**
   ```bash
   curl -I https://sentinel.yourdomain.com/api/v1/health
   ```
   *Verify presence of:*
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `Referrer-Policy: strict-origin-when-cross-origin`
