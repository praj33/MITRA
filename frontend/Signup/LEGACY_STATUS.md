# Legacy Auth Service

This folder contains the original standalone Express auth microservice.

## Status

- Deprecated for the active MITRA integrated deployment
- Not required for the current production architecture
- Replaced by FastAPI auth routes in `backend/app/api/auth.py`

## Current Deployment Architecture

Use only:

- `backend/` -> Render
- `frontend/frontend/` -> Vercel

## Why This Exists

This code is kept only as a historical reference while the merged backend auth rollout stabilizes.

Do not deploy this service unless you intentionally want to restore the old three-service architecture.
