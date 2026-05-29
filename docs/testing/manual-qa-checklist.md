# Manual QA checklist

## Auth & onboarding

- [ ] Register new user
- [ ] Login / logout
- [ ] Refresh token survives page reload
- [ ] Password reset flow
- [ ] Platform tour + resume onboarding modal
- [ ] Privacy policy link works

## Jobs & scans

- [ ] Start background scan — progress moves (poll or WS)
- [ ] Jobs appear in feed after scan
- [ ] Manual scan (`run-scan-now`) queues or completes
- [ ] Scheduled scan fires (worker logs)
- [ ] Pagination on jobs feed (6 per page)

## Realtime

- [ ] WebSocket connects (browser devtools)
- [ ] Progress updates without full page refresh
- [ ] Polling still works if WS disabled

## Automation & extension

- [ ] LinkedIn pairing via Career Lens extension
- [ ] Automation page shows session status
- [ ] Prepare session (local only if headed available)

## Notifications

- [ ] Bell icon — unread count
- [ ] Mark all read

## Settings

- [ ] Preferences save
- [ ] Roles/skills tags
- [ ] Target companies filter

## Production smoke (post-deploy)

- [ ] `GET /health` API + workers
- [ ] Login from Vercel URL
- [ ] One full scan end-to-end
- [ ] Email received (if configured)

## Known acceptable failures

- [ ] Indeed may show 0 jobs — **expected** on some hosts
- [ ] First request slow after Render sleep — **expected**
