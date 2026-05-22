# Career OS

Career OS is a modular job-search automation platform. This repository contains the foundational architecture for a React dashboard and a FastAPI backend, prepared for scraping, AI matching, background workers, and browser automation in later phases.

## Architecture

```
career-os/
├── frontend/          # React + Vite dashboard (placeholder UI)
├── backend/           # FastAPI API and domain-oriented packages
├── docker-compose.yml # Redis (+ optional backend profile)
└── .env.example       # Environment variable template
```

The backend is organized by service domains under `backend/app/`:

| Package | Purpose |
|---------|---------|
| `api/` | HTTP routes and request handlers |
| `core/` | App config, Celery app |
| `models/` | Data models and schemas |
| `services/` | Business orchestration |
| `workers/` | Celery task workers |
| `automation/` | Playwright browser workflows |
| `ai_engine/` | AI matching and scoring |
| `scheduler/` | Scheduled jobs |
| `notifications/` | Email and alerts |
| `utils/` | Shared helpers |

MongoDB is intended for **MongoDB Atlas** (cloud). Redis runs locally via Docker for queues and Celery.

## Tech Stack

**Frontend**

- React 19, Vite, TypeScript
- Tailwind CSS v4, shadcn/ui, lucide-react

**Backend**

- FastAPI, Uvicorn
- Motor / PyMongo (MongoDB)
- Celery, Redis
- Playwright (installed, not wired to workflows yet)

**Infrastructure**

- Docker, docker-compose
- Redis 7 (container)

## Local Setup

### Prerequisites

- Node.js 20+ (Vite 6; Node 20.19+ recommended for latest tooling)
- Python 3.12+
- Docker Desktop (for Redis)

### 1. Environment

```bash
cp .env.example .env
# Edit .env with your Atlas URI and API keys when ready
```

### 2. Redis (Docker)

Start Redis only (recommended for local API development):

```bash
docker compose up redis -d
```

Verify:

```bash
docker compose ps
```

### 3. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

Run the API from the `backend` directory:

```bash
uvicorn app.main:app --reload
```

Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) → `{"status":"ok"}`

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: [http://localhost:5173](http://localhost:5173)

### Optional: Full Docker stack

Includes backend container (slower first build due to Playwright):

```bash
docker compose --profile full up --build
```

## Future Modules (not implemented yet)

- **Job scraping** — ingest listings from target boards
- **AI matching** — Gemini-powered fit scoring and filtering
- **Easy Apply automation** — Playwright workflows for supported apply flows
- **Authentication** — user accounts and session management
- **Application tracking** — pipeline from discovery to submission
- **Notifications** — Resend email for scan results and status updates
- **Scheduler** — recurring scans and rate-limited worker jobs

## Design Notes

- MVP-oriented for ~10 concurrent users: simple containers, domain folders, and placeholder UI
- No business logic in this foundation commit—only structure, health checks, and dashboard shell
- Celery and Playwright are configured as placeholders for the next development phase

## License

Private project — add license terms as needed.
