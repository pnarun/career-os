# AI job matching (product)

**Status:** **Implemented** — scores shown in job feed; tuning ongoing.

## What users see

- **Match score** per job (resume vs description)
- Sort/filter by relevance in dashboard
- Career analytics uses aggregated match history

## How it works (high level)

1. User uploads or builds resume profile (skills, roles).
2. During/after scan, jobs stored with text fields.
3. Matching engine compares resume signals to job title/description/requirements.
4. Gemini may assist copilot/analytics; core scoring uses structured matching logic.

Engine detail: [../automation/resume-matching-engine.md](../automation/resume-matching-engine.md).

## Honest limitations

- Scores are **heuristic + AI-assisted**, not hiring decisions
- Sparse job descriptions → lower confidence
- Board-specific HTML quality affects extraction
- No guarantee of "perfect" ranking vs human judgment

## Privacy

Resume text processed server-side for matching; see [privacy-and-security.md](./privacy-and-security.md).
