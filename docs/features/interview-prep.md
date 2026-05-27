# Interview preparation

## Capabilities

- Job-scoped interview prep overview
- Readiness score and gap analysis
- Generated question banks (behavioral, technical, role-specific)
- Study plan generation
- Mock interview sessions
- Practice mode with progress tracking
- Optional web question enrichment (`INTERVIEW_WEB_QUESTIONS_ENABLED`)

![Interview prep](../assets/screenshots/interview-prep.png)

*Add screenshot when captured.*

## Frontend

**Page:** `src/pages/InterviewPrep.jsx`  
**Service:** `src/services/interviewAiService.js`  
**Hub:** Career track → Interview tab

## Backend

**Router:** `app/api/routes/interview_ai.py`  
**Services:** `app/services/interview_ai/*`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/interview-prep/jobs` | Jobs with prep data |
| GET | `/interview-prep/overview` | Summary for job |
| POST | `/interview-prep/questions` | Generate questions |
| POST | `/interview-prep/mock` | Mock session |
| GET | `/interview-prep/progress` | User progress |

**Collection:** `interview_prep_progress`

## AI

Uses Gemini via `interview_ai_facade.py` and specialized services (`mock_interview_service`, `readiness_service`, etc.).

## Related

- [Job discovery](./job-discovery.md)
- [Applications pipeline](./job-discovery.md) — interview status
