# Job scan lifecycle (product)

## User journey

| Step | User action | System response |
|------|-------------|-----------------|
| 1 | Configure roles, skills, locations | Preferences saved |
| 2 | Upload resume | Profile enriched for matching |
| 3 | Start scan | Instant “started” — no long wait on button |
| 4 | Watch progress | Per-provider status |
| 5 | Review results | Sorted by match |
| 6 | Save / apply | Pipeline tracking |

## Scheduled scans

Users can enable **automatic scans** (e.g. daily or every 6 hours). Scans run even if the user is offline — results appear on next login and via email if enabled.

## Quality signals

- **Match percentage** — resume vs job
- **Remote / India-focused** filters where configured
- **Dedup** — same role not spammed across boards

## When scans fail

Users see error state with reason when possible. Partial success (some boards fail, others succeed) still delivers jobs — **partial success** is normal.

## Email

Optional digest email with top opportunities (typically capped for readability).
