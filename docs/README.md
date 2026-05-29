# Career OS — Documentation Portal

<p align="center">
  <img src="./assets/ui/career-os-logo.png" alt="Career OS" width="280" />
</p>

**Organization:** [ELVA Tech](https://elvatech.in)  
**Parent platform:** [Career Lens](https://career-lens.in)

Career OS is an AI-powered job discovery and career automation platform deployed as a **modular distributed monolith** on Vercel + Render + MongoDB Atlas.

Documentation is **transparent about architecture** — workers, Mongo queues, limitations, and free-tier tradeoffs are first-class topics, not hidden implementation details.

---

## Audience guide

| You are… | Start here |
|----------|------------|
| **New developer** | [developer-guide/README.md](./developer-guide/README.md) |
| **DevOps / SRE** | [deployment/render-vercel-deployment.md](./deployment/render-vercel-deployment.md) |
| **QA / tester** | [testing/README.md](./testing/README.md) |
| **Product / investor / evaluator** | [product/platform-experience.md](./product/platform-experience.md) |
| **On-call / ops** | [operations/README.md](./operations/README.md) |
| **Architect** | [architecture/overview.md](./architecture/overview.md) |

---

## Architecture (deep dive)

| Document | Topic |
|----------|--------|
| [overview.md](./architecture/overview.md) | System map + status legend |
| [distributed-runtime.md](./architecture/distributed-runtime.md) | `SERVICE_MODE`, entrypoints |
| [scan-worker.md](./architecture/scan-worker.md) | **career-os-scan-worker** |
| [automation-worker.md](./architecture/automation-worker.md) | **career-os-automation** |
| [mongo-queue.md](./architecture/mongo-queue.md) | `scan_execution_tasks`, `scan_states` |
| [realtime-sync.md](./architecture/realtime-sync.md) | `realtime_events` + bridge |
| [deployment-topology.md](./architecture/deployment-topology.md) | Render + Vercel |
| [scaling-strategy.md](./architecture/scaling-strategy.md) | Growth path |
| [free-tier-strategy.md](./architecture/free-tier-strategy.md) | Cost constraints |
| [memory-management.md](./architecture/memory-management.md) | OOM prevention |
| [security-model.md](./architecture/security-model.md) | Trust boundaries |
| [service-boundaries.md](./architecture/service-boundaries.md) | Who owns what |
| [scan-execution-isolation.md](./architecture/scan-execution-isolation.md) | Phases 1A–1B + 6 |
| [diagrams.md](./architecture/diagrams.md) | Mermaid + ASCII flows |

---

## Deployment

| Document | Topic |
|----------|--------|
| [render-vercel-deployment.md](./deployment/render-vercel-deployment.md) | Primary deploy guide |
| [render-multi-service.md](./deployment/render-multi-service.md) | 3 Render services |
| [startup-order.md](./deployment/startup-order.md) | Boot sequence |
| [rollback-and-recovery.md](./deployment/rollback-and-recovery.md) | Incidents |
| [troubleshooting-deploy.md](./deployment/troubleshooting-deploy.md) | Common failures |
| [mongo-atlas-setup.md](./deployment/mongo-atlas-setup.md) | Atlas |
| [upstash-setup.md](./deployment/upstash-setup.md) | Optional cache |
| [playwright-setup.md](./deployment/playwright-setup.md) | Chromium on Render |
| [health-checks.md](./deployment/health-checks.md) | `/health` per service |
| [environment-variables.md](./deployment/environment-variables.md) | Short env table |
| [configuration/environment-variables.md](./configuration/environment-variables.md) | **Full env reference** |
| [uptime-robot-keepalive.md](./deployment/uptime-robot-keepalive.md) | Cold start mitigation |

---

## Testing

[testing/README.md](./testing/README.md) — QA checklists, scan flow, realtime, workers, Mongo, failures.

---

## Product & business

| Document | Topic |
|----------|--------|
| [product/overview.md](./product/overview.md) | Product summary |
| [product/platform-experience.md](./product/platform-experience.md) | User-facing experience |
| [product/job-scan-lifecycle.md](./product/job-scan-lifecycle.md) | Scan journey |
| [product/saas-vision.md](./product/saas-vision.md) | SaaS direction |
| [product/competitive-advantages.md](./product/competitive-advantages.md) | Positioning |
| [product/ai-scoring.md](./product/ai-scoring.md) | Match scores |
| [product/automation-lifecycle.md](./product/automation-lifecycle.md) | LinkedIn / automation |
| [product/dashboard-explanation.md](./product/dashboard-explanation.md) | UI areas |
| [product/privacy-and-security.md](./product/privacy-and-security.md) | Trust |
| [product/vision-and-goals.md](./product/vision-and-goals.md) | Vision |
| [product/onboarding-experience.md](./product/onboarding-experience.md) | Onboarding |

---

## Operations

[operations/README.md](./operations/README.md) — monitoring, logs, queues, TTL, cold starts, incidents, cost.

---

## Developer guide

[developer-guide/README.md](./developer-guide/README.md) — repo layout, scans, automation, realtime bridge, pitfalls, safe deploy.

---

## Configuration & status

| Document | Topic |
|----------|--------|
| [configuration/environment-variables.md](./configuration/environment-variables.md) | All env vars |
| [project-status/current-phase.md](./project-status/current-phase.md) | Phase history + honesty |

---

## Legacy / feature docs

Still valid for feature depth:

- [backend/backend-architecture.md](./backend/backend-architecture.md)
- [frontend/frontend-architecture.md](./frontend/frontend-architecture.md)
- [automation/playwright-automation.md](./automation/playwright-automation.md)
- [features/job-discovery.md](./features/job-discovery.md)
- [api/api-reference.md](./api/api-reference.md)
- [roadmap/future-roadmap.md](./roadmap/future-roadmap.md)

---

## Documentation tree

```text
docs/
├── architecture/          # System design (distributed runtime)
├── configuration/         # Env reference
├── deployment/            # Render, Vercel, ops deploy
├── developer-guide/       # Engineer onboarding
├── operations/            # Runbooks
├── product/               # Customer / business
├── project-status/        # Phase transparency
├── testing/               # QA
├── api/ backend/ frontend/ features/ automation/  # Feature depth
└── README.md              # This portal
```

---

## Production services

| Name | `SERVICE_MODE` | Command |
|------|----------------|---------|
| **career-os** | `api` | `python start_api.py` |
| **career-os-scan-worker** | `scan_worker` | `python start_scan_worker.py` |
| **career-os-automation** | `automation_worker` | `python start_automation_worker.py` |

---

## Status legend (used across docs)

| Label | Meaning |
|-------|---------|
| **Implemented** | In production path |
| **Partial** | Code exists; limited or disabled in prod |
| **Planned** | Documented intent only |

*Last updated: May 2026 — reflects distributed runtime, Mongo sync, Phase 5 TTL, Phase 6 realtime bridge.*
