# MITRA â€” Repository and Deployment Map

> **Document Type:** Operational & DevOps Handover Artifact
> **Source of Truth:** Live Git Repository, CI/CD Workflows, Docker Configurations
> **Repository:** `https://github.com/praj33/MITRA.git`
> **Active Branch:** `main` | **Current HEAD:** `1a0bd3b9ef624007cdb72e961ecb058966d5cffb`
> **Target Audience:** Ashwini Wadekar (Technical Continuity) & Production Engineering
> **Status:** OFFICIAL HANDOVER AUDIT

---

## 1. "START HERE" â€” Ashwini's Rapid Onboarding Protocol

Welcome Ashwini. Follow these 9 concrete steps to initialize and verify the MITRA development and operational environment on your machine.

### Step 1: Clone Repository
```bash
git clone https://github.com/praj33/MITRA.git
cd MITRA
```

### Step 2: Checkout and Verify Main Branch
```bash
git checkout main
git pull origin main
git rev-parse HEAD
# Expected verification: 1a0bd3b9ef624007cdb72e961ecb058966d5cffb
```

### Step 3: Inspect Environment Templates
```bash
# Review templates (DO NOT commit real credentials)
cat .env.example
cat backend/.env.example
cat frontend/frontend/.env.example
```

### Step 4: Install Dependencies
```bash
# 4A. Backend Python Virtual Environment (Python 3.10 required)
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4B. Frontend Node Environment (Node 20 LTS recommended)
cd ../frontend/frontend
npm ci
```

### Step 5: Start Backend Server Locally
```bash
# In backend/ directory with venv activated
# Ensure local MongoDB is running OR set MONGODB_URI to test cluster
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Verify backend:
curl http://localhost:8000/health
# Expected output: {"status":"healthy"}
```

### Step 6: Start Frontend Development Server
```bash
# In frontend/frontend/ directory
npm start
# Opens http://localhost:3000 in your browser
```

### Step 7: Run Automated Verification Test Suites
```bash
# In backend/ directory with venv activated
pytest tests/test_comm_security.py tests/test_comm_contract.py tests/test_comm_pending.py tests/test_email_draft_edit_flow.py -v

# In frontend/frontend/ directory
npm test -- --watchAll=false
```

### Step 8: Inspect Production Deployment Architecture
- Review the automated CI/CD pipeline: `.github/workflows/cicd.yml`
- Review the production Docker Compose template: `docker-compose.production.template.yml`
- Review the cloud VM Nginx specification: `MITRA_CLOUD_VM_DEPLOYMENT_GUIDE.md`

### Step 9: Locate Major Runtime Modules
- Core Gateway: [backend/app/main.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/main.py)
- Communication Engine: [backend/app/services/communication_service.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/services/communication_service.py)
- Gmail / Email Executor: [backend/app/executors/email_executor.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/executors/email_executor.py)
- Capability Registry: [backend/app/capabilities/__init__.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/capabilities/__init__.py)
- Frontend Shell: [frontend/frontend/src/components/shell/ConversationCenter.tsx](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/frontend/frontend/src/components/shell/ConversationCenter.tsx)
- Input & Draft Composer: [frontend/frontend/src/components/shell/InputBar.tsx](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/frontend/frontend/src/components/shell/InputBar.tsx)

---

## 2. Repository Directory Map

```
MITRA/
â”œâ”€â”€ .github/
â”‚   â””â”€â”€ workflows/
â”‚       â””â”€â”€ cicd.yml                # Master GitHub Actions CI/CD Pipeline (build, deploy, rollback)
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ api/                    # REST routers (auth, oauth, communication, companion, assistant)
â”‚   â”‚   â”œâ”€â”€ capabilities/           # Capability adapters (email, calendar, whatsapp, samachar, etc.)
â”‚   â”‚   â”œâ”€â”€ companion/              # Orchestration, session state, memory, personality synthesis
â”‚   â”‚   â”œâ”€â”€ core/                   # Security, database connection, encryption, LLM bridge, logging
â”‚   â”‚   â”œâ”€â”€ ecosystem/              # BHIV partner adapters (TANTRA, Setu, UniGuru, Brahmanda)
â”‚   â”‚   â”œâ”€â”€ executors/              # External execution drivers (email_executor, calendar_executor, whatsapp)
â”‚   â”‚   â”œâ”€â”€ integrations/           # OAuth providers (Google, Microsoft, GitHub)
â”‚   â”‚   â”œâ”€â”€ runtime/                # Event bus, replay engine, attachment runtime, context contracts
â”‚   â”‚   â”œâ”€â”€ services/               # CommunicationService, PendingActionService, BucketService
â”‚   â”‚   â”œâ”€â”€ tantra/                 # TANTRA governance, state machine, insightflow telemetry
â”‚   â”‚   â””â”€â”€ main.py                 # FastAPI application root, CORS, middleware, lifespan
â”‚   â”œâ”€â”€ tests/                      # Automated regression and security test suites
â”‚   â”œâ”€â”€ Dockerfile                  # Multi-stage Python 3.10 production build
â”‚   â””â”€â”€ requirements.txt            # Locked backend dependencies
â”œâ”€â”€ frontend/
â”‚   â””â”€â”€ frontend/
â”‚       â”œâ”€â”€ public/                 # Static assets, favicon, manifest.json, hover embed
â”‚       â”œâ”€â”€ src/
â”‚       â”‚   â”œâ”€â”€ components/         # UI components (shell, cards, modals, auth, dashboard)
â”‚       â”‚   â”œâ”€â”€ contexts/           # React context providers (AuthContext)
â”‚       â”‚   â”œâ”€â”€ store/              # Zustand state stores (authStore, companionStore)
â”‚       â”‚   â”œâ”€â”€ services/           # Frontend API clients (api.ts, communicationService.ts)
â”‚       â”‚   â”œâ”€â”€ App.tsx             # Main React entrypoint
â”‚       â”‚   â””â”€â”€ index.css           # Global Tailwind CSS and design tokens
â”‚       â”œâ”€â”€ Dockerfile              # Node 20 alpine multi-stage static build with 'serve'
â”‚       â””â”€â”€ package.json            # Frontend scripts and locked npm packages
â”œâ”€â”€ docs/                           # Architecture guides, wireframes, design system tokens
â”œâ”€â”€ DEP/                            # Handover, deployment, and operational convergence specs
â”œâ”€â”€ evidence_packet/                # Verification records, test logs, demonstration artifacts
â”œâ”€â”€ docker-compose.production.template.yml # Production container orchestrator template
â””â”€â”€ MITRA_CLOUD_VM_DEPLOYMENT_GUIDE.md     # Production cloud VM setup and Nginx specification
```

---

## 3. Production Deployment Architecture & CI/CD Pipeline

Production is hosted on a dedicated Linux Cloud Virtual Machine (`Ubuntu 22.04 LTS`) managed via GitHub Actions automation.

### 3.1 Production Topology

| Component | Target Location / Container | Internal Port | External Exposure | Domain / Route |
|---|---|---|---|---|
| **Reverse Proxy** | Host VM System Nginx | 80, 443 | Public HTTPS / HTTP | `https://mitra.blackholeinfiverse.com` |
| **Frontend SPA** | Docker container `mitra_frontend` | 3000 | Host `3007` (Proxy internal) | `https://mitra.blackholeinfiverse.com/` |
| **Backend Gateway** | Docker container `mitra_backend` | 8000 | Host `8011` (Proxy internal) | `https://mitra.blackholeinfiverse.com/api/*` |
| **Duplex Audio WS** | Docker container `mitra_backend` | 8000 | Host `8011` (Proxy internal) | `wss://mitra.blackholeinfiverse.com/ws/*` |
| **Database** | MongoDB Atlas Dedicated Cluster | 27017 | Restricted VPC / IP Whitelist | Injected via `MONGODB_URI` secret |

### 3.2 Automated CI/CD Workflow (`.github/workflows/cicd.yml`)

The CI/CD pipeline triggers automatically on any `git push` to `main`:

```
git push origin main
       â”‚
       â–¼
1. Job: validate
   â”œâ”€â”€ Checkout repository (actions/checkout@v4)
   â”œâ”€â”€ Generate compose file with short SHA tag
   â””â”€â”€ Validate Docker Compose configuration with stub env
       â”‚
       â–¼
2. Job: build (runs on ubuntu-latest)
   â”œâ”€â”€ Set short git commit SHA (sha_short)
   â”œâ”€â”€ Build and push backend image to Docker Hub:
   â”‚   â””â”€â”€ bhiv/mitra-backend:${sha_short}
   â””â”€â”€ Build and push frontend image to Docker Hub:
       â””â”€â”€ bhiv/mitra-frontend:${sha_short}
       â”‚
       â–¼
3. Job: deploy (via SSH to production VM)
   â”œâ”€â”€ Inject backend .env from secret BACKEND_ENV_FILE
   â”œâ”€â”€ SCP deployment tarball to VM: ~/MITRA/deployment.tar.gz
   â”œâ”€â”€ Substitute IMG_TAG in docker-compose.production.template.yml
   â”œâ”€â”€ Pull newly built Docker images
   â”œâ”€â”€ Start containers: docker compose -f docker-compose.production.yml up -d
   â”œâ”€â”€ 12-Step Health Check (120 seconds max):
   â”‚   â”œâ”€â”€ Inspect container healthy status: mitra_backend
   â”‚   â””â”€â”€ Probe HTTP status: curl -sf http://localhost:3007
   â”œâ”€â”€ Update Release History: docs/RELEASE_HISTORY.md
   â””â”€â”€ Prune images older than 7 days (preserving recent images for fast rollback)
       â”‚
       â–¼ (If deploy fails)
4. Job: rollback (Automatic Disaster Recovery)
   â”œâ”€â”€ Extract LAST_HEALTHY_TAG from docs/RELEASE_HISTORY.md
   â”œâ”€â”€ Re-substitute IMG_TAG with last known healthy SHA
   â”œâ”€â”€ Pull and start last known healthy container stack
   â”œâ”€â”€ Verify health check on recovered containers
   â””â”€â”€ Record ROLLBACK_SUCCESS in release registry
```

---

## 4. Environment Variables Specification

> **SECURITY INVARIANT:** No real secrets, passwords, or private keys are stored in this document. Below is the strict structural catalog of all runtime environment variables.

| Variable Name | Purpose | Configuration Location | Recommended Owner | Verifiable Production Status |
|---|---|---|---|---|
| `ENV` / `ENVIRONMENT` | Defines operational mode (`production` / `development`) | Backend `.env` & CI/CD secret | Ashwini Wadekar | **VERIFIED** (`production`) |
| `PORT` | FastAPI internal listening port (default 8000) | Backend `.env` | Ashwini Wadekar | **VERIFIED** (8000 inside container) |
| `API_KEY` | Master server-to-server gateway API key | Backend `.env` & GitHub Secret | Ashwini Wadekar | **VERIFIED** |
| `JWT_SECRET_KEY` | Cryptographic key for signing user auth tokens | Backend `.env` & GitHub Secret | Ashwini Wadekar | **VERIFIED** |
| `FRONTEND_URL` | Canonical frontend domain for CORS headers | Backend `.env` | Ashwini Wadekar | **VERIFIED** (`https://mitra.blackholeinfiverse.com`) |
| `CORS_ORIGINS` | Comma-separated allowed external origins | Backend `.env` | Ashwini Wadekar | **VERIFIED** |
| `MONGODB_URI` | MongoDB Atlas replica-set connection string | GitHub Secret `MONGODB_URI` | Ashwini Wadekar | **VERIFIED** (Injected at deploy) |
| `DATABASE_NAME` | Target MongoDB database name (default `ai_assistant`) | Backend `.env` | Ashwini Wadekar | **VERIFIED** |
| `CREDENTIAL_ENCRYPTION_KEY` | AES-256 key for encrypting OAuth tokens at rest | Backend `.env` & GitHub Secret | Ashwini Wadekar | **VERIFIED** (32-byte urlsafe key) |
| `OPENAI_API_KEY` | OpenAI API key for LLM generation | Backend `.env` & GitHub Secret | Ashwini Wadekar | **VERIFIED** |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models | Backend `.env` | Ashwini Wadekar | **OPTIONAL / VERIFIED** |
| `GROQ_API_KEY` | Groq API key for low-latency Llama 3 models | Backend `.env` | Ashwini Wadekar | **OPTIONAL / VERIFIED** |
| `TAVILY_API_KEY` | Tavily Search API key for news & web research | Backend `.env` | Ashwini Wadekar | **VERIFIED** |
| `GOOGLE_CLIENT_ID` | Google Cloud OAuth 2.0 Web Client ID | Backend `.env` & GitHub Secret | Ashwini Wadekar | **VERIFIED** |
| `GOOGLE_CLIENT_SECRET` | Google Cloud OAuth 2.0 Web Client Secret | Backend `.env` & GitHub Secret | Ashwini Wadekar | **VERIFIED** |
| `GOOGLE_REDIRECT_URI` | Google OAuth callback URI | Backend `.env` | Ashwini Wadekar | **VERIFIED** (`.../api/oauth/google/callback`) |
| `MICROSOFT_CLIENT_ID` | Azure App Registration Client ID | Backend `.env` | Ashwini Wadekar | **CONFIGURED / NEEDS CREDENTIAL VERIF** |
| `MICROSOFT_CLIENT_SECRET` | Azure App Registration Secret | Backend `.env` | Ashwini Wadekar | **CONFIGURED / NEEDS CREDENTIAL VERIF** |
| `GITHUB_CLIENT_ID` | GitHub OAuth App Client ID | Backend `.env` | Ashwini Wadekar | **CONFIGURED / NEEDS CREDENTIAL VERIF** |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Secret | Backend `.env` | Ashwini Wadekar | **CONFIGURED / NEEDS CREDENTIAL VERIF** |
| `WHATSAPP_CLOUD_ACCESS_TOKEN` | Meta Developer WhatsApp Cloud API System Token | Backend `.env` | Ashwini Wadekar | **PENDING META VERIFICATION** |
| `WHATSAPP_CLOUD_PHONE_NUMBER_ID` | Meta WhatsApp Cloud Phone Number ID | Backend `.env` | Ashwini Wadekar | **PENDING META VERIFICATION** |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | Custom token for Meta webhook handshake challenge | Backend `.env` | Ashwini Wadekar | **PENDING META VERIFICATION** |
| `TANTRA_API_URL` | TANTRA backend service endpoint | Backend `.env` | Ashwini Wadekar | **ADAPTER ONLY (DEFAULT URL)** |
| `VM_IP` / `VM_USERNAME` / `VM_PASSWORD` | Remote production VM SSH access credentials | GitHub Secrets only | Ashwini Wadekar | **VERIFIED IN ACTIONS** |
| `DOCKER_USERNAME` / `DOCKER_PASSWORD` | Docker Hub registry credentials | GitHub Secrets only | Ashwini Wadekar | **VERIFIED IN ACTIONS** |

---

## 5. Rollback and Disaster Recovery Protocol

In the event that a deployment fails or unexpected runtime degradation occurs post-deployment:

### Automated Rollback
If the 12-step health check fails during CI/CD execution, the GitHub Actions `rollback` job triggers automatically, identifies the last healthy image SHA recorded in `docs/RELEASE_HISTORY.md`, pulls that image tag, and restarts the containers.

### Manual Emergency Rollback via SSH
If manual intervention is required on the production VM:
```bash
# 1. SSH into the production VM
ssh -p <VM_PORT> <VM_USER>@<VM_IP>

# 2. Navigate to MITRA directory
cd ~/MITRA

# 3. Inspect recent release history
tail -n 10 docs/RELEASE_HISTORY.md

# 4. Choose a known stable Git SHA (e.g., 6a4962a) and update docker-compose.production.yml
sed "s|IMG_TAG|6a4962a|g" docker-compose.production.template.yml > docker-compose.production.yml

# 5. Restart services with the stable tag
docker compose -f docker-compose.production.yml up -d --remove-orphans

# 6. Verify health
docker compose -f docker-compose.production.yml ps
curl -I http://localhost:3007
docker inspect --format='{{.State.Health.Status}}' mitra_backend
```

---

## 6. External Repository Dependencies (`_ecosystem_repos/`)

The repository contains an `_ecosystem_repos/` directory with legacy and partner submodules:
- `_ecosystem_repos/companion-runtime/`: Legacy runtime experiments.
- `_ecosystem_repos/duplex-audio/`: Real-time WebSocket audio streaming server.
- `_ecosystem_repos/uniguru-v2/`: UniGuru cognitive engine and ontology snapshots.

> **Operational Note for Ashwini:** None of these sub-repositories are required for running the core MITRA production frontend or backend. Production dependencies are completely self-contained in `backend/` and `frontend/frontend/`.
