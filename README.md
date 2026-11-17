# PulsePilot AI

PulsePilot AI is a portfolio-ready social-media analytics workspace. It has a React + TypeScript dashboard, a FastAPI REST API, local SQLite persistence, token-based authentication, and an AI-analysis adapter that works in demo mode or with Ollama.

## What it demonstrates

- Account registration and sign-in; passwords are salted and hashed server-side.
- A dashboard that stores posts and metrics in SQLite through the API only.
- A three-stage analysis pipeline: sentiment extraction, content strategy, and copy recommendations.
- Clear provider behavior: `demo` is deterministic and needs no key; `ollama` uses a local Ollama instance when configured.
- Input validation, useful HTTP errors, loading/error states, automated API tests, Docker configuration, and API docs at `/docs`.

## Structure

```
backend/     FastAPI service, database, auth, AI services, tests
frontend/    React TypeScript client
docs/        architecture and walkthrough
reports/     updated project report and synopsis
```

## Run locally

1. Create a Python virtual environment and install `backend/requirements.txt`.
2. Copy `backend/.env.example` to `backend/.env`. Demo mode works unchanged.
3. From `backend`, run `uvicorn app.main:app --reload`.
4. From `frontend`, run `npm install` then `npm run dev`.

The API starts at `http://localhost:8000`; the client normally starts at `http://localhost:5173`.

## Optional Ollama integration

Install and run Ollama, then set `AI_PROVIDER=ollama` and `OLLAMA_BASE_URL=http://localhost:11434`. The application sends a constrained JSON prompt to `/api/generate`; if the provider cannot respond, the API returns a clear `502` rather than pretending an AI result was generated.

## Quality checks

```bash
cd backend && PYTHONPATH=. pytest
cd ../frontend && npm run build
```
