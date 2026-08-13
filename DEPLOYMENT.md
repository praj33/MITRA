# 🚀 MITRA AI Companion — Cloud VM Deployment & Operations Handbook

> **Platform Version:** MITRA v5.0.0 Unified Release  
> **Deployment Architecture:** 2-Tier Containerized Monorepo Stack (FastAPI Backend + React PWA Frontend)  
> **Database Specification:** Cloud MongoDB Atlas Replica Set (Runtime Environment Injection)  

---

## 1. 🏗️ Architecture Overview

```
 ┌─────────────────────────────────────────────────────────────┐
 │                 Client PWA Browser Application              │
 │                     (React + TypeScript)                    │
 └──────────────────────────────┬──────────────────────────────┘
                                │ HTTP / WebSockets (Port 3000 / 8000)
 ┌──────────────────────────────▼──────────────────────────────┐
 │                      Containerized Stack                    │
 │ ┌────────────────────────────┐  ┌─────────────────────────┐ │
 │ │      mitra_frontend        │  │      mitra_backend     │ │
 │ │       (Node Serve)         │  │   (FastAPI / Uvicorn)   │ │
 │ └────────────────────────────┘  └────────────┬────────────┘ │
 └──────────────────────────────────────────────┼──────────────┘
                                                │ PyMongo / Motor
 ┌──────────────────────────────────────────────▼──────────────┐
 │                  MongoDB Atlas Replica Set                  │
 │      (Users, Tasks, Habits, Reminders, Memories, Facts)     │
 └─────────────────────────────────────────────────────────────┘
```

---

## 2. 📁 Environment File Locations

The system requires two separate environment configuration files:

| Target File Path | Purpose | Loaded By |
|---|---|---|
| [`backend/.env`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/MITRA/MITRA/backend/.env) | FastAPI runtime, security keys, email/whatsapp credentials, LLM gateway URL | Backend Container (`mitra_backend`) & compose |
| [`frontend/.env`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/MITRA/MITRA/frontend/.env) | React SPA environment variables (`REACT_APP_API_URL`, `REACT_APP_API_KEY`) | Frontend Container (`mitra_frontend`) |

---

## 3. 🔑 Required GitHub Secrets for CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/cicd.yml`) requires the following repository secrets:

| Secret Name | Description | Example / Required Value |
|---|---|---|
| `DOCKER_USERNAME` | Docker Hub registry username | `bhiv` |
| `DOCKER_PASSWORD` | Docker Hub access token or password | `dckr_pat_xxx` |
| `VM_IP` | Remote Virtual Machine IP Address | `163.128.209.18` |
| `VM_USERNAME` | SSH username on VM | `ubuntu` |
| `VM_PASSWORD` | SSH authentication password | `YourVMPassword123` |
| `VM_PORT` | SSH access port | `22` |
| `MONGODB_URI` | **MongoDB Atlas Connection String** (Runtime Injected) | `mongodb+srv://user:pass@cluster.mongodb.net/ai_assistant` |
| `BACKEND_ENV_FILE` | Full contents of `backend/.env` file | Entire `backend.env` key-value contents |
| `FRONTEND_ENV_FILE` | Full contents of `frontend/.env` file | Entire `frontend.env` key-value contents |

---

## 4. 🛢️ MongoDB Atlas Runtime Injection Mechanism

To adhere to strict security practices, connection strings are **never baked into Docker images or committed code**.

### How Runtime Injection Works:
1. **GitHub Pipeline Execution**:
   In `.github/workflows/cicd.yml`, the SSH deployment step sets the environment variable dynamically:
   ```bash
   export MONGODB_URI='${{ secrets.MONGODB_URI }}'
   ```
2. **Compose Substitution**:
   `docker-compose.production.template.yml` specifies:
   ```yaml
   backend:
     environment:
       - MONGODB_URI=${MONGODB_URI}
   ```
3. **Container Environment**:
   `mitra_backend` reads `MONGODB_URI` directly at process instantiation.

---

## 5. 💻 Local Execution & Testing SOP

To run the containerized stack locally on your machine:

```bash
# 1. Build and start containers
docker compose build
docker compose up -d

# 2. Check health status
docker compose ps
curl -sf http://localhost:8011/health

# 3. View container logs
docker compose logs -f

# 4. Stop stack
docker compose down
```

---

## 6. 🩺 Health Verification Endpoints

| Endpoint | Method | Target Service | Expected Output |
|---|---|---|---|
| `http://163.128.209.18:8011/health` (or `https://mitra.blackholeinfiverse.com/api/health`) | `GET` | FastAPI Backend | `{"status":"ok","version":"5.0.0"}` |
| `http://163.128.209.18:8011/health/system` | `GET` | FastAPI Backend | Full JSON snapshot of DB, memory, capabilities |
| `http://163.128.209.18:3007` (or `https://mitra.blackholeinfiverse.com`) | `GET` | React Frontend | `HTTP 200 OK` (PWA static asset bundle) |


