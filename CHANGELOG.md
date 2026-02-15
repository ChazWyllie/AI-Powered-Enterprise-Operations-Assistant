# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.13.0] - 2026-02-14

### Added

- **WP13 Observability Production**
  - `X-Trace-Id` response header on all `/chat` responses for debugging
  - Health endpoint now reports `observability` status (`langfuse`, `mock`, or `disabled`)
  - Environment-driven observability client: Langfuse when keys set, mock otherwise
  - Environment-driven LLM selection: OpenAI when `OPENAI_API_KEY` set, stub otherwise
  - 17 observability production tests (`test_observability_production.py`):
    - Trace ID presence (4): in audit, valid UUID, unique per request, in execute_safe
    - X-Trace-Id header (3): present, matches body, absent on health
    - Health observability (2): includes field, reports mock when no Langfuse
    - Client selection (4): mock explicit, Langfuse when env set, fallback
    - Trace spans (4): mock records, child spans, span lifecycle, generation tokens

### Changed

- `main.py`: App version → 0.13.0
- `main.py`: Orchestrator uses env-driven observability client (not hardcoded stub)
- Health endpoint response now includes `observability` field
- Test count: 294 → 311 (+17)

## [0.12.0] - 2026-02-14

### Added

- **WP12 Portfolio Docs + Demo Content**
  - Portfolio-grade README rewrite with "Why It Matters" recruiter statement
  - 7-layer defense in depth security documentation
  - Frontend section with pages, routes, and demo prompt descriptions
  - Deployment section with one-click deploy matrix (Render/Vercel/Docker)
  - Updated architecture diagram showing full stack (React → FastAPI → LLM → MCP)
  - WP7–WP12 added to project status table
  - New environment variables documented (DEMO_MODE, ALLOWED_ORIGINS, RATE_LIMIT_RPM, MAX_REQUEST_BYTES)
  - Updated test summary: 323 tests (294 backend + 29 frontend) across 18 files
  - Updated repo structure reflecting frontend/, deployment configs, and scripts/
  - Updated tech stack table with frontend technologies and deployment platforms

## [0.11.0] - 2026-02-14

### Added

- **WP11 Deployment Architecture**
  - `render.yaml` blueprint for one-click Render deployment
  - `docker-compose.prod.yml` for self-hosted production deployment
  - `scripts/smoke-test.sh` for production validation (health, chat, structure, errors)
  - `docs/deployment.md` with Render, Vercel, and Docker Compose guides
  - Updated `docker-compose.yml` with WP9/WP10 environment variables
  - 8 smoke tests (`test_smoke.py`):
    - Health endpoint, chat plan_only, response structure, validation errors
    - Trace ID presence, plan_only no actions, health format

### Changed

- Test count: 286 → 294 (+8)

## [0.10.0] - 2026-02-14

### Added

- **WP10 Public Demo Mode Gate**
  - `DEMO_MODE=public` rejects execute_safe requests with 403 Forbidden
  - Clear error message: "execute_safe is not available in public demo mode"
  - `DEMO_MODE=local` allows execute_safe (default behavior preserved)
  - CommandPolicy enforcement remains active in ALL modes
  - 10 demo mode gate tests (`test_demo_mode_gate.py`):
    - Public: execute_safe rejected 403, plan_only allowed 200, clear error message
    - Local: execute_safe allowed 200, plan_only allowed 200
    - Policy: rm blocked in both modes, shell injection blocked, path traversal blocked
    - Dangerous requests in plan_only still return valid plan

### Changed

- Test count: 276 → 286 (+10)

## [0.9.0] - 2026-02-14

### Added

- **WP9 Backend Hardening for Web Use**
  - CORS middleware: configurable `ALLOWED_ORIGINS` (defaults to localhost:3000,5173)
  - Rate limiting: in-memory sliding-window per-IP, configurable via `RATE_LIMIT_RPM`
  - Request body size limit: `MAX_REQUEST_BYTES` (default 2048), returns 413
  - `DEMO_MODE` environment variable: `public` or `local` (default)
  - `RateLimiter` class with sliding window pruning and per-key isolation
  - 15 backend hardening tests (`test_web_hardening.py`):
    - CORS: allowed origin succeeds, disallowed origin rejected
    - Validation: invalid mode 422, empty message 422, missing fields 422, valid 200
    - Rate limiting: within limit, over limit, disabled when zero, 429 on endpoint, per-IP
    - Request size: oversized 413, normal passes
    - Configuration: DEMO_MODE default, RateLimiter initialization

### Changed

- Updated `test_security_boundaries.py`: very long message now expects 413 (WP9 size limit)
- Backend version bumped to 0.9.0
- Test count: 261 → 276 (+15)

## [0.8.0] - 2026-02-14

### Added

- **WP8 Frontend UI Skeleton (Website MVP)**
  - React + Vite + TypeScript SPA (`frontend/`)
  - Pages: `/` (Chat), `/demo` (Interactive Demo), `/about`, `/security`
  - Components:
    - `ChatInput`: textarea + mode toggle (plan_only / execute_safe) + send button
    - `ResponseRenderer`: structured display of answer, plan, actions, script, audit
    - `ErrorDisplay`: error alert panel with accessibility role
  - API client layer (`src/api/client.ts`):
    - `sendChatMessage()`: POST /chat with typed request/response
    - `checkHealth()`: GET /health availability check
  - Type definitions (`src/types/chat.ts`):
    - ChatRequest, ChatResponse, PlanStep, ActionResult, AuditInfo, ApiError
  - Demo page with 6 preset prompts for guided exploration
  - Security page documenting defense-in-depth model
  - Dark theme UI with responsive mobile layout
  - Vite dev proxy `/api` → `localhost:8000` for local development
  - Test suite: 29 frontend tests across 4 test files:
    - ChatInput: send triggers fetch, mode toggle, loading states, empty validation
    - ResponseRenderer: all sections, missing fields, error badges, singular/plural
    - ErrorDisplay: null, message rendering, accessibility
    - API client: fetch calls, mode payload, error handling, health check

### Technical

- Vite 6 + React 19 + TypeScript 5.7
- Vitest + Testing Library + jsdom for component testing
- React Router v7 for client-side navigation
- CSS custom properties for theming

## [0.7.0] - 2025-06-13

### Added

- **WP7 Productization Spec + Public Demo Safety RFC**
  - Created `docs/rfcs/2025-06-web-demo-rfc.md`:
    - Public demo policy: plan_only enforced, execute_safe rejected (403)
    - Environment detection via `DEMO_MODE` (public/local)
    - Rate limiting spec: 10 req/min per IP in public mode
    - Request size limit: 2KB max
    - Threat model: prompt injection, tool misuse, DoS, data leakage
    - Test plan gates for WP9, WP10, WP14
    - Public-safe behavior policy (6 CAN-do, 6 CANNOT-do)
    - 5 security invariants that must hold at all times
  - Created `docs/architecture.md`:
    - High-level system architecture diagram
    - Component architecture (Frontend, Backend, Orchestrator, Policy, MCP, Observability)
    - Deployment architecture for public demo vs local development
    - Environment configuration table
    - Data flow diagrams (plan_only and execute_safe)
    - Security architecture: 7-layer defense in depth
    - Trust boundary model (untrusted → semi-trusted → trusted)
    - Test architecture summary (261 tests, 92% coverage)
    - Technology stack reference

### Documentation

- RFC documents all design decisions before implementation
- Architecture document serves as single source of truth for system design
- Threat model identifies 4 attack categories with specific mitigations
- Implementation sequence defined: WP7 → WP8 → ... → WP15

## [0.6.0] - 2026-02-13

### Added

- **WP6 AI-Based TDD + Vibe Coding Evidence**
  - Security boundary test suite (`test_security_boundaries.py`):
    - Shell injection vectors: newline, carriage return, semicolons
    - Environment variable expansion blocking
    - Subshell, heredoc, process substitution blocking
    - Path traversal and jail escape attempts
    - API error surface tests (no stack traces leak)
    - Dangerous request safe handling
  - LLM coverage tests (`test_llm_coverage.py`):
    - OpenAILLM initialization, lazy client, env key fallback
    - Mock-based tests for generate (success, tool calls, empty content, API error fallback)
    - System prompt and tool definition validation
    - LLMStub pattern matching: config intents, log sources, command types
  - MCP tools coverage tests (`test_mcp_tools_coverage.py`):
    - Simulated log fallback for all sources
    - Command execution paths: echo actual, simulated, blocked
    - _simulate_command_execution for all command types
    - Config edge cases: whitespace keys, sensitive key blocking
  - Observability coverage tests (`test_observability_coverage.py`):
    - Span/Generation/Trace method coverage with and without Langfuse
    - Langfuse client initialization: no credentials, import error, missing SDK
    - Factory function branches: mock flag, env config, fallback
  - Orchestrator coverage tests (`test_orchestrator_coverage.py`):
    - Execute-safe mode: status, logs, commands, config
    - Answer building for all tool result types
    - Script generation: single/multiple commands, empty, no commands
    - Initialization variants

### Changed

- CI pipeline now enforces 80% minimum coverage via `--cov-fail-under=80`
- Added `pytest-cov` to `requirements.txt`
- README updated with demo prompts section and accurate test counts

### Metrics

- Test suite: 126 → 261 tests (+135 new tests)
- Line coverage: 78% → 92% (+14 percentage points)
- All 6 work packages complete

## [0.5.0] - 2026-02-13

### Added

- **WP5 Langfuse Observability**
  - Observability module (`app/observability.py`) with trace/span management:
    - `ObservabilityClient` abstract base for pluggable backends
    - `MockObservabilityClient` for deterministic testing
    - `LangfuseObservabilityClient` for production tracing
    - `Trace` class with metadata, tags, input/output recording
    - `Span` class for operation-level tracing with status tracking
    - `Generation` class for LLM call tracking with token usage
  - Orchestrator integration:
    - Each `/chat` request creates a trace with unique trace_id
    - LLM calls recorded as spans with input/output
    - Tool calls recorded as individual spans with success/error status
    - Trace output includes answer, plan count, actions count
  - Configuration via environment variables:
    - `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`
    - Falls back to mock client when not configured
  - Test suite expanded: 23 observability tests (126 total tests)

### Observability

- Traces automatically created for all `/chat` requests
- Spans record: LLM generation, tool execution, errors
- Trace IDs returned in API response audit object
- Token usage tracked for LLM generations

## [0.4.0] - 2026-02-13

### Added

- **WP4 FastAPI Integration**
  - `POST /chat` endpoint with full orchestration integration
  - Pydantic request/response models:
    - `ChatRequest` with message and mode fields
    - `ChatResponse` with answer, plan, actions_taken, script, audit
    - `ChatMode` enum: plan_only, execute_safe
    - `AuditInfo` with trace_id and mode tracking
  - Input validation:
    - Required message field with min_length=1
    - Required mode enum with valid values only
    - Whitespace-only message rejection
  - End-to-end integration: API → Orchestrator → MCP Tools
  - Test suite expanded: 18 API integration tests (103 total tests)

### API

- `GET /health` - Returns `{"status": "ok"}` (unchanged from WP1)
- `POST /chat` - Process user message through AI agent
  - Request: `{"message": "...", "mode": "plan_only|execute_safe"}`
  - Response: `{"answer": "...", "plan": [...], "actions_taken": [...], "audit": {...}}`

## [0.3.0] - 2026-02-13

### Added

- **WP3 Agent Orchestration Layer**
  - LLM interface and stub (`app/llm.py`):
    - Abstract `LLMInterface` base class with tool call support
    - `LLMStub` for deterministic testing with intent pattern matching
    - `OpenAILLM` production implementation with GPT-4 tool definitions
    - Structured `LLMResponse` with answer, tool_calls, and reasoning fields
  - Agent orchestrator (`app/orchestrator.py`):
    - `OrchestratorMode` enum: PLAN_ONLY and EXECUTE_SAFE modes
    - `OrchestratorResponse` dataclass with answer, plan, actions_taken, script, audit
    - `AgentOrchestrator` class coordinating LLM decisions and tool execution
    - Automatic tool mapping to MCP functions (get_logs, get_system_status, run_command, update_config)
    - Audit trail with trace_id and mode tracking
    - Script generation from execution results
  - Test suite expanded: 18 orchestrator tests (85 total tests)

### Architecture

- Clean separation: LLM makes decisions, orchestrator coordinates, MCP tools execute
- Deterministic LLMStub enables reliable testing without LLM API calls
- PLAN_ONLY mode never executes, returns plan only
- EXECUTE_SAFE mode executes with full policy enforcement

## [0.2.0] - 2026-02-13

### Added

- **WP2 Enterprise Simulator + MCP Tools + Command Policy**
  - Command policy engine (`app/policy.py`) with strict security guardrails:
    - Allowlist of safe read-only commands (cat, grep, head, tail, ls, etc.)
    - Blocklist of dangerous commands (rm, curl, bash, sudo, etc.)
    - Shell metacharacter blocking (;, |, &, `, $(), >, <, etc.)
    - Path jail enforcement (only `/sim/**` paths allowed)
    - Path traversal prevention (blocks `..` sequences)
  - MCP tools layer (`app/mcp/tools.py`) with 4 core tools:
    - `get_logs(source, tail)` - retrieve logs from syslog, joblog, audit, error
    - `get_system_status()` - get CPU, memory, jobs, subsystem status
    - `run_command(command, dry_run)` - execute commands with policy enforcement
    - `update_config(key, value)` - update configuration with sensitive key blocking
  - Deterministic simulator fixtures:
    - `simulator/fixtures/syslog.log` - system log entries
    - `simulator/fixtures/joblog.log` - batch job execution logs
    - `simulator/fixtures/audit.log` - security audit trail
    - `simulator/fixtures/error.log` - error messages
    - `simulator/fixtures/status.json` - system status metrics
  - Test suite expanded: 38 policy tests + 27 MCP tools tests (65 new tests)

### Security

- Policy engine blocks all known dangerous commands and shell injection vectors
- run_command defaults to `dry_run=True` for safety
- Sensitive config keys (api_secret, password, token) blocked from update_config
- All command validation happens before any execution attempt

## [0.1.0] - 2026-02-13

### Added

- **WP1 Foundation**: Initial project infrastructure
  - FastAPI application with `/health` endpoint returning `{"status": "ok"}`
  - Pydantic response models for type-safe API contracts
  - Structured logging with Python's logging module
  - `requirements.txt` with FastAPI, uvicorn, pytest, httpx, ruff, openai, langfuse
  - `pyproject.toml` with pytest and ruff configuration
  - `Dockerfile` for API container (Python 3.11-slim, non-root user, health check)
  - `Dockerfile.runner` for sandbox execution container with security hardening
  - `docker-compose.yml` with API and runner services (runner locked down per WP2 spec)
  - GitHub Actions CI workflow with lint, test, and Docker build jobs
  - `.gitignore` for Python projects
  - `.env.example` for environment variable documentation
  - `simulator/fixtures/` directory placeholder for WP2
  - Test suite with 2 passing tests for health endpoint

### Security

- Runner container configured with: `network_mode: none`, `read_only: true`, `cap_drop: ALL`, `no-new-privileges: true`, resource limits

[Unreleased]: https://github.com/ChazWyllie/AI-Powered-Enterprise-Operations-Assistant/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/ChazWyllie/AI-Powered-Enterprise-Operations-Assistant/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ChazWyllie/AI-Powered-Enterprise-Operations-Assistant/releases/tag/v0.1.0
