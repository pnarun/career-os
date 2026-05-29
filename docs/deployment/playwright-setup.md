# Playwright setup (deployment)

## Docker (Render)

`backend/Dockerfile` installs Chromium dependencies and runs `playwright install chromium`.

No extra Render build step if using provided Dockerfile.

## Environment

```env
ENABLE_PLAYWRIGHT=true
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_DEFAULT_TIMEOUT_MS=30000
```

## Services that need Playwright

| Service | Playwright |
|---------|------------|
| career-os-scan-worker | **Yes** (job fetch) |
| career-os-automation | **Future** |
| career-os API | Usually no heavy browser in dispatch mode |

## Memory

Free-tier scan-worker: plan for **512MB**. See [../architecture/memory-management.md](../architecture/memory-management.md).

## Local dev

```bash
playwright install chromium
```

## Verification

[../testing/playwright-verification.md](../testing/playwright-verification.md)
