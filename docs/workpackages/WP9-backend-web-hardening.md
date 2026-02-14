
# WP9 — Backend Hardening for Web Use (CORS + Validation + Rate Limits)

## Objective
Make backend safe and stable for browser calls.

## Confirm/Decide
- [ ] Allowed origins: dev + prod domain(s)
- [ ] Request size limits
- [ ] Rate limiting strategy (recommended public)

## Tests First
- CORS: allowed origin works; disallowed fails
- Validation: invalid mode returns 400
- Rate limit: repeated calls trigger 429 (if enabled)

## Acceptance Criteria
- Browser can call `/chat` from the UI
- Abuse-resistant defaults for public mode
