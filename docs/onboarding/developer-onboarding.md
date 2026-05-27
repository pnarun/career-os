# Developer onboarding

Welcome to **Career OS** (ELVA Tech / Career Lens). This guide gets you from clone to running scan in under an hour.

## Prerequisites

| Tool | Version |
|------|---------|
| Node.js | 18+ |
| Python | 3.12 |
| MongoDB | Atlas or local |
| Git | latest |

Optional: Docker (Redis), Playwright browsers

## 1. Clone and structure

```bash
git clone <repo-url>
cd career-os
```

Read [Documentation portal](../README.md) and [System overview](../architecture/system-overview.md).

## 2. Backend setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium

cp .env.example .env
# Edit: MONGO_URI, JWT_SECRET_KEY, GEMINI_API_KEY (minimal)
```

**Run API:**

```bash
uvicorn app.main:app --reload --port 8001
```

Verify: http://127.0.0.1:8001/health  
Docs: http://127.0.0.1:8001/docs

## 3. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
# VITE_API_BASE_URL=http://127.0.0.1:8001
npm run dev
```

Open: http://localhost:5173

## 4. First user flow

1. Register on landing page
2. Upload resume (Resume hub)
3. Configure Settings (roles, scan schedule)
4. Operations → Scans → Run scan now
5. Jobs hub → view feed

## 5. Key code locations

| Task | Where to look |
|------|----------------|
| Add API route | `backend/app/api/routes/` + register in `main.py` |
| Business logic | `backend/app/services/` |
| Add UI page | `frontend/src/pages/` + wire in `App.tsx` |
| API call | `frontend/src/services/*.js` |
| Scheduler | `scheduler_service.py` |
| Playwright | `automation/browser/` |
| Auth | `backend/app/auth/` |

## 6. Conventions

- **Backend:** thin routes, fat services; Pydantic models in `app/models/`
- **Frontend:** `apiFetch` for HTTP; no secrets in `VITE_*`
- **Commits:** focused diffs; don't commit `.env`
- **Debug UI:** only `import.meta.env.DEV`

## 7. Tests

```bash
cd backend
pytest
```

## 8. Docker (optional Redis)

```bash
# from repo root
docker compose up -d redis
# REDIS_ENABLED=true in backend .env
```

## 9. Production deploy

Follow [Render + Vercel deployment](../deployment/render-vercel-deployment.md).

## 10. Get help

- [Troubleshooting](../troubleshooting/common-issues.md)
- API logs: `/logs` when API running
- Team: ELVA Tech engineering

## Day-one checklist

- [ ] `/health` returns ok locally
- [ ] Login works
- [ ] Resume upload succeeds
- [ ] Manual scan stores jobs
- [ ] Read [Security model](../security/security-model.md)
- [ ] Skim [API reference](../api/api-reference.md)
