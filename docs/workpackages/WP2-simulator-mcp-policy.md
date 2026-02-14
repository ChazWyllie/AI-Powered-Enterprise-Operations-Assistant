
# Work Package 2 — Enterprise Simulator + MCP Tools + Command Policy

## Objective
Introduce a realistic enterprise simulation and an MCP tool layer with strict guardrails.

## Tools (MVP)
- `get_logs(source, tail) -> {lines: [...]}`
- `get_system_status() -> {cpu, mem, jobs}`
- `run_command(command, dry_run) -> {stdout, stderr, exit_code, allowed}`
- `update_config(key, value) -> {ok, previous}`

## Sandbox Requirement (Option B)
- `run_command` must execute ONLY inside the `ai_runner` container
- Never execute commands on host

## Tests First (must exist before code)
- Policy blocks metacharacters and dangerous binaries
- Path jail: only `/sim/**`
- Tool schemas stable and deterministic
- Sandbox checks: non-root, no network, read-only FS

## Acceptance Criteria
- Unit + integration tests pass
- Dangerous commands are blocked even if prompted
- Deterministic fixtures exist under `simulator/fixtures/`
