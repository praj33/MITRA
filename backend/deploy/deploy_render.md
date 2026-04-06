# Render Deployment Guide

This backend is now part of the merged two-service architecture:

- `backend/` on Render
- `frontend/frontend/` on Vercel

## Render Settings

- Root directory: `backend`
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

## Required Environment Variables

```text
API_KEY=replace-with-strong-random-value
JWT_SECRET_KEY=replace-with-strong-random-value
MONGODB_URI=your-mongodb-connection-string
DATABASE_NAME=ai_assistant
FRONTEND_URL=https://your-vercel-app.vercel.app
ENV=production
ENVIRONMENT=production
```

## Recommended Optional Variables

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
```

## Post-Deploy Checks

- `GET /health`
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/assistant`

## Notes

- The old standalone auth microservice is deprecated and is no longer part of the default deployment path.
- Use `backend/render.yaml` as the most reliable Render blueprint for this service.
- See the repo-level merged guide at `MERGED_DEPLOYMENT_GUIDE.md` for the full two-service setup.
