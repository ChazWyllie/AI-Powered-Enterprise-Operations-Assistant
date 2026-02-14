
# Phase Gates (Entry/Exit Criteria)

These gates prevent skipping steps and make your repo “auditably professional.”

## Gate A — Requirements & Design complete
Exit criteria:
- RFC written (docs/rfcs/YYYY-MM-DD-rfc.md)
- Interfaces + constraints captured
- Risks + guardrails documented

## Gate B — Test plan complete
Exit criteria:
- Test cases listed (unit + integration + negative cases)
- Deterministic fixtures defined (simulator inputs)

## Gate C — Tests written and failing
Exit criteria:
- Tests exist in `/tests`
- `pytest` fails *for the right reason*

## Gate D — Implementation complete
Exit criteria:
- Tests pass locally
- Lint passes
- No sandbox/policy bypass
- Observability hooks present where required

## Gate E — Review complete
Exit criteria:
- Reviewer checklist completed
- Security concerns resolved
- Changelog updated

## Gate F — Release-ready
Exit criteria:
- Docker build works
- “Demo prompts” documented in README
- CI green
