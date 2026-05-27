# Career analytics

## Capabilities

| Widget | Description |
|--------|-------------|
| Dashboard | High-level KPIs |
| Salary insights | Expected vs market (INR support in UI) |
| Market trends | Role demand over time |
| Skill demand | Trending skills |
| Application funnel | saved → applied → interview → offer |
| Provider performance | Which sources perform best |
| Career growth | Progress metrics |
| Role transitions | Path analysis |
| Heatmap | Activity / apply patterns |
| Weekly insights | Digest-style summaries |

![Career analytics](../assets/screenshots/career-analytics.png)

## Frontend

**Page:** `src/pages/CareerAnalytics.jsx`  
**Charts:** `src/components/careerAnalytics/CareerAnalyticsCharts.jsx`  
**Service:** `src/services/careerAnalyticsService.js`  
**Hub:** Intelligence → Analytics

**UI notes:** Role dropdown filter; chart tooltips styled for dark theme (orange/yellow).

## Backend

**Router:** `app/api/routes/career_analytics.py`  
**Services:** `app/services/career_analytics/*`

Prefix: `/career-analytics/`

Data sources: `jobs`, `applications`, `scan_sessions`, aggregated in memory with caching TTLs from config.

## Caching

`CACHE_ANALYTICS_TTL` (default 600s) in `config.py` for expensive aggregates.

## Related

- [Career copilot](./job-discovery.md) — conversational layer on same data
- [Dashboard](../ui/ui-walkthrough.md)
