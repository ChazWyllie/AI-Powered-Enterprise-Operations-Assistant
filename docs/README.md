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
| WP5 Langfuse Observability | 🔲 Not Started | Tracing, metrics, and observability integration |
| WP6 AI-based TDD | 🔲 Not Started | Test-driven development workflow automation |

**Test Coverage:** 103 tests passing

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
├── tests/             # Pytest suite (103 tests)
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

# Start with Docker
docker compose up

# Run linting
ruff check src tests
```

## Tech Stack

- **Python 3.11** + FastAPI + Pydantic
- **OpenAI GPT-4** (with tool calling)
- **Docker** (sandbox runner with security hardening)
- **Pytest** + httpx (testing)
- **Ruff** (linting)
- **GitHub Actions** (CI/CD)
