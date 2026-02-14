
# Iteration Loop (Planner → Implementer → Reviewer)

Use this every time you add a feature, fix a bug, or complete a work package.

## Step 0 — Prepare context (human)
- Current goal / work package
- Repo tree (what files exist)
- Constraints (sandboxing, no host exec, etc.)
- Current failing tests (if any)

## Step 1 — Planner (no code)
**Input to Planner**
- `agents/planner.md`
- One of:
  - `prompts/feature-template.md`
  - `prompts/bugfix-template.md`
  - `prompts/refactor-template.md`
- Paste the relevant RFC excerpt (or create one via VS Code task: “Work Package: Start new RFC”)

**Planner output must include**
- Design notes (brief)
- Task breakdown with acceptance criteria
- Test plan (unit/integration)
- Risks / guardrails
- “Stop point” = what needs human approval

## Step 2 — Tests first (human + Implementer)
- Add failing tests in `/tests`
- Run: VS Code Task “Tests: pytest (quick)”
- Commit: `test: add failing tests for <feature>`

## Step 3 — Implementer (code)
**Input to Implementer**
- `agents/implementer.md`
- The Planner output (esp. tests + acceptance criteria)
- Current repo context (files touched)

**Implementer output must include**
- Minimal code to satisfy tests
- Error handling + logging
- No policy/sandbox bypass
- Update docs when needed

Run: “Tests: pytest (quick)” + “Lint: ruff check”

## Step 4 — Reviewer (no code changes unless requested)
**Input to Reviewer**
- `agents/reviewer.md`
- The diff / files changed
- Test results

**Reviewer output must include**
- Security review (sandbox + policy)
- Correctness and edge cases
- Suggested improvements
- “Approve / Request changes” decision

## Step 5 — Merge-ready checkpoint (human)
- Update `CHANGELOG.md`
- Ensure CI passes
- Merge or proceed to next work package
