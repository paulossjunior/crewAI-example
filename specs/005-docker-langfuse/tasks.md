# Tasks: Docker Compose Install with Langfuse Monitoring

- [X] T001 Pin and review official Langfuse compose; add local override (localhost, telemetry off)
- [X] T002 Secrets/keys generator `scripts/setup_langfuse_env.py`
- [X] T003 Add `langfuse`, `openinference-instrumentation-crewai`, `openinference-instrumentation-openai`
- [X] T004 `observability.py` (optional tracing, retry, flush) + tests
- [X] T005 Route CLI and UI crew runs through `kickoff_traced` (user, session, tags)
- [X] T006 `Dockerfile`, `.dockerignore`, root `docker-compose.yml`; validate with `docker compose config`
- [X] T007 Constitution 3.1.0; docs and README
- [ ] T008 `docker compose up -d --build` and check a trace end-to-end (blocked: host disk full, Docker Desktop down)
