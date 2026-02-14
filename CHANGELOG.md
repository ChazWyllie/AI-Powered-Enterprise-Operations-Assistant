# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
