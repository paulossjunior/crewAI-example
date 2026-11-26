# Como rodar com Docker (aplicação + Langfuse)

Um `docker compose up` sobe a interface Streamlit e um [Langfuse](https://langfuse.com) local, que
registra cada execução da crew: agentes, tarefas, chamadas de tool e chamadas à OpenAI (prompts,
tokens e custo).

## Pré-requisitos

- Docker Desktop (ou Docker Engine) com Compose v2.24+.
- ~10 GB livres em disco: as imagens do Langfuse ocupam alguns GB, mais os dados.
- `uv`, só para rodar o script de configuração.
- Opcional: `OPENAI_API_KEY` no `.env`, para o modo "Com IA" (sem ela, só o modo offline funciona e
  não há traces).

## 1. Gerar segredos e chaves (uma vez)

```bash
uv run python scripts/setup_langfuse_env.py
```

O script cria `infra/langfuse/.env` (senhas dos bancos, chaves de criptografia, organização,
projeto, par de chaves de API e usuário admin) e acrescenta `LANGFUSE_PUBLIC_KEY`,
`LANGFUSE_SECRET_KEY` e `LANGFUSE_HOST` ao `.env` da aplicação. Os dois arquivos ficam fora do git.
Ele imprime o login do Langfuse; depois, consulte-o em `infra/langfuse/.env`
(`LANGFUSE_INIT_USER_EMAIL` / `LANGFUSE_INIT_USER_PASSWORD`).

## 2. Subir

```bash
docker compose up -d --build
```

A aplicação espera o Langfuse ficar saudável (o primeiro boot leva 1–2 min, com as migrações).
Acompanhe com `docker compose ps` ou `docker compose logs -f app langfuse-web`.

| Serviço | Endereço |
|---|---|
| Aplicação | http://localhost:8501 |
| Langfuse | http://localhost:3000 |

Todas as portas escutam só em `127.0.0.1`.

## 3. Ver os traces

1. Na aplicação, escolha **Com IA (CrewAI + OpenAI)** e faça um pedido.
2. No Langfuse, entre com o login do passo 1 e abra o projeto **dinner-crew** → **Tracing**.

Cada execução aparece como um trace `dinner-plan`, com:

- **input**: os placeholders enviados à crew; **output**: o plano final;
- spans dos 4 agentes, das 4 tarefas e das 3 tools de recomendação;
- gerações OpenAI com prompt, resposta, tokens e custo estimado;
- **user** = id do usuário do pedido, **session** = a conversa do chat, **tags** = `streamlit` ou
  `cli` e a base (`toy`/`large`).

## Monitorar a CLI sem Docker para a aplicação

Com o Langfuse rodando (`docker compose up -d langfuse-web langfuse-worker`), a CLI local também
envia traces, usando `LANGFUSE_HOST=http://localhost:3000` do `.env`:

```bash
uv run dinner-crew --prefs "massa,tomate" --user u1
```

## Desligar o tracing

Remova (ou comente) `LANGFUSE_PUBLIC_KEY` e `LANGFUSE_SECRET_KEY` do `.env`. Sem elas, nada é
enviado. Se o Langfuse estiver fora do ar, a aplicação avisa uma vez no log e segue sem tracing,
tentando de novo a cada 30 s.

## Parar e limpar

```bash
docker compose down          # para os containers, mantém os dados
docker compose down -v       # também apaga os volumes (traces, usuários, chaves) — irreversível
```

Para usar o gateway de IA opcional do Langfuse: `docker compose --profile gateway up -d`.
