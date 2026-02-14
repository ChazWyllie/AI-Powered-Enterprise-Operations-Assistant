
# Work Package 1 — Repo & Infrastructure Foundation

## Objective
Create a production-ready skeleton with:
- FastAPI `/health`
- pytest wiring
- Dockerfile + docker-compose (api + runner sandbox container)
- GitHub Actions CI that runs pytest

## Entry Criteria
- Repo scaffolding exists (docs/prompts/agents/src/tests/.github/workflows)

## Outputs
- `requirements.txt` (+ optional `requirements-dev.txt`)
- `src/app/main.py` with `/health`
- `tests/test_health.py` passing
- Docker + compose runnable
- CI workflow runs `pytest`

## Acceptance Criteria
- `pytest -q` passes
- `docker compose up --build` works
- `curl http://localhost:8000/health` returns `{"status":"ok"}`
- CI passes on push/PR

## VS Code Tasks
- Python: Install deps
- Tests: pytest (quick)
- Docker: compose up (build)
- Docker: compose down
