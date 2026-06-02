# Backend Route Layer

Routes:

- GET /api/health
- GET /api/pnl
- GET /api/cost-centers
- GET /api/vendors
- GET /api/transactions?page=1&pageSize=200
- GET /api/trend?quarters=5

All routes:

- Validate query params using zod.
- Resolve period windows server side.
- Use parameterized SQL (`$1`, `$2`, etc.).
- Cache by query for 5 minutes.
- Emit audit logs with userId, endpoint, filter params, response time.
- Do not log response bodies.
