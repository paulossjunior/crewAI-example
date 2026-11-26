# Referência da CLI `dinner-crew`

Ponto de entrada: `dinner_crew.main:main` (declarado em `pyproject.toml`, `[project.scripts]`).

```text
uv run dinner-crew [--prefs TERMOS] [--restrictions LISTA] [--price {baixa,media,alta}]
                   [--city CIDADE] [--user USER_ID] [--dish NOME] [--dataset {large,toy}]
                   [--dry-run]
```

## Opções

| Opção | Formato | Padrão | Usada por |
|---|---|---|---|
| `--prefs` | termos separados por vírgula: `"cogumelos,cremoso"` | vazio | LightFM (features do usuário) |
| `--restrictions` | separadas por vírgula, de `vegetariano`, `vegano`, `sem_gluten`, `sem_lactose` | vazio | filtro de pratos |
| `--price` | `baixa`, `media` ou `alta` | `media` | filtro de vinhos (implicit) |
| `--city` | nome exato da cidade em `restaurants.csv` | `São Paulo` | filtro de restaurantes (Surprise) |
| `--user` | id de usuário, ex.: `u1` | nenhum | LightFM (identidade) e Surprise (vizinhos) |
| `--dish` | nome exato de um prato em `dishes.csv` | nenhum | fixa o prato; vinho e restaurante usam ele |
| `--dataset` | `toy` ou `large` | `toy` | base de dados; também define `DINNER_DATASET` para as tools da crew |
| `--dry-run` | flag | desligada | roda só os recomendadores e imprime JSON; não usa LLM |

Termos de `--prefs` são normalizados: minúsculas, sem acentos, espaços viram `_`. Termos fora do
vocabulário dos perfis de usuário são ignorados.

## Saída

**Execução completa:** markdown em stdout escrito pelo agente Anfitrião, com as seções
`## 🗣️ Resumo do anfitrião`, `## 🍽️ Prato`, `## 🍷 Vinho` e `## 📍 Restaurante`. Cada item traz
ingredientes ou uva e preço em R$; cada seção termina com uma linha `**Recomendador:**`.

**`--dry-run`:** JSON em stdout:

```json
{
  "food":        { "technique": "hybrid", "library": "lightfm", "items": [...], "warning": null },
  "chosen_dish": "Spaghetti al pomodoro",
  "wine":        { "technique": "implicit-feedback-als", "library": "implicit", "items": [...], "warning": null },
  "restaurant":  { "technique": "explicit-rating-knn", "library": "surprise", "items": [...], "warning": "..." }
}
```

`chosen_dish` é `--dish`, se informado, senão o primeiro item de `food`. Os `attributes` de cada
item incluem `ingredients` e `price_brl` (pratos), `grape` e `price_brl` (vinhos) e
`avg_ticket_brl` (restaurantes). Estrutura de `items` em
[Referência do código › models](codigo.md#dinner_crewmodels).

## Códigos de saída

| Código | Situação | Mensagem (stderr ou stdout) |
|---|---|---|
| `0` | sucesso | — |
| `1` | nenhum prato atende às restrições (e `--dish` não informado) | `Nenhum prato atende às restrições informadas.` (stdout) |
| `2` | `--price` inválido | mensagem padrão do argparse |
| `2` | restrição inválida | `Erro: restrição inválida [...]; use: ...` |
| `2` | `--dish` desconhecido | `Erro: prato desconhecido '...'; opções: ...` |
| `2` | `OPENAI_API_KEY` ausente ou vazia (sem `--dry-run`) | `Erro: defina OPENAI_API_KEY no ambiente ou no arquivo .env.` |

## Variáveis de ambiente

| Variável | Uso | Padrão |
|---|---|---|
| `OPENAI_API_KEY` | chave da OpenAI; obrigatória sem `--dry-run` | — |
| `OPENAI_MODEL` | modelo usado pelos quatro agentes | `gpt-4o-mini` |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` | ativam o tracing da crew no Langfuse ([guia](../guias/como-rodar-com-docker-e-langfuse.md)); sem elas, nada é enviado | — |
| `DINNER_DATASET` | base padrão (`toy` ou `large`) quando `--dataset` não é usado por quem lê os dados | `toy` |

São lidas do ambiente e do arquivo `.env` (via `python-dotenv`); o ambiente tem prioridade.
