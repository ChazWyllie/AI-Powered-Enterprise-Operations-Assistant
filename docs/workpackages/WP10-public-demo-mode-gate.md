
# WP10 — Public Demo Mode Gate (Plan-only by Default)

## Objective
Ensure the website demo cannot be abused.

## Confirm/Decide
- [ ] Production demo defaults to plan_only
- [ ] execute_safe behavior:
  - [ ] disabled entirely on public
  - OR [ ] auth token required
  - OR [ ] ENV=local only

## Tests First
- Public mode: execute_safe requests are rejected
- Policy: still denies dangerous commands even in local

## Acceptance Criteria
- Public deployment cannot run commands
- Local dev retains execute_safe (if desired)
