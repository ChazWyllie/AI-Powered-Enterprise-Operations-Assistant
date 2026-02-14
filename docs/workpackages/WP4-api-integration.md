
# Work Package 4 — API Integration (FastAPI)

## Objective
Expose the system via API with strict request/response contracts.

## Endpoints
- `GET /health`
- `POST /chat`

## Acceptance Criteria
- Validates inputs (mode enum, message required)
- Graceful errors (400 for invalid mode/policy)
- End-to-end integration tests pass (API → Agent → MCP tools)
