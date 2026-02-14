# Architecture — AI Enterprise Operations Assistant (IBM Z Simulation)

## Purpose
Build a production-style AI operations assistant that integrates:
- FastAPI service layer
- LLM agent orchestration
- MCP tool server layer
- Python + Bash automation
- Containerized sandbox execution (no host execution)
- Observability via Langfuse
- AI-based TDD workflow
- CI/CD pipeline

This project simulates IBM Z / enterprise infrastructure operations to demonstrate modern AI-driven infrastructure automation.

## High-Level Components
1. **API Gateway (FastAPI)**  
   - Endpoints: `/health`, `/chat`
   - Input validation via Pydantic models
   - Structured logging
   - Calls Agent Orchestrator

2. **Agent Orchestrator**
   - Modes: `plan_only`, `execute_safe`
   - Produces a plan of MCP tool calls
   - Executes tools in safe mode only
   - Returns: answer, plan, actions_taken, generated_script, audit object

3. **MCP Server (Tools Layer)**
   - Tool endpoints:
     - `get_logs(source, tail)`
     - `get_system_status()`
     - `run_command(command, dry_run)`
     - `update_config(key, value)`
   - Enforces command policy + audit logging

4. **Sandbox Runner**
   - A locked-down Docker container used for command execution
   - No network
   - Non-root
   - Read-only filesystem
   - Resource limits + dropped capabilities

5. **Enterprise Simulator**
   - Deterministic fixtures:
     - `/sim/syslog.log`
     - job queue states
     - config store
   - Used for tests and demo

6. **Observability**
   - Langfuse traces:
     - prompt + model response
     - tool calls and results
     - latency, errors
   - Trace ID returned in API response

## Data Contracts
### POST /chat request
- message: string
- mode: enum(plan_only|execute_safe)
- optional context object

### POST /chat response
- answer: string
- plan: list(tool calls)
- actions_taken: list(executed tool calls)
- generated_script: optional string
- audit: includes mode, policy decisions, trace_id

## Safety Guardrails
- No direct host shell execution
- Tool command allowlist + strict argument validation
- Default `plan_only` and default `dry_run=true` in tools
- Path jail: only allow access under `/sim/**`
- Block shell metacharacters and dangerous binaries

## Test Strategy
- Unit tests: policy engine, tool schemas
- Integration tests: API + MCP + sandbox runner
- Deterministic LLM stub for tests; real LLM optional for demo

## Extensibility
- Swap simulator tools for real enterprise connectors
- Add multi-agent roles (Planner/Executor/Reviewer)
- Expand MCP tool set and job operations simulation
