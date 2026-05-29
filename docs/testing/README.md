# Testing documentation

QA and engineering verification for distributed Career OS.

| Guide | Audience |
|-------|----------|
| [manual-qa-checklist.md](./manual-qa-checklist.md) | QA / release |
| [scan-testing-flow.md](./scan-testing-flow.md) | Scan features |
| [realtime-verification.md](./realtime-verification.md) | WebSocket + bridge |
| [worker-verification.md](./worker-verification.md) | Render workers |
| [mongo-verification.md](./mongo-verification.md) | Atlas data |
| [scheduler-testing.md](./scheduler-testing.md) | Cron scans |
| [failure-simulation.md](./failure-simulation.md) | Resilience |
| [frontend-integration.md](./frontend-integration.md) | E2E |
| [queue-verification.md](./queue-verification.md) | Mongo queue |
| [playwright-verification.md](./playwright-verification.md) | Browser automation |
| [browser-crash-recovery.md](./browser-crash-recovery.md) | Crash / session invalid |
| [oom-testing.md](./oom-testing.md) | Memory limits |
| [multi-user-testing.md](./multi-user-testing.md) | Isolation |

Automated backend tests: `cd backend && REDIS_ENABLED=false pytest tests/`
