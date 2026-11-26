# Feature Specification: Docker Compose Install with Langfuse Monitoring

**Created**: 2026-11-26 · **Status**: Implemented and verified end-to-end

**Input**: "agora instale o langfuse para monitorar" · "coloca na instalação da aplicação .. crie um
docker compose com a aplicação e langfuse"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subir tudo com um comando (P1)

`docker compose up -d --build` sobe a interface Streamlit e um Langfuse local já configurado
(organização, projeto, chaves e usuário admin criados automaticamente).

**Acceptance**: app em http://localhost:8501 e Langfuse em http://localhost:3000, acessíveis só
pela própria máquina.

### User Story 2 - Ver cada execução da crew no Langfuse (P1)

Cada execução no modo "Com IA" (UI) ou da CLI vira um trace: span raiz `dinner-plan` com inputs e
plano final; spans por agente/tarefa/tool; gerações OpenAI com prompts, tokens e custo; usuário,
sessão do chat e tags (`streamlit`/`cli`, base de dados).

### User Story 3 - Tracing nunca atrapalha (P1)

Sem chaves ou com o Langfuse fora do ar, a app funciona igual e avisa uma vez; a UI volta a tentar
conectar a cada 30 s.

## Requirements *(mandatory)*

- **FR-001**: Root `docker-compose.yml` with the app and the official Langfuse services.
- **FR-002**: All published ports bound to 127.0.0.1; Langfuse telemetry disabled; AI gateway off by default.
- **FR-003**: Secrets generated locally by a script, git-ignored.
- **FR-004**: Tracing optional, retried after failures, covered by offline tests.

## Success Criteria *(mandatory)*

- **SC-001**: `docker compose config` validates; full test suite stays offline.
- **SC-002**: One trace per crew run with user/session/tags.
