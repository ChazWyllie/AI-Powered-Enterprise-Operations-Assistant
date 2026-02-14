
# WP11 — Deployment Architecture (Backend + Frontend + Runner)

## Objective
Deploy a live demo you can link on your portfolio.

## Confirm/Decide
- [ ] Backend host: Render / Fly.io / DO / other
- [ ] Runner container deployed? (recommended: NO for public)
- [ ] Domain routing: app vs api subdomains or single domain

## Tests First
- Smoke test script for production:
  - GET /health
  - POST /chat (plan_only)

## Acceptance Criteria
- Live UI loads
- Live API responds
- UI successfully calls API
