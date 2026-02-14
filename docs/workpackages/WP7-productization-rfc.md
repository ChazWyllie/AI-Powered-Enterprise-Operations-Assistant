
# WP7 — Productization Spec + Public Demo Safety RFC

## Objective
Lock requirements for a public-facing demo, defining what is exposed publicly vs local-only.

## Confirm/Decide (must be checked before implementation)
- [ ] Public site supports **plan_only only** OR plan_only + execute_safe?
- [ ] If execute_safe is allowed publicly: extra constraints? (rate limits, auth, stricter allowlist)
- [ ] LLM provider for demo: OpenAI vs local Ollama vs stub
- [ ] Langfuse enabled in production demo? (yes/no)

## Deliverables
- [ ] Create `docs/rfcs/{DATE}-web-demo-rfc.md`
- [ ] Update `docs/architecture.md` with web UI + deployment architecture
- [ ] Add threat model section (prompt injection, abuse, DoS, data leakage)

## Planner Outputs
- Public Demo Policy (default behaviors, denial behaviors)
- Deployment decision (where backend runs, whether runner is deployed)
- Test plan list for WP9/WP10/WP14 gates

## Acceptance Criteria
- RFC exists and documents **public demo mode** + security stance
- Clear, written “public-safe behavior” policy
