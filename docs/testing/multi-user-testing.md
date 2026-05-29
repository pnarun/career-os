# Multi-user testing

## Goals

Verify data isolation and fair queue behavior under multiple accounts.

## Setup

- Two test users (different emails) or demo seed if enabled locally only (`AUTH_SEED_DEMO_USERS=true` — **never in production**).

## Checklist

| Test | Pass criteria |
|------|----------------|
| Auth isolation | User A cannot `GET` User B jobs/scans |
| Concurrent scans | Two users scanning → separate `scan_id`, `user_id` on tasks |
| Realtime | User A WS events do not appear on User B session |
| Notifications | Each user receives only own scan-complete emails |
| Scheduler | Scheduled scans fire per-user settings |
| Mongo TTL | User A data expiry does not delete User B |

## Load (light)

With `SCAN_WORKER_MAX_CONCURRENT=1`, second user's scan queues — both eventually complete; neither sees other's progress %.

## JWT

Use separate browser profiles or incognito windows to avoid token bleed.
