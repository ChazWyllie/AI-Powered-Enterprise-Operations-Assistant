# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-13

### Added

- **WP1 Foundation**: Initial project infrastructure
  - FastAPI application with `/health` endpoint returning `{"status": "ok"}`
  - Pydantic response models for type-safe API contracts
  - Structured logging with Python's logging module
  - `requirements.txt` with FastAPI, uvicorn, pytest, httpx, ruff, openai, langfuse
  - `pyproject.toml` with pytest and ruff configuration
  - `Dockerfile` for API container (Python 3.11-slim, non-root user, health check)
  - `Dockerfile.runner` for sandbox execution container with security hardening
  - `docker-compose.yml` with API and runner services (runner locked down per WP2 spec)
  - GitHub Actions CI workflow with lint, test, and Docker build jobs
  - `.gitignore` for Python projects
  - `.env.example` for environment variable documentation
  - `simulator/fixtures/` directory placeholder for WP2
  - Test suite with 2 passing tests for health endpoint

### Security

- Runner container configured with: `network_mode: none`, `read_only: true`, `cap_drop: ALL`, `no-new-privileges: true`, resource limits

[Unreleased]: https://github.com/ChazWyllie/AI-Powered-Enterprise-Operations-Assistant/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ChazWyllie/AI-Powered-Enterprise-Operations-Assistant/releases/tag/v0.1.0
