
# Agentic Workflow Pack (VS Code)

This folder turns your **agentic engineering plan** into repeatable, phase-gated workflows you can run inside VS Code.

## What you already have (from your templates)
- A strict **phase-based engineering loop** (Requirements → Design → Test-first → Implementation → Review → Release).
- Role separation: Planner / Implementer / Reviewer.
- Prompt templates for Feature / Bugfix / Refactor / Architecture review / Multi-agent orchestration.

## What this pack adds
- A concrete **“how to run it in VS Code”** runbook
- Phase gates + checklists
- Work-package execution docs (WP1 → WP6) aligned to your IBM-targeted project
- `.vscode/tasks.json` shortcuts for common actions

Start here:
1. Read `docs/workflows/01-iteration-loop.md`
2. Pick the next work package in `docs/workpackages/`
3. Use the matching prompt template in `/prompts/` with the role file in `/agents/`
