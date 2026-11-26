# Referência da instalação Docker

## Arquivos

| Arquivo | Conteúdo | No git |
|---|---|---|
| `docker-compose.yml` | serviço `app` + `include` da stack do Langfuse | sim |
| `Dockerfile` | imagem da aplicação (multi-stage, `uv`, usuário não-root, healthcheck) | sim |
| `.dockerignore` | exclui `.git`, `.venv`, `.env`, `infra/`, `docs/`, `specs/`, `tests/`, `scripts/` do contexto de build | sim |
| `infra/langfuse/docker-compose.yml` | compose oficial do Langfuse v4.87.0, sem modificações | sim |
| `infra/langfuse/docker-compose.override.yml` | ajustes locais (ver abaixo) | sim |
| `infra/langfuse/.env` | segredos e inicialização do Langfuse, gerados por `scripts/setup_langfuse_env.py` | **não** |
| `.env` | `OPENAI_API_KEY` e chaves `LANGFUSE_*` da aplicação | **não** |

Nome do projeto Compose: `dinner-crew` (containers `dinner-crew-<serviço>-1`).

## Serviços

| Serviço | Imagem | Porta publicada | Healthcheck | Inicia com `up` |
|---|---|---|---|---|
| `app` | `dinner-crew:latest` (build local, `pull_policy: build`) | `127.0.0.1:8501` | `GET /_stcore/health` (no Dockerfile) | sim |
| `langfuse-web` | `docker.langfuse.com/langfuse/langfuse:4.87.0` | `127.0.0.1:3000` | `GET /api/public/health` no hostname do container | sim |
| `langfuse-worker` | `docker.langfuse.com/langfuse/langfuse-worker:4.87.0` | `127.0.0.1:3030` | — | sim |
| `postgres` | `postgres:17` | `127.0.0.1:5432` | `pg_isready` | sim |
| `clickhouse` | `clickhouse/clickhouse-server:26.3.62.3` | `127.0.0.1:8123`, `127.0.0.1:9000` | `GET /ping` | sim |
| `redis` | `redis:7` | `127.0.0.1:6379` | `redis-cli ping` | sim |
| `minio` | `cgr.dev/chainguard/minio` | `127.0.0.1:9090`, `127.0.0.1:9091` | `mc ready local` | sim |
| `langfuse-ai-gateway` | `docker.langfuse.com/langfuse/ai-gateway:4.87.0` | `127.0.0.1:3031` | `GET /health` | só com `--profile gateway` |

Dependências: `app` espera `langfuse-web` ficar `healthy`; `langfuse-web` e `langfuse-worker`
esperam `postgres`, `clickhouse`, `redis` e `minio` ficarem `healthy`.

## Ajustes do override local

| Ajuste | Serviço | Motivo |
|---|---|---|
| portas presas a `127.0.0.1` (`ports: !override`) | `langfuse-web`, `minio`, `langfuse-ai-gateway` | o arquivo oficial publica essas portas em todas as interfaces |
| `TELEMETRY_ENABLED: "false"` | `langfuse-web`, `langfuse-worker` | desliga a telemetria anônima enviada ao Langfuse |
| `healthcheck` | `langfuse-web` | permite que `app` espere o Langfuse; usa o hostname do container porque o Next.js não escuta em `127.0.0.1` |
| `profiles: ["gateway"]` | `langfuse-ai-gateway` | o gateway de IA não é necessário para tracing |

## Volumes

| Volume | Conteúdo |
|---|---|
| `dinner-crew_langfuse_postgres_data` | usuários, projetos, chaves e configurações do Langfuse |
| `dinner-crew_langfuse_clickhouse_data`, `..._clickhouse_logs` | traces e observações |
| `dinner-crew_langfuse_minio_data` | eventos brutos e mídia |
| `dinner-crew_langfuse_redis_data` | filas |

`docker compose down` mantém os volumes; `docker compose down -v` os apaga.

## Variáveis de ambiente da aplicação

| Variável | Onde | Efeito | Padrão |
|---|---|---|---|
| `OPENAI_API_KEY` | `.env` | chave da OpenAI; obrigatória para o modo com IA | — |
| `OPENAI_MODEL` | `.env` | modelo dos quatro agentes | `gpt-4o-mini` |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | `.env` | ativam o tracing; sem elas, nada é enviado | — |
| `LANGFUSE_HOST` | `.env` (local) / `environment` do `app` (compose) | endereço do Langfuse | `http://localhost:3000` (local), `http://langfuse-web:3000` (compose) |
| `DINNER_DATASET` | ambiente | base padrão (`toy` ou `large`) | `toy` |

## Variáveis geradas em `infra/langfuse/.env`

| Grupo | Variáveis |
|---|---|
| versão | `LANGFUSE_IMAGE_TAG` |
| autenticação web | `NEXTAUTH_URL`, `NEXTAUTH_SECRET`, `SALT`, `ENCRYPTION_KEY` |
| bancos e armazenamento | `POSTGRES_PASSWORD`, `DATABASE_URL`, `CLICKHOUSE_PASSWORD`, `REDIS_AUTH`, `MINIO_ROOT_PASSWORD`, `LANGFUSE_S3_*_SECRET_ACCESS_KEY` |
| inicialização sem interface | `LANGFUSE_INIT_ORG_ID`, `LANGFUSE_INIT_ORG_NAME`, `LANGFUSE_INIT_PROJECT_ID`, `LANGFUSE_INIT_PROJECT_NAME`, `LANGFUSE_INIT_PROJECT_PUBLIC_KEY`, `LANGFUSE_INIT_PROJECT_SECRET_KEY`, `LANGFUSE_INIT_USER_EMAIL`, `LANGFUSE_INIT_USER_NAME`, `LANGFUSE_INIT_USER_PASSWORD` |

O script nunca sobrescreve um `infra/langfuse/.env` existente; as chaves do projeto são copiadas
para o `.env` da aplicação só se ele ainda não tiver `LANGFUSE_PUBLIC_KEY`.

## Imagem da aplicação

| Estágio | Base | Faz |
|---|---|---|
| `builder` | `python:3.12-slim-bookworm` + `uv` 0.11.8 + `build-essential` | `uv sync --frozen --no-dev` (compila a LightFM, distribuída só como código-fonte) |
| final | `python:3.12-slim-bookworm` + `libgomp1` | copia `.venv`, `src/`, `data/`; roda como usuário `app`; `streamlit run src/dinner_crew/app.py` na porta 8501 |

Tamanho aproximado: 1,75 GB.
