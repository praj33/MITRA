# Frontend Workspace

This repo currently contains two frontend-related folders:

- `frontend/` -> active React app for Vercel deployment
- `Signup/` -> legacy standalone auth microservice kept only for reference

## Active Architecture

The current integrated deployment uses:

- `../backend` on Render
- `./frontend` on Vercel

Authentication is now served by the FastAPI backend at:

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`

The `Signup/` service is deprecated and should not be part of the default deployment path.
