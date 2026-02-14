
# Work Package 3 — Agent Orchestration Layer

## Objective
Implement the agent “brain” with deterministic testing.

## Modes
- `plan_only`: returns tool plan, no execution
- `execute_safe`: executes allowlisted commands via tools

## Testing Strategy
- Stub LLM for deterministic outputs
- Verify tool call order (logs → status → recommendation)
- Verify audit object populated

## Acceptance Criteria
- Plan-only never runs commands
- Execute-safe runs only allowlisted commands in runner container
- Responses include: answer, plan, actions_taken, generated_script(optional), audit
