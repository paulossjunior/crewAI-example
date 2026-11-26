# Implementation Plan: Docker Compose Install with Langfuse Monitoring

## Decisions

| Decision | Rationale | Alternatives |
|---|---|---|
| Self-hosted Langfuse (user's choice) | traces stay local; no new external service | Langfuse Cloud |
| Official compose pinned to v4.87.0, unmodified, + `docker-compose.override.yml` | easy upgrades; local hardening is explicit | editing the official file |
| Root compose uses `include:` with the override and `infra/langfuse/.env` | one `docker compose up` for app + Langfuse | separate compose projects |
| Headless init (`LANGFUSE_INIT_*`) | org/project/keys/admin exist on first boot; no manual setup | creating keys in the UI |
| OpenInference instrumentors for CrewAI and OpenAI + root span with `propagate_attributes` | Langfuse-recommended path; agent/task/tool spans and LLM generations | OpenLit; manual spans |
| Lazy setup, retry every 30 s, `flush()` after kickoff | app may start before Langfuse; CLI exits quickly | fail fast / cache failure |
| Multi-stage Dockerfile, uv, non-root user | small runtime image; LightFM sdist needs a compiler only at build | single stage |

## Source Changes

```text
docker-compose.yml, Dockerfile, .dockerignore
infra/langfuse/docker-compose.yml           # official, pinned
infra/langfuse/docker-compose.override.yml  # localhost ports, telemetry off, healthcheck, gateway profile
scripts/setup_langfuse_env.py               # secrets + app keys
src/dinner_crew/observability.py            # setup_tracing, kickoff_traced
src/dinner_crew/main.py, app.py             # crew runs go through kickoff_traced
tests/test_observability.py
```
