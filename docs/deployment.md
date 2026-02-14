# Deployment Guide

## Local Development

```bash
# Start backend + sandbox runner
docker compose up -d

# Verify
curl http://localhost:8000/health

# Start frontend dev server
cd frontend && npm run dev
# → http://localhost:3000
```

## Production Deployment

### Backend (Render)

1. Connect your GitHub repo to [Render](https://render.com)
2. The `render.yaml` blueprint auto-configures the service
3. Set secret environment variables in Render dashboard:
   - `OPENAI_API_KEY`
   - `LANGFUSE_PUBLIC_KEY`
   - `LANGFUSE_SECRET_KEY`
4. Deploy — Render builds from `Dockerfile` automatically

### Frontend (Vercel)

1. Connect your GitHub repo to [Vercel](https://vercel.com)
2. Set root directory to `frontend/`
3. Set environment variable:
   - `VITE_API_URL` = `https://api-enterprise-ops.onrender.com`
4. Deploy — Vercel auto-detects Vite and builds

### Alternative: Docker Compose (self-hosted)

```bash
# Production mode (public demo)
docker compose -f docker-compose.prod.yml up -d

# Verify
./scripts/smoke-test.sh http://localhost:8000
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DEMO_MODE` | `local` | `public` = plan_only enforced, rate limits active |
| `ALLOWED_ORIGINS` | `http://localhost:3000,...` | Comma-separated CORS origins |
| `RATE_LIMIT_RPM` | `0` (local), `10` (public) | Max requests per minute per IP |
| `MAX_REQUEST_BYTES` | `2048` | Max request body size in bytes |
| `OPENAI_API_KEY` | — | OpenAI API key for GPT-4 |
| `LANGFUSE_PUBLIC_KEY` | — | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | — | Langfuse secret key |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Langfuse endpoint |

## Smoke Testing

```bash
# Test local
./scripts/smoke-test.sh http://localhost:8000

# Test production
./scripts/smoke-test.sh https://api-enterprise-ops.onrender.com
```

The smoke test validates:
1. `GET /health` → 200
2. `POST /chat` (plan_only) → 200
3. Response structure (answer, plan, actions_taken, audit)
4. Invalid mode → 422
5. Empty message → 422

## Security Checklist (Production)

- [ ] `DEMO_MODE=public` set
- [ ] `ALLOWED_ORIGINS` set to frontend domain only
- [ ] `RATE_LIMIT_RPM=10` set
- [ ] `OPENAI_API_KEY` set as secret (not in code)
- [ ] Runner container **NOT** deployed
- [ ] Smoke test passes
- [ ] CORS tested from frontend domain
