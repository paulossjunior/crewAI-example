# Como criar uma nova tool recomendadora para um agente

Este guia cobre trocar o recomendador de um agente existente ou dar a um novo agente sua própria
tool. O padrão do projeto tem três camadas: **recomendador** (Python, sem CrewAI) → **tool**
(adapter CrewAI) → **agente/tarefa** (YAML). O porquê está em
[Arquitetura do projeto](../explicacao/arquitetura.md).

A constitution (`.specify/memory/constitution.md`) exige uma biblioteca distinta por agente. Se a
mudança altera isso, emende a constitution antes — veja
[Como evoluir com o Spec Kit](como-evoluir-com-spec-kit.md).

## 1. Escreva o recomendador

Crie `src/dinner_crew/recommenders/<nome>.py` com uma classe que:

- treina o modelo no `__init__` com **semente fixa** e **uma thread** (determinismo);
- expõe `recommend(...)` devolvendo `Recommendation` (de `dinner_crew.models`);
- não importa nada de `crewai`.

```python
from dinner_crew.models import Item, Recommendation

TECHNIQUE = "item-based-knn"
LIBRARY = "surprise"


class DessertRecommender:
    def __init__(self, seed: int = 42) -> None:
        ...  # carregar data/, treinar modelo

    def recommend(self, dish_name: str, k: int = 3) -> Recommendation:
        ...
        return Recommendation(TECHNIQUE, LIBRARY, items, warning=None)
```

Use `warning` sempre que houver fallback ou relaxamento de filtro: o agente repassa o aviso ao
usuário.

## 2. Teste o recomendador

Crie `tests/test_<nome>.py` testando: técnica/biblioteca, um ranking esperado nos dados toy,
fallbacks e determinismo (`recommend(...).to_json()` igual em dois modelos treinados do zero).
Rode `uv run pytest tests/test_<nome>.py`.

## 3. Crie a tool

Primeiro, treine o novo modelo em `pipeline.Recommenders.__init__` (passando `data_dir`, para que ele
respeite a base escolhida). Depois, em `src/dinner_crew/tools/recommender_tools.py`, adicione uma
função que o devolva a partir de `recommenders()` (cacheado por base), um schema pydantic e a classe
da tool:

```python
def dessert_recommender() -> DessertRecommender:
    return recommenders().dessert


class DessertArgs(BaseModel):
    dish_name: str = Field(description="Nome exato do prato principal")


class DessertTool(BaseTool):
    name: str = "dessert_surprise_recommender"
    description: str = "Recomenda até 3 sobremesas com Surprise (KNN item-based). Retorna JSON."
    args_schema: type[BaseModel] = DessertArgs

    def _run(self, dish_name: str) -> str:
        return dessert_recommender().recommend(dish_name).to_json()
```

A `description` é o que o LLM lê para decidir usar a tool: nomeie a biblioteca e diga o que
entra e sai.

## 4. Ligue a tool ao agente

- **Agente novo:** adicione-o em `src/dinner_crew/config/agents.yaml` (`role`, `goal`,
  `backstory` — inclua "NUNCA invente itens fora do resultado da ferramenta") e crie o método
  `@agent` em `src/dinner_crew/crew.py` com `tools=[DessertTool()]`.
- **Agente existente:** troque a tool em `tools=[...]` no método `@agent` correspondente.

## 5. Crie ou ajuste a tarefa

Em `src/dinner_crew/config/tasks.yaml`, a tarefa deve dizer qual tool chamar e com quais
argumentos. Use `context` para receber a saída de tarefas anteriores. A ordem dos métodos `@task`
em `crew.py` define a sequência: a nova tarefa deve vir **antes** de `write_summary`, e
`write_summary` precisa listá-la em `context` (e ganhar uma seção no prompt) para que o Anfitrião
a inclua no plano. Atualize também `pipeline.render_plan`/`summarize` para o modo sem IA.

Se a tarefa usa um placeholder novo (ex.: `{dessert_pref}`), inclua-o no dicionário `inputs` em
`src/dinner_crew/main.py`.

## 6. Atualize o `--dry-run` e os testes da CLI

Acrescente o novo recomendador ao bloco `if args.dry_run:` de `main.py` e o nome da tool à
lista esperada em `tests/test_cli.py::test_crew_builds_without_kickoff` (o último agente, o
Anfitrião, não tem tool).

## 7. Verifique

```bash
uv run pytest
uv run dinner-crew --prefs "..." --dry-run
```
