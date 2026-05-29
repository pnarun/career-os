# MongoDB Atlas setup

## Cluster

| Setting | Recommendation |
|---------|----------------|
| Tier | M0 free for MVP (512MB) |
| Region | Same as Render (e.g. Singapore) |
| Provider | AWS |

## Database user

- Read/write user for application
- IP allowlist: `0.0.0.0/0` for Render (or Atlas VPC if upgraded)

## Connection string

```env
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/career_os?retryWrites=true&w=majority
```

Set on **all three** Render services: API, scan-worker, automation.

## Indexes

Created at API startup via `ensure_indexes()` / `ensure_ttl_indexes()`.

Watch logs:

```
[TTL_INDEX_CREATED]
[STORAGE_REPORT]
```

## Free-tier limits

- 512MB storage — TTL discipline required
- Connection count — three Render services share pool; use reasonable `maxPoolSize` defaults

## Verification

See [../testing/mongo-verification.md](../testing/mongo-verification.md).
