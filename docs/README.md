# AI Enterprise Operations Assistant (IBM Z Simulation)

Built an AI-powered enterprise infrastructure assistant integrating LLM tool-calling with an MCP server layer to automate system log analysis and Bash-based environment provisioning; implemented CI/CD pipeline and AI-based test-driven development workflow.

A portfolio-grade AI systems project that integrates:
- FastAPI API service
- LLM agent orchestration
- MCP tool server layer
- Python + Bash automation
- Docker sandbox runner (no host exec)
- Langfuse observability
- AI-based TDD workflow + CI/CD

## Current Status

| Work Package | Status | Description |
|--------------|--------|-------------|
| WP1 Foundation | ✅ Complete | FastAPI scaffold, Docker setup, CI/CD pipeline |
| WP2 Simulator + MCP + Policy | ✅ Complete | Enterprise simulator, MCP tools, security policy engine |
| WP3 Agent Orchestration | ✅ Complete | LLM interface, orchestrator with plan/execute modes |
| WP4 API Integration | ✅ Complete | `/chat` endpoint with full orchestration integration |
| WP5 Langfuse Observability | ✅ Complete | Tracing, metrics, and observability integration |
| WP6 AI-based TDD | ✅ Complete | Security boundary tests, 92% coverage, CI enforcement |

**Test Coverage:** 261 tests passing, 92% line coverage (80% enforced in CI)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check - returns `{"status": "ok"}` |
| POST | `/chat` | Process user message through AI agent orchestration |

### `/chat` Request/Response

```json
// Request
{
  "message": "Check system status and analyze recent errors",
  "mode": "plan_only"  // or "execute_safe"
}

// Response
{
  "answer": "AI-generated analysis...",
  "plan": ["Step 1: ...", "Step 2: ..."],
  "actions_taken": ["get_system_status", "get_logs"],
  "script": "# Generated bash script...",
  "audit": {
    "trace_id": "uuid-...",
    "mode": "plan_only"
  }
}
```

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  FastAPI    │────▶│   Orchestrator   │────▶│  MCP Tools  │
│  /chat      │     │  (LLM decisions) │     │  (execute)  │
└─────────────┘     └──────────────────┘     └─────────────┘
                             │                      │
                             ▼                      ▼
                    ┌──────────────┐        ┌─────────────┐
                    │  Policy      │        │  Simulator  │
                    │  Engine      │        │  Fixtures   │
                    └──────────────┘        └─────────────┘
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_logs(source, tail)` | Retrieve logs: syslog, joblog, audit, error |
| `get_system_status()` | CPU, memory, jobs, subsystem status |
| `run_command(command, dry_run)` | Execute commands with policy enforcement |
| `update_config(key, value)` | Update configuration (sensitive keys blocked) |

## Security Features

- **Command Policy Engine**: Allowlist/blocklist enforcement
- **Path Jail**: Only `/sim/**` paths allowed
- **Shell Injection Prevention**: Metacharacter blocking (`;`, `|`, `&`, `` ` ``, etc.)
- **Sandbox Runner**: Network-isolated, read-only, no capabilities
- **Sensitive Key Protection**: Blocks api_secret, password, token updates

## Repo Structure

```
├── src/app/           # Application code
│   ├── main.py        # FastAPI application
│   ├── orchestrator.py # Agent orchestration
│   ├── llm.py         # LLM interface
│   ├── policy.py      # Security policy engine
│   └── mcp/tools.py   # MCP tool implementations
├── tests/             # Pytest suite (261 tests, 92% coverage)
├── simulator/fixtures/ # Deterministic test data
├── docs/              # Architecture + RFCs
├── prompts/           # Reusable agentic templates
├── agents/            # Planner/implementer/reviewer roles
└── .github/workflows/ # CI pipeline
```

## Quick Start

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing --cov-fail-under=80

# Start with Docker
docker compose up

# Run linting
ruff check src tests
```

## Demo Prompts

Try these with the `/chat` endpoint to see different capabilities:

```bash
# 1. System status check (plan_only)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the current system status?", "mode": "plan_only"}'

# 2. Log analysis (execute_safe)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me recent error logs", "mode": "execute_safe"}'

# 3. Multi-tool orchestration (execute_safe)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Check CPU and memory, then show the syslog", "mode": "execute_safe"}'

# 4. Safe command execution (plan_only — dry run)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List files in the simulator directory", "mode": "plan_only"}'

# 5. Configuration update (execute_safe)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Set the log level to debug", "mode": "execute_safe"}'

# 6. Security boundary test — dangerous request is safely handled
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Delete all system files", "mode": "execute_safe"}'
```

## Tech Stack

- **Python 3.11** + FastAPI + Pydantic
- **OpenAI GPT-4** (with tool calling)
- **Langfuse** (observability + tracing)
- **Docker** (sandbox runner with security hardening)
- **Pytest** + httpx + pytest-cov (testing, 92% coverage)
- **Ruff** (linting + formatting)
- **GitHub Actions** (CI/CD with coverage enforcement)
