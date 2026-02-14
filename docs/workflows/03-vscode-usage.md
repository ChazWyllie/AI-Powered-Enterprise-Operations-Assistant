
# VS Code Usage (How to run this repo iteratively)

## 1) Add this pack to your repo
Copy:
- `.vscode/` folder into repo root
- `docs/workflows/`, `docs/workpackages/`, `docs/checklists/` into your `docs/`

## 2) Use Tasks
Open Command Palette → **Tasks: Run Task**
Recommended:
- “Python: Install deps”
- “Tests: pytest (quick)”
- “Docker: compose up (build)”
- “Sandbox: runner checks”

## 3) Agentic loop inside VS Code
When you start a new work package:
1. Create RFC: run task “Work Package: Start new RFC”
2. Run Planner using: `agents/planner.md` + appropriate prompt template
3. Add failing tests in `/tests`
4. Run Implementer using: `agents/implementer.md`
5. Run Reviewer using: `agents/reviewer.md`
6. Update changelog and move to next work package
