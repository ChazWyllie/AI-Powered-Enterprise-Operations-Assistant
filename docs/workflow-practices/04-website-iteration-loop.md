
# Website Track Iteration Loop (WP7–WP15)

This is the same Planner → Tests → Implement → Review loop, specialized for website work.

## Step order (do not skip)
1) Planner: short design + acceptance criteria + tests
2) Tests: add failing tests (frontend + backend)
3) Implement: minimal code to satisfy tests
4) Review: security + correctness + UX
5) Changelog: log the WP completion
6) Next WP

## Safety defaults
- Public demo defaults to **plan_only**
- execute_safe is local-only or auth-gated
- Rate limit public endpoints
- Strict CORS
