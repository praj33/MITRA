# Production Deployment Configuration

This repository now deploys as a merged two-service system:

- `backend/` -> Render
- `frontend/frontend/` -> Vercel

## Backend Environment Variables

Required:

```text
API_KEY=replace-with-strong-random-value
JWT_SECRET_KEY=replace-with-strong-random-value
MONGODB_URI=your-mongodb-connection-string
DATABASE_NAME=ai_assistant
FRONTEND_URL=https://your-frontend.vercel.app
ENV=production
ENVIRONMENT=production
```

Optional:

```text
LOG_LEVEL=INFO
SENTRY_DSN=
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

## Frontend Environment Variables

Required:

```text
REACT_APP_API_URL=https://your-render-backend.onrender.com
REACT_APP_API_KEY=the-same-api-key-you-set-on-render
```

Optional:

```text
REACT_APP_AUTH_API_URL=https://your-render-backend.onrender.com
```

The separate auth service URL is no longer needed in the merged architecture.

## Smoke Tests

Backend:

```bash
curl https://your-render-backend.onrender.com/health
```

```bash
curl -X POST https://your-render-backend.onrender.com/api/auth/signup \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Test User\",\"email\":\"test@example.com\",\"password\":\"securepass123\"}"
```

```bash
curl -X POST https://your-render-backend.onrender.com/api/assistant \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d "{\"version\":\"3.0.0\",\"input\":{\"message\":\"hello\"},\"context\":{\"platform\":\"web\",\"device\":\"desktop\"}}"
```

See `MERGED_DEPLOYMENT_GUIDE.md` for the complete setup.

