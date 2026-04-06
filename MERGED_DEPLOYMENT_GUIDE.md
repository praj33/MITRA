# Merged Deployment Guide

Date: 2026-04-06

## Final Architecture

Deploy only two services:

- `backend/` -> Render web service
- `frontend/frontend/` -> Vercel project

The old `frontend/Signup/` auth microservice is now legacy and should not be deployed in the default setup.

## Backend on Render

Root directory:

```text
backend
```

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Required environment variables:

```text
API_KEY=replace-with-strong-random-value
JWT_SECRET_KEY=replace-with-strong-random-value
MONGODB_URI=your-mongodb-connection-string
DATABASE_NAME=ai_assistant
FRONTEND_URL=https://your-vercel-app.vercel.app
ENV=production
ENVIRONMENT=production
```

Recommended optional environment variables:

```text
LOG_LEVEL=INFO
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=
EMAIL_PASSWORD=
SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=
BREVO_API_KEY=
BREVO_FROM_EMAIL=
BREVO_FROM_NAME=AI Assistant
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_URL=
GOOGLE_CALENDAR_API_KEY=
GOOGLE_CALENDAR_ACCESS_TOKEN=
GOOGLE_CALENDAR_ID=primary
EMS_API_URL=
EMS_API_KEY=
META_VERIFY_TOKEN=mitra_verify_token
WHATSAPP_PROVIDER=cloud
WHATSAPP_CLOUD_ACCESS_TOKEN=
WHATSAPP_CLOUD_PHONE_NUMBER_ID=
WHATSAPP_CLOUD_API_VERSION=v20.0
WHATSAPP_CLOUD_BASE_URL=https://graph.facebook.com
WHATSAPP_WEBHOOK_SECRET=
WHATSAPP_VERIFY_TOKEN=
INBOUND_MEDIATION_ENABLED=1
OUTBOUND_SAFETY_GATE_ENABLED=1
```

Render health check path:

```text
/health
```

## Frontend on Vercel

Root directory:

```text
frontend/frontend
```

Build command:

```bash
npm run build
```

Output directory:

```text
build
```

Required environment variables:

```text
REACT_APP_API_URL=https://your-render-backend.onrender.com
REACT_APP_API_KEY=the-same-api-key-you-set-on-render
```

Optional legacy override:

```text
REACT_APP_AUTH_API_URL=https://your-render-backend.onrender.com
```

You do not need a separate auth backend URL in the merged architecture.

## Local Development

Backend:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend/frontend
npm install
npm start
```

Frontend local env:

```text
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_KEY=localtest
```

## Post-Deploy Smoke Checks

Backend:

```text
GET  /health
POST /api/auth/signup
POST /api/auth/login
GET  /api/auth/me
POST /api/assistant
```

Frontend:

- signup works
- login works
- chat works
- refresh preserves session
- logout clears session

## Notes

- The backend now enriches assistant requests with the authenticated user when a bearer token is present.
- The React app uses the same backend base URL for auth and assistant traffic.
- The legacy `frontend/Signup/` folder is intentionally not deleted, but it is no longer part of the recommended deployment.
