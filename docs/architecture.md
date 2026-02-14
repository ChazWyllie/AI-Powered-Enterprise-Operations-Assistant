# Architecture — AI-Powered Enterprise Operations Assistant

## System Overview

The AI-Powered Enterprise Operations Assistant is an AI-driven operations tool for enterprise infrastructure (IBM Z / mainframe environments). It combines an LLM-powered agent with secure tool execution, policy enforcement, and full observability.

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Public Internet                               │
│                                                                      │
│  ┌──────────────────┐         ┌─────────────────────────────────┐   │
│  │   Frontend SPA    │  HTTPS  │        FastAPI Backend           │   │
│  │   (React/Vite)    │────────▶│                                 │   │
│  │                   │         │  ┌───────────┐  ┌────────────┐  │   │
│  │  • Chat UI        │◀────────│  │  /health  │  │  /chat     │  │   │
│  │  • Mode Toggle    │   JSON  │  └───────────┘  └─────┬──────┘  │   │
│  │  • Plan Viewer    │         │                       │         │   │
│  │  • Audit Panel    │         │  ┌────────────────────▼──────┐  │   │
│  └──────────────────┘         │  │   Agent Orchestrator       │  │   │
│                                │  │                            │  │   │
│                                │  │  ┌──────┐  ┌───────────┐  │  │   │
│                                │  │  │ LLM  │  │  Policy    │  │  │   │
│                                │  │  │Engine│  │  Engine    │  │  │   │
│                                │  │  └──┬───┘  └─────┬─────┘  │  │   │
│                                │  │     │            │         │  │   │
│                                │  │  ┌──▼────────────▼──────┐  │  │   │
│                                │  │  │    MCP Tool Layer     │  │  │   │
│                                │  │  │                       │  │  │   │
│                                │  │  │ get_logs │ run_command│  │  │   │
│                                │  │  │ get_status│update_conf│  │  │   │
│                                │  │  └───────────┬──────────┘  │  │   │
│                                │  └──────────────┼─────────────┘  │   │
│                                │                 │                │   │
│                                │  ┌──────────────▼──────────┐    │   │
│                                │  │  Enterprise Simulator    │    │   │
│                                │  │  (Synthetic Fixtures)    │    │   │
│                                │  │                          │    │   │
│                                │  │  syslog.log │ status.json│    │   │
│                                │  │  joblog.log │ audit.log  │    │   │
│                                │  └─────────────────────────┘    │   │
│                                └─────────────────────────────────┘   │
│                                          │                           │
│                                   ┌──────▼──────┐                    │
│                                   │   Langfuse   │                    │
│                                   │   Cloud      │                    │
│                                   │  (Traces)    │                    │
│                                   └─────────────┘                    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Frontend (SPA)

| Property | Value |
|---|---|
| Framework | React + Vite + TypeScript |
| Hosting | Vercel (static) |
| Pages | `/` (chat), `/about`, `/demo`, `/security` |
| State | Local only (no session persistence) |

**Responsibilities:**
- Chat interface with message input and response rendering
- Mode toggle (plan_only / execute_safe — execute_safe hidden in public mode)
- Structured response display: answer, plan, actions, script, audit
- Error and loading states
- Mobile-responsive layout

### 2. Backend (FastAPI)

| Property | Value |
|---|---|
| Framework | FastAPI + Pydantic v2 + uvicorn |
| Hosting | Render / Fly.io |
| Python | 3.11 |
| Endpoints | `GET /health`, `POST /chat` |

**Responsibilities:**
- Request validation and CORS enforcement
- Demo mode gating (`DEMO_MODE` environment variable)
- Rate limiting (public mode: 10 req/min per IP)
- Agent orchestration pipeline
- Observability integration

### 3. Agent Orchestrator

| Property | Value |
|---|---|
| Module | `app/orchestrator.py` |
| Modes | `plan_only`, `execute_safe` |
| LLM | OpenAI GPT-4 (production) / LLMStub (testing) |

**Pipeline:**
```
User Message
    │
    ▼
┌─────────────┐
│  LLM Engine  │ ← Generate tool call plan
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Plan Only?  │──Yes──▶ Return plan + script (no execution)
└──────┬──────┘
       │ No (execute_safe)
       ▼
┌─────────────────┐
│  Policy Engine   │ ← Validate each command
│  (CommandPolicy) │
└──────┬──────────┘
       │ Pass
       ▼
┌──────────────┐
│  MCP Tools    │ ← Execute validated tools
└──────┬───────┘
       │
       ▼
   Response
```

### 4. Security Layer (CommandPolicy)

| Property | Value |
|---|---|
| Module | `app/policy.py` |
| Strategy | Allowlist + Blocklist + Metacharacter blocking |
| Path Jail | `/sim/**` only |

**Enforcement layers:**
1. **Allowlist** — only `cat`, `head`, `tail`, `grep`, `ls`, etc.
2. **Blocklist** — explicit deny for `rm`, `curl`, `sudo`, `python`, etc.
3. **Metacharacter blocking** — `;`, `|`, `&`, `` ` ``, `$()`, `>`, `<`
4. **Path jail** — all file paths must resolve within `/sim/`
5. **Traversal blocking** — `..` rejected in all paths

### 5. MCP Tool Layer

| Tool | Purpose | Mode |
|---|---|---|
| `get_logs` | Retrieve simulated log entries | Read-only |
| `get_system_status` | Return system metrics | Read-only |
| `run_command` | Execute validated commands | Policy-gated |
| `update_config` | Update simulator config | Write (validated) |

### 6. Observability (Langfuse)

| Property | Value |
|---|---|
| Module | `app/observability.py` |
| Backend | Langfuse Cloud |
| Tracing | Per-request trace with spans |

**What gets traced:**
- Each `/chat` request → Trace with unique ID
- LLM calls → Span with input/output
- Tool executions → Span with success/error status
- Token usage → Generation metrics

---

## Deployment Architecture

### Public Demo

```
┌─────────────┐     ┌─────────────┐     ┌──────────┐
│   Vercel     │────▶│   Render     │────▶│ Langfuse │
│  (Frontend)  │     │  (Backend)   │     │ (Traces) │
└─────────────┘     └─────────────┘     └──────────┘
                          │
                    ┌─────▼─────┐
                    │  OpenAI    │
                    │  API       │
                    └───────────┘

❌ No Runner container in production
❌ No execute_safe in production
✅ plan_only mode only
✅ Rate limited (10 req/min)
✅ Strict CORS
```

### Local Development

```
┌──────────────┐     ┌──────────────┐     ┌────────────┐
│  localhost    │────▶│  localhost    │────▶│  Docker     │
│  :3000       │     │  :8000       │     │  Runner     │
│  (Frontend)  │     │  (Backend)   │     │  Container  │
└──────────────┘     └──────────────┘     └────────────┘
                          │
                    ┌─────▼─────┐
                    │ LLM Stub  │
                    │ or OpenAI │
                    └───────────┘

✅ execute_safe available
✅ Runner container active
✅ No rate limits
✅ Permissive CORS
```

---

## Environment Configuration

| Variable | Public | Local | Description |
|---|---|---|---|
| `DEMO_MODE` | `public` | `local` (default) | Controls security posture |
| `OPENAI_API_KEY` | Set | Optional | LLM provider key |
| `LANGFUSE_PUBLIC_KEY` | Set | Optional | Observability |
| `LANGFUSE_SECRET_KEY` | Set | Optional | Observability |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Same or unset | Langfuse endpoint |
| `ALLOWED_ORIGINS` | `https://enterprise-ops.vercel.app` | `http://localhost:3000` | CORS origins |
| `RATE_LIMIT_RPM` | `10` | `0` (disabled) | Requests per minute |

---

## Data Flow

### Plan-Only Request (Public)

```
Client                    API                  Orchestrator         LLM
  │                        │                       │                │
  │  POST /chat            │                       │                │
  │  mode=plan_only        │                       │                │
  │───────────────────────▶│                       │                │
  │                        │  process(msg, PLAN)   │                │
  │                        │──────────────────────▶│                │
  │                        │                       │  generate(msg) │
  │                        │                       │───────────────▶│
  │                        │                       │  tool_calls[]  │
  │                        │                       │◀───────────────│
  │                        │                       │                │
  │                        │  {answer, plan,       │                │
  │                        │   script, audit}      │                │
  │                        │◀──────────────────────│                │
  │  200 OK                │                       │                │
  │  ChatResponse          │                       │                │
  │◀───────────────────────│                       │                │
```

### Execute-Safe Request (Local Only)

```
Client                    API            Orchestrator    Policy     MCP Tools
  │                        │                  │            │           │
  │  POST /chat            │                  │            │           │
  │  mode=execute_safe     │                  │            │           │
  │───────────────────────▶│                  │            │           │
  │                        │  DEMO_MODE check │            │           │
  │                        │  (must be local) │            │           │
  │                        │  process(msg,    │            │           │
  │                        │   EXECUTE_SAFE)  │            │           │
  │                        │─────────────────▶│            │           │
  │                        │                  │ validate() │           │
  │                        │                  │───────────▶│           │
  │                        │                  │ allowed    │           │
  │                        │                  │◀───────────│           │
  │                        │                  │ execute()  │           │
  │                        │                  │────────────┼──────────▶│
  │                        │                  │ result     │           │
  │                        │                  │◀───────────┼───────────│
  │  200 OK                │                  │            │           │
  │◀───────────────────────│                  │            │           │
```

---

## Security Architecture

See also: [Web Demo RFC](rfcs/2025-06-web-demo-rfc.md)

### Defense in Depth

```
Layer 1: Network     → CORS, rate limiting, request size limits
Layer 2: API         → Demo mode gate (reject execute_safe in public)
Layer 3: Validation  → Pydantic models, enum validation, whitespace checks
Layer 4: Policy      → CommandPolicy (allowlist, blocklist, metachar, path jail)
Layer 5: Sandbox     → Docker runner container (local only)
Layer 6: Data        → Synthetic simulator fixtures only
Layer 7: Observability → Langfuse traces for audit trail
```

### Trust Boundaries

```
┌─────────────────────────────────────────────┐
│  UNTRUSTED: User Input                       │
│  • Chat messages (potential prompt injection) │
│  • Mode selection (may request execute_safe)  │
└──────────────────────┬──────────────────────┘
                       │ Validated by Pydantic + Demo Gate
                       ▼
┌─────────────────────────────────────────────┐
│  SEMI-TRUSTED: LLM Output                   │
│  • Generated plans (may contain bad cmds)    │
│  • Tool call arguments (may have bad paths)  │
└──────────────────────┬──────────────────────┘
                       │ Validated by CommandPolicy
                       ▼
┌─────────────────────────────────────────────┐
│  TRUSTED: MCP Tool Execution                 │
│  • Only after policy validation passes       │
│  • Only in Docker sandbox (local)            │
│  • Only synthetic data accessed              │
└─────────────────────────────────────────────┘
```

---

## Test Architecture

| Layer | Tests | Count | Coverage |
|---|---|---|---|
| Unit — Policy | `test_policy.py` | 38 | Allowlist, blocklist, metachar, path jail |
| Unit — MCP Tools | `test_mcp_tools.py` + `_coverage` | 51 | All 4 tools, edge cases |
| Unit — LLM | `test_llm_coverage.py` | 27 | Stub patterns, OpenAI mock |
| Unit — Observability | `test_observability.py` + `_coverage` | 55 | Mock + Langfuse client |
| Integration — Orchestrator | `test_orchestrator.py` + `_coverage` | 40 | Both modes, all flows |
| Integration — API | `test_api_integration.py` | 18 | HTTP layer, validation |
| Security — Boundaries | `test_security_boundaries.py` | 30 | Injection, traversal, abuse |
| **Total** | | **261** | **92%** |

---

## Technology Stack

| Category | Technology | Version |
|---|---|---|
| Language | Python | 3.11 |
| API Framework | FastAPI | ≥0.109 |
| Validation | Pydantic | v2.5+ |
| ASGI Server | uvicorn | ≥0.27 |
| LLM | OpenAI GPT-4 | SDK ≥1.10 |
| Observability | Langfuse | ≥2.0 |
| Testing | pytest + pytest-asyncio | ≥8.0 |
| Linting | ruff | ≥0.2 |
| Containerization | Docker | Multi-stage |
| CI/CD | GitHub Actions | 3 stages |
| Frontend | React + Vite + TypeScript | (WP8) |
| Hosting | Vercel (FE) + Render (BE) | (WP11) |
