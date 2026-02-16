# AI-Powered Enterprise Operations Assistant

> An AI agent that automates IBM Z / enterprise mainframe operations using LLM tool-calling, a Model Context Protocol (MCP) server layer, and a security-hardened Docker sandbox — with a React web UI for interactive demos.

![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![React 19](https://img.shields.io/badge/react-19-61DAFB)
![Tests](https://img.shields.io/badge/tests-323%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

🌐 **[Live Demo →](https://chazwyllie.github.io/AI-Powered-Enterprise-Operations-Assistant/)**

---

## Why It Matters

Enterprise AI isn't just about calling an LLM — it's about **trust boundaries, auditability, and safe execution**. This project demonstrates production-grade patterns that enterprises demand:

- An LLM agent that can **plan** dangerous operations without executing them
- A security policy engine that blocks shell injection, path traversal, and destructive commands **before** they reach the sandbox
- Full observability — every LLM call, tool execution, and policy decision is traced
- A public demo mode that guarantees **read-only behavior** for internet-facing deployments

**If you're hiring for AI engineering, platform engineering, or DevOps roles**, this project shows the full stack: from React frontend → FastAPI backend → LLM orchestration → sandboxed tool execution → production deployment.

---

## Overview

This project is a portfolio-grade AI systems build that demonstrates end-to-end integration of:

- **LLM Agent Orchestration** — GPT-4 with structured tool-calling (plan-only & execute-safe modes)
- **MCP Tool Server** — 4 enterprise tools: log retrieval, system status, command execution, config management
- **Security Policy Engine** — Command allowlist/blocklist, path jail (`/sim/**`), metacharacter injection blocking
- **Observability** — Langfuse tracing with spans for every LLM call, tool execution, and API request
- **Sandbox Isolation** — Docker runner with no network, read-only filesystem, dropped capabilities
- **React Web UI** — Interactive chat interface, demo page with preset prompts, security documentation
- **Production Hardening** — CORS, rate limiting, request size limits, public demo mode gate
- **AI-Based TDD** — 323 tests (294 backend + 29 frontend), 92% coverage, CI-enforced quality gates

## Project Status

| Work Package | Status | Version | Highlights |
|---|---|---|---|
| WP1 Foundation | ✅ Complete | v0.1.0 | FastAPI scaffold, Docker, CI/CD pipeline |
| WP2 Simulator + MCP + Policy | ✅ Complete | v0.2.0 | 4 MCP tools, policy engine, 65 tests |
| WP3 Agent Orchestration | ✅ Complete | v0.3.0 | LLM interface, orchestrator, 18 tests |
| WP4 API Integration | ✅ Complete | v0.4.0 | `/chat` endpoint, Pydantic models, 18 tests |
| WP5 Langfuse Observability | ✅ Complete | v0.5.0 | Trace/span/generation tracking, 23 tests |
| WP6 AI-Based TDD | ✅ Complete | v0.6.0 | Security boundary tests, 92% coverage |
| WP7 Productization RFC | ✅ Complete | v0.7.0 | RFC, architecture docs, threat model |
| WP8 Frontend UI MVP | ✅ Complete | v0.8.0 | React + Vite + TypeScript SPA, 29 tests |
| WP9 Backend Web Hardening | ✅ Complete | v0.9.0 | CORS, rate limiting, request size limits |
| WP10 Public Demo Mode Gate | ✅ Complete | v0.10.0 | execute_safe blocked in public mode |
| WP11 Deployment Architecture | ✅ Complete | v0.11.0 | Render/Vercel deploy, smoke tests |
| WP12 Portfolio Docs + Demo | ✅ Complete | v0.12.0 | Portfolio-grade README, demo content |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for sandbox runner)
- OpenAI API key (optional — deterministic stub available for local dev)

### Local Development

```bash
# Clone and install
git clone https://github.com/ChazWyllie/AI-Powered-Enterprise-Operations-Assistant.git
cd AI-Powered-Enterprise-Operations-Assistant
pip install -r requirements.txt

# Run tests
pytest

# Run tests with coverage enforcement
pytest --cov=app --cov-report=term-missing --cov-fail-under=80

# Lint & format
ruff check src/ tests/
ruff format --check src/ tests/

# Start the API server
PYTHONPATH=src uvicorn app.main:app --reload
```

### Docker

```bash
# Start full stack (API + sandbox runner)
docker compose up

# Health check
curl http://localhost:8000/health
# → {"status": "ok"}
```

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | No | — | OpenAI API key (falls back to deterministic stub) |
| `LANGFUSE_PUBLIC_KEY` | No | — | Langfuse public key for tracing |
| `LANGFUSE_SECRET_KEY` | No | — | Langfuse secret key for tracing |
| `LANGFUSE_HOST` | No | `https://cloud.langfuse.com` | Langfuse host URL |
| `DEMO_MODE` | No | `local` | `public` (plan_only enforced, rate limits) or `local` (full access) |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000,http://localhost:5173` | CORS allowed origins (comma-separated) |
| `RATE_LIMIT_RPM` | No | `30` | Requests per minute per IP address |
| `MAX_REQUEST_BYTES` | No | `2048` | Maximum request body size in bytes |

## API Reference

### `GET /health`

Returns service health status.

```json
{"status": "ok"}
```

### `POST /chat`

Process a user message through the AI agent orchestrator.

**Request:**

```json
{
  "message": "Check system status and analyze recent errors",
  "mode": "plan_only"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | Yes | Natural language instruction (min 1 char, no whitespace-only) |
| `mode` | string | Yes | `"plan_only"` (dry run) or `"execute_safe"` (run tools) |

**Response:**

```json
{
  "answer": "I'll check the current system status. System: CPU 45.2%, Memory 78.1%",
  "plan": [
    {
      "tool": "get_system_status",
      "args": {},
      "reasoning": "User requested system status information",
      "executed": true
    }
  ],
  "actions_taken": [
    {
      "tool": "get_system_status",
      "args": {},
      "success": true,
      "result": {"cpu": 45.2, "memory": {"percent": 78.1}}
    }
  ],
  "script": null,
  "audit": {
    "trace_id": "a1b2c3d4-...",
    "mode": "execute_safe"
  }
}
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     React SPA (Vite)                         │
│  ChatPage │ DemoPage │ AboutPage │ SecurityPage              │
│  Dark theme • Mobile responsive • Mode toggle                │
└──────────────────────┬───────────────────────────────────────┘
                       │  /api proxy (dev) or direct (prod)
┌──────────────────────▼───────────────────────────────────────┐
│                      FastAPI Server                          │
│  CORS │ Rate Limiter │ Size Limit │ Demo Mode Gate           │
│  GET /health                POST /chat                       │
└──────────────────────┬───────────────────────────────────────┘
                       │
          ┌────────────▼─────────────┐
          │    Agent Orchestrator     │
          │  plan_only │ execute_safe │
          └──┬─────────┬──────────┬──┘
             │         │          │
┌────────────▼──┐  ┌───▼────┐  ┌──▼──────────────┐
│  LLM Layer    │  │ Policy │  │ Observability   │
│  GPT-4/Stub   │  │ Engine │  │ Langfuse/Mock   │
└───────────────┘  └───┬────┘  └─────────────────┘
                       │
          ┌────────────▼─────────────┐
          │       MCP Tool Layer      │
          │  get_logs  │ get_status   │
          │  run_cmd   │ update_cfg   │
          └────────────┬─────────────┘
                       │
          ┌────────────▼─────────────┐
          │   Simulator / Fixtures    │
          │  syslog, joblog, audit,   │
          │  error, status.json       │
          └──────────────────────────┘
```

### Execution Modes

| Mode | Behavior |
|---|---|
| `plan_only` | LLM generates a tool-call plan + optional bash script. No tools executed. |
| `execute_safe` | Plan is generated, then tools are executed with policy enforcement. Results summarized in answer. |

## MCP Tools

| Tool | Signature | Description |
|---|---|---|
| `get_logs` | `(source, tail=100)` | Retrieve log entries from syslog, joblog, audit, or error sources |
| `get_system_status` | `()` | CPU, memory, running/queued/failed jobs, subsystem status |
| `run_command` | `(command, dry_run=True)` | Execute shell commands with allowlist + path jail enforcement |
| `update_config` | `(key, value)` | Update config values (sensitive keys like passwords/tokens blocked) |

## Security

### 7-Layer Defense in Depth

| Layer | Protection |
|---|---|
| 1. CORS | Origin allowlist — only configured frontends can call the API |
| 2. Rate Limiting | Per-IP sliding window (default 30 req/min) — blocks abuse |
| 3. Request Size | Body limit (default 2KB) — blocks payload bombs |
| 4. Demo Mode Gate | `DEMO_MODE=public` → execute_safe returns 403 Forbidden |
| 5. Input Validation | Pydantic models reject empty/invalid messages |
| 6. Policy Engine | Command allowlist, blocklist, metacharacter blocking, path jail |
| 7. Docker Sandbox | No network, read-only FS, dropped capabilities, non-root |

### Policy Engine

- **Allowlist**: Only `cat`, `ls`, `head`, `tail`, `grep`, `echo`, `date`, `hostname`, `wc` permitted
- **Blocklist**: `rm`, `chmod`, `chown`, `kill`, `shutdown`, `reboot`, `mkfs`, `dd`, `curl`, `wget` blocked
- **Metacharacter blocking**: `;`, `|`, `&`, `` ` ``, `$()`, `>`, `<`, `\n`, `\r` all rejected
- **Path jail**: All file arguments must resolve to `/sim/**` — traversal (`..`) blocked

### Docker Sandbox (`Dockerfile.runner`)

- Non-root user (`runner:1001`)
- Read-only filesystem
- No network access (`network_mode: none`)
- All capabilities dropped (`cap_drop: ALL`)
- No privilege escalation (`no-new-privileges`)
- Resource limits enforced

### Public Demo Mode

When `DEMO_MODE=public`, the system enforces read-only behavior:
- `execute_safe` mode is **blocked** — returns 403 Forbidden
- Only `plan_only` mode is allowed — LLM generates plans without executing tools
- Policy engine remains active in all modes (blocks dangerous requests even in plan_only)
- Rate limiting protects against abuse

## Frontend

The React SPA provides an interactive interface for exploring the AI agent:

### Pages

| Route | Page | Description |
|---|---|---|
| `/` | Chat | Free-form chat with mode toggle (plan_only / execute_safe) |
| `/demo` | Demo | 6 preset prompts that showcase key capabilities |
| `/about` | About | Project overview and technical details |
| `/security` | Security | Security model documentation |

### Running the Frontend

```bash
cd frontend
npm install
npm run dev          # → http://localhost:5173 (proxies /api → :8000)
npm test             # Run 29 component + API tests
npm run build        # Production build
```

### Demo Page Prompts

The `/demo` page offers one-click prompts that demonstrate:

1. **System Health Check** — `get_system_status` tool planning
2. **Error Log Analysis** — `get_logs` tool with source filtering
3. **Multi-Tool Orchestration** — CPU/memory + syslog in one query
4. **File Listing** — `run_command` with path jail enforcement
5. **Configuration Change** — `update_config` with sensitive key blocking
6. **Security Boundary** — Dangerous request → safe plan (no execution)

## Deployment

### One-Click Deploy

| Platform | Type | Config |
|---|---|---|
| **Render** | Backend API | `render.yaml` — auto-builds from repo |
| **Vercel** | Frontend SPA | Connect repo → set output `frontend/dist` |
| **Docker** | Self-hosted | `docker-compose.prod.yml` with full hardening |

### Production Docker

```bash
# Production stack with security hardening
docker compose -f docker-compose.prod.yml up

# Run smoke tests
bash scripts/smoke-test.sh http://localhost:8000
```

See [`docs/deployment.md`](deployment.md) for detailed deployment guides.

## Demo Prompts

Try these with `curl` after starting the server:

```bash
# 1. System health check (plan only)
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the current system status?", "mode": "plan_only"}' | python -m json.tool

# 2. Log analysis (execute)
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me recent error logs", "mode": "execute_safe"}' | python -m json.tool

# 3. Multi-tool orchestration
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Check CPU and memory, then show the syslog", "mode": "execute_safe"}' | python -m json.tool

# 4. File listing
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List files in the simulator directory", "mode": "plan_only"}' | python -m json.tool

# 5. Configuration change
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Set the log level to debug", "mode": "execute_safe"}' | python -m json.tool

# 6. Security boundary — dangerous request handled safely
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Delete all system files", "mode": "execute_safe"}' | python -m json.tool
```

## Testing

323 tests across 18 test files (294 backend + 29 frontend):

### Backend Tests (Python — pytest)

| Category | Tests | Files |
|---|---|---|
| Health endpoint | 2 | `test_health.py` |
| Command policy | 38 | `test_policy.py` |
| MCP tools | 27 + 24 | `test_mcp_tools.py`, `test_mcp_tools_coverage.py` |
| Orchestrator | 18 + 22 | `test_orchestrator.py`, `test_orchestrator_coverage.py` |
| API integration | 18 | `test_api_integration.py` |
| Observability | 23 + 32 | `test_observability.py`, `test_observability_coverage.py` |
| LLM interface | 27 | `test_llm_coverage.py` |
| Security boundaries | 30 | `test_security_boundaries.py` |
| Web hardening | 15 | `test_web_hardening.py` |
| Demo mode gate | 10 | `test_demo_mode_gate.py` |
| Smoke tests | 8 | `test_smoke.py` |

### Frontend Tests (TypeScript — Vitest)

| Category | Tests | Files |
|---|---|---|
| Chat input component | 8 | `ChatInput.test.tsx` |
| Response renderer | 10 | `ResponseRenderer.test.tsx` |
| Error display | 3 | `ErrorDisplay.test.tsx` |
| API client | 8 | `api.test.ts` |

**Coverage by module:**

| Module | Coverage |
|---|---|
| `llm.py` | 98% |
| `observability.py` | 95% |
| `policy.py` | 91% |
| `main.py` | 89% |
| `orchestrator.py` | 89% |
| `mcp/tools.py` | 82% |
| **Total** | **92%** |

## Repo Structure

```
├── src/app/               # Application source code
│   ├── main.py            # FastAPI app, middleware, /health + /chat
│   ├── orchestrator.py    # Agent orchestrator (plan/execute modes)
│   ├── llm.py             # LLM interface (OpenAI + deterministic stub)
│   ├── policy.py          # Security policy engine
│   ├── observability.py   # Langfuse tracing integration
│   └── mcp/tools.py       # MCP tool implementations
├── frontend/              # React SPA (Vite + TypeScript)
│   ├── src/
│   │   ├── api/client.ts       # Typed API client (chat, health)
│   │   ├── components/         # ChatInput, ResponseRenderer, ErrorDisplay
│   │   ├── pages/              # ChatPage, DemoPage, AboutPage, SecurityPage
│   │   ├── types/chat.ts       # TypeScript interfaces
│   │   └── App.tsx             # Router + navigation + dark theme
│   └── package.json            # React 19, Vite 6, Vitest
├── tests/                 # 294 backend tests (92% coverage)
├── simulator/fixtures/    # Deterministic log + status data
├── docs/                  # Architecture, RFC, deployment, checklists
│   ├── architecture.md         # Full architecture documentation
│   ├── deployment.md           # Render / Vercel / Docker deploy guide
│   └── rfcs/                   # Productization RFC + threat model
├── scripts/smoke-test.sh  # Production smoke tests
├── prompts/               # Reusable agentic prompt templates
├── agents/                # Planner / implementer / reviewer roles
├── .github/workflows/     # CI: lint → test (80%+ coverage) → docker
├── Dockerfile             # API container (Python 3.11-slim)
├── Dockerfile.runner      # Sandbox runner (security-hardened)
├── docker-compose.yml     # Development multi-container orchestration
├── docker-compose.prod.yml # Production compose with hardening
├── render.yaml            # Render one-click deployment blueprint
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Ruff + pytest config
└── CHANGELOG.md           # Versioned changelog (v0.1.0 → v0.12.0)
```

## CI/CD Pipeline

```
┌────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Lint  │────▶│  Test (80%+ coverage)│────▶│  Docker Build   │
│  ruff  │     │  pytest + pytest-cov │     │  + Health Check │
└────────┘     └──────────────────────┘     └─────────────────┘
```

- **Lint**: `ruff check` + `ruff format --check` (Python 3.11 target, 100-char line length)
- **Test**: `pytest --cov-fail-under=80` — fails the build if coverage drops below 80%
- **Docker**: Build image → start container → `curl /health` → verify `{"status":"ok"}`

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11, TypeScript 5.7 |
| API Framework | FastAPI + Pydantic v2 |
| Frontend | React 19 + Vite 6 + React Router v7 |
| LLM | OpenAI GPT-4 (tool calling) |
| Observability | Langfuse (traces, spans, generations) |
| Containerization | Docker + Docker Compose |
| Backend Testing | pytest, pytest-asyncio, pytest-cov, httpx |
| Frontend Testing | Vitest, React Testing Library, jsdom |
| Linting | Ruff (Python), TypeScript strict mode |
| CI/CD | GitHub Actions |
| Deployment | Render (backend), Vercel (frontend) |

## License

MIT
