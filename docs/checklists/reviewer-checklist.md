
# Reviewer Checklist (Gate E)

- [ ] Tests added/updated appropriately
- [ ] `pytest` passes locally
- [ ] Lint passes (`ruff check .`)
- [ ] No host command execution (runner only)
- [ ] Policy blocks dangerous commands and metacharacters
- [ ] Path jail enforced (`/sim/**` only)
- [ ] Errors handled cleanly (no stack traces leaked via API)
- [ ] Observability hooks present where required (Langfuse)
- [ ] Docs updated (README/architecture/RFC/Changelog)
