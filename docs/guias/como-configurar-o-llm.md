# Como configurar o LLM

O LLM só é usado na execução completa (sem `--dry-run`). Os recomendadores nunca o chamam.

## Definir a chave

```bash
cp .env.example .env
```

Edite `.env`:

```dotenv
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

O `.env` está no `.gitignore`; nunca o commite. Uma variável já definida no ambiente tem
prioridade sobre o `.env`.

## Trocar o modelo

Mude `OPENAI_MODEL` no `.env` ou só para uma execução:

```bash
OPENAI_MODEL=gpt-4o uv run dinner-crew --prefs "massa" --user u1
```

## Mudar temperatura ou outros parâmetros

Edite `build_llm()` em `src/dinner_crew/crew.py`. O padrão é `temperature=0`, para reduzir a
variação do texto entre execuções (os itens recomendados já são determinísticos).

## Usar outro provedor

O `crewai.LLM` aceita modelos de outros provedores pelo prefixo (ex.: `anthropic/...`), com a
chave do provedor correspondente. Duas coisas mudam além do `OPENAI_MODEL`:

1. a checagem de `OPENAI_API_KEY` em `src/dinner_crew/main.py`;
2. a constitution, que fixa OpenAI como único serviço externo (Princípio III). Emende-a com
   `/speckit-constitution` — veja [Como evoluir com o Spec Kit](como-evoluir-com-spec-kit.md).

## Ver o raciocínio dos agentes

Em `src/dinner_crew/crew.py`, mude `verbose=False` para `verbose=True` no `Crew(...)`. O CrewAI
passa a imprimir cada passo, chamada de tool e resposta.
