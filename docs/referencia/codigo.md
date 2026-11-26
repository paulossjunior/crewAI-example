# Referência do código

Pacote `dinner_crew` em `src/dinner_crew/`.

```text
src/dinner_crew/
├── models.py                       vocabulários, Item, Recommendation
├── intake.py                       DinnerRequest, RequestParser (texto livre → pedido)
├── pipeline.py                     Recommenders, run_recommenders, render_plan, build_crew_inputs
├── app.py                          interface Streamlit
├── data.py                         leitura de data/
├── recommenders/
│   ├── food_lightfm.py             FoodRecommender        (LightFM)
│   ├── wine_implicit.py            WineRecommender        (implicit)
│   └── restaurant_surprise.py      RestaurantRecommender  (Surprise)
├── tools/recommender_tools.py      3 tools CrewAI
├── config/agents.yaml              4 agentes (3 especialistas + Anfitrião)
├── config/tasks.yaml               4 tarefas
├── crew.py                         DinnerCrew, build_llm
├── observability.py                tracing opcional no Langfuse
└── main.py                         CLI
```

Os módulos em `recommenders/` não importam `crewai`.

**Atributos expostos nos itens:** pratos — `cuisine`, `protein`, `sauce`, `intensity`,
`ingredients`, `price_brl`; vinhos — `type`, `body`, `price`, `notes`, `grape`, `price_brl`;
restaurantes — `cuisine`, `city`, `neighborhood`, `price`, `avg_ticket_brl`.

---

## `dinner_crew.models`

[models.py](../../src/dinner_crew/models.py)

### Constantes

`PROTEINS`, `SAUCES`, `INTENSITIES`, `PRICES`, `RESTRICTIONS`, `WINE_TYPES`, `WINE_BODIES` —
tuplas com os vocabulários (valores em [Referência dos dados](dados.md#vocabulários)). `PRICES` é
ordenada; o índice representa o nível de preço.

`MAX_ITEMS = 3` — número máximo de itens em uma `Recommendation`.

### `Item` (dataclass)

| Campo | Tipo | Descrição |
|---|---|---|
| `name` | `str` | nome exato do item nos dados |
| `score` | `float` | pontuação do modelo; só a ordem é comparável entre itens da mesma lista |
| `explanation` | `str` | justificativa em português |
| `attributes` | `dict` | atributos do item (culinária, tipo, cidade…) |

### `Recommendation` (dataclass)

| Campo | Tipo | Descrição |
|---|---|---|
| `technique` | `str` | `"hybrid"`, `"implicit-feedback-als"` ou `"explicit-rating-knn"` |
| `library` | `str` | `"lightfm"`, `"implicit"` ou `"surprise"` |
| `items` | `list[Item]` | ordenados por score decrescente, empate por nome; truncados em `MAX_ITEMS` |
| `warning` | `str \| None` | aviso de fallback, relaxamento de filtro ou sinal fraco |

Métodos: `to_dict() -> dict`, `to_json() -> str` (UTF-8, `indent=2`).

---

## `dinner_crew.data`

[data.py](../../src/dinner_crew/data.py)

`DATA_DIR` — `Path` para `data/` na raiz do repositório.

`DATASETS` — `{"toy": data/, "large": data/large/}`.

`dataset_dir(name=None) -> Path` — pasta da base `name`; sem nome, usa `$DINNER_DATASET` e depois
`"toy"`. `ValueError` para nome desconhecido.

Todas as funções de carga aceitam `data_dir: Path | None = None` (padrão `dataset_dir()`).

| Função | Retorno | Conversões |
|---|---|---|
| `load_dishes()` | `list[dict]` | `tags`, `suitable_for`, `ingredients` → `list[str]`; `price_brl` → `int` |
| `load_wines()` | `list[dict]` | `price_brl` → `int` |
| `load_user_profiles()` | `dict[str, list[str]]` | `user_id` → termos |
| `load_dish_likes()` | `list[dict]` | — |
| `load_wine_orders()` | `list[dict]` | `count` → `int` |
| `load_restaurants()` | `list[dict]` | `avg_ticket_brl` → `int` |
| `load_ratings()` | `list[dict]` | `rating` → `int` |

---

## `dinner_crew.recommenders.food_lightfm`

[food_lightfm.py](../../src/dinner_crew/recommenders/food_lightfm.py) · `TECHNIQUE = "hybrid"` ·
`LIBRARY = "lightfm"`

### `normalize(term: str) -> str`

Remove acentos, converte para minúsculas, troca espaços por `_`. Ex.: `"Camarão"` → `"camarao"`.

### `dish_terms(dish: dict) -> list[str]`

Termos normalizados de um prato: `cuisine`, `protein`, `sauce`, `intensity` e `tags`.

### `class FoodRecommender`

```python
FoodRecommender(dishes=None, profiles=None, likes=None, epochs=150, seed=42, data_dir=None)
```

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `dishes`, `profiles`, `likes` | lidos de `data_dir` | dados de treino (injeção para testes) |
| `data_dir` | `dataset_dir()` | base usada para o que não foi injetado |
| `epochs` | `150` | épocas de treino |
| `seed` | `42` | `random_state` do LightFM |

Treino no construtor:

- **features de usuário:** identidade do usuário + `pref:<termo>` para cada termo do perfil;
- **features de item:** identidade do prato + `attr:<termo>` para cada termo de `dish_terms`;
- **interações:** `dish_likes.csv`;
- **modelo:** `LightFM(no_components=16, loss="warp", learning_rate=0.05)`, `num_threads=1`.

Atributos públicos: `dishes`, `model`, `dataset`, `user_features`, `item_features`,
`like_counts` (`Counter` de curtidas por prato).

#### `recommend(preferences, restrictions=None, user_id=None, k=3) -> Recommendation`

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `preferences` | `list[str]` | termos de preferência; desconhecidos são ignorados |
| `restrictions` | `list[str] \| None` | o prato precisa ter todas em `suitable_for` |
| `user_id` | `str \| None` | se conhecido, a identidade entra no vetor do usuário |
| `k` | `int` | máximo de itens |

Comportamento:

| Situação | Resultado | `warning` |
|---|---|---|
| nenhum prato atende às restrições | `items=[]` | `Nenhum prato atende às restrições informadas.` |
| nenhum termo reconhecido e usuário desconhecido | top-k por número de curtidas | `Preferências não reconhecidas e usuário desconhecido: ranking por popularidade.` |
| caso normal | top-k por `model.predict` com vetor de usuário montado na hora | `None` |

O vetor do usuário na predição tem peso `1/n` em cada uma das `n` features ativas.

---

## `dinner_crew.recommenders.wine_implicit`

[wine_implicit.py](../../src/dinner_crew/recommenders/wine_implicit.py) ·
`TECHNIQUE = "implicit-feedback-als"` · `LIBRARY = "implicit"`

Constantes: `MIN_RELATIVE_SCORE = 0.3`, `WEAK_SIGNAL = 0.2`.

### `class WineRecommender`

```python
WineRecommender(dishes=None, wines=None, orders=None, factors=8, seed=42, data_dir=None)
```

Treino no construtor: matriz esparsa prato×vinho com `count` como valor;
`AlternatingLeastSquares(factors=8, regularization=0.05, alpha=2.0, iterations=30, num_threads=1)`.
O prato ocupa o papel de "usuário" da biblioteca.

Atributos públicos: `dishes`, `wines`, `orders` (`csr_matrix`), `model`.

#### `similar_dishes(dish: int, n=2) -> list[str]`

Nomes dos `n` pratos com fatores latentes mais próximos (`model.similar_users`), excluindo o próprio.

#### `recommend(dish_name, price="media", k=3) -> Recommendation`

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `dish_name` | `str` | nome exato do prato |
| `price` | `str` | faixa de `PRICES` |
| `k` | `int` | máximo de itens |

Exceções: `ValueError` se o prato é desconhecido ou a faixa é inválida.

Comportamento:

1. Candidatos = vinhos da faixa `price`. Se vazia, faixas à distância 1, depois 2;
   `warning`: `Nenhum vinho na faixa '<price>'; faixa de preço relaxada.`
2. Score de cada candidato via `model.recommend(..., filter_already_liked_items=False, items=candidatos)`.
3. Mantém itens com `score > 0` e `score ≥ MIN_RELATIVE_SCORE × melhor`; mínimo de 1 item.
4. Se melhor score `< WEAK_SIGNAL`, acrescenta ao `warning`:
   `Sinal fraco (score X): nenhum vinho desta faixa costuma ser pedido com pratos parecidos.`

A explicação de cada item inclui quantas vezes o vinho foi pedido com o prato e os pratos
similares.

---

## `dinner_crew.recommenders.restaurant_surprise`

[restaurant_surprise.py](../../src/dinner_crew/recommenders/restaurant_surprise.py) ·
`TECHNIQUE = "explicit-rating-knn"` · `LIBRARY = "surprise"`

### `class RestaurantRecommender`

```python
RestaurantRecommender(data_dir=None, neighbors=3)
```

Treino no construtor: `ratings.csv` lido com `Dataset.load_from_file` (escala 1–5);
`KNNWithMeans(k=neighbors, sim_options={"name": "pearson", "user_based": True, "min_support": 3})`.
`MIN_SUPPORT = 3`: similaridades calculadas com menos de 3 restaurantes em comum valem 0.

Atributos públicos: `restaurants`, `trainset`, `algo`, `rated` (`dict[user, set[restaurante]]`),
`own_rating` (`dict[(user, restaurante), nota]`), `item_mean` (`dict[restaurante, média]`).

#### `recommend(cuisine, city, user_id=None, k=3) -> Recommendation`

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `cuisine` | `str` | igual a `restaurants.csv.cuisine` |
| `city` | `str` | igual a `restaurants.csv.city` |
| `user_id` | `str \| None` | usuário com notas em `ratings.csv` |
| `k` | `int` | máximo de itens |

Seleção de candidatos, em ordem:

| Etapa | Candidatos | `warning` acrescentado |
|---|---|---|
| 1 | culinária + cidade, ainda não avaliados pelo usuário | — |
| 2 | culinária + cidade, incluindo avaliados | `Você já avaliou todos os restaurantes '<cuisine>' em <city>; sugerindo revisitar.` |
| 3 | culinária em qualquer cidade, não avaliados | `Nenhum restaurante '<cuisine>' em <city>; sugerindo de outras cidades.` |
| — | nenhum | `items=[]`, `Nenhum restaurante '<cuisine>' disponível.` |

Score de cada candidato:

| Caso | Score | Explicação |
|---|---|---|
| já avaliado pelo usuário | a própria nota | `Você mesmo já deu nota N...` |
| usuário conhecido e há vizinhos com Pearson > 0 que avaliaram | `algo.predict(user, restaurante).est` | lista de vizinhos e similaridades |
| senão, restaurante tem notas | média das notas (popularidade) | `Popularidade: nota média...` |
| senão | `trainset.global_mean` | `Sem avaliações ainda; usando a média global...` |

Os dois últimos casos acrescentam `Fallback por popularidade (<motivo>).` ao `warning`.

---

## `dinner_crew.tools.recommender_tools`

[recommender_tools.py](../../src/dinner_crew/tools/recommender_tools.py)

`recommenders()` devolve um `pipeline.Recommenders` da base em `$DINNER_DATASET`, treinado uma vez
por base e processo (cache por base, para a interface poder trocar de base). `food_recommender()`,
`wine_recommender()` e `restaurant_recommender()` devolvem cada modelo dele.

Tools (subclasses de `crewai.tools.BaseTool`); `_run` devolve `Recommendation.to_json()`:

| Classe | `name` | Argumentos |
|---|---|---|
| `FoodLightFMTool` | `food_lightfm_recommender` | `preferences: list[str] = []`, `restrictions: list[str] = []`, `user_id: str \| None = None` |
| `WineImplicitTool` | `wine_implicit_recommender` | `dish_name: str`, `price: str = "media"` |
| `RestaurantSurpriseTool` | `restaurant_surprise_recommender` | `cuisine: str`, `city: str`, `user_id: str \| None = None` |

`WineImplicitTool` captura `ValueError` e devolve `{"error": "<mensagem>"}`.

---

## `dinner_crew.crew`

[crew.py](../../src/dinner_crew/crew.py)

### `build_llm() -> crewai.LLM`

`LLM(model=$OPENAI_MODEL or "gpt-4o-mini", temperature=0)`.

### `class DinnerCrew` (`@CrewBase`)

Lê `config/agents.yaml` e `config/tasks.yaml`.

| Agente (`@agent`) | Tool |
|---|---|
| `food_sommelier` | `FoodLightFMTool` |
| `wine_sommelier` | `WineImplicitTool` |
| `concierge` | `RestaurantSurpriseTool` |
| `host` (Anfitrião) | nenhuma |

| Tarefa (`@task`), em ordem | Agente | `context` |
|---|---|---|
| `recommend_dish` | `food_sommelier` | — |
| `pair_wine` | `wine_sommelier` | `recommend_dish` |
| `recommend_restaurant` | `concierge` | `recommend_dish` |
| `write_summary` | `host` | `recommend_dish`, `pair_wine`, `recommend_restaurant` |

`write_summary` produz a saída final: seções `🗣️ Resumo do anfitrião`, `🍽️ Prato`, `🍷 Vinho` e
`📍 Restaurante`, com ingredientes/uva, preços e uma linha **Recomendador** por seção.

`crew()` devolve `Crew(process=Process.sequential, verbose=False)`.

### Placeholders das configurações YAML

Preenchidos por `main.py` em `kickoff(inputs=...)`:

| Placeholder | Valor |
|---|---|
| `{preferences}`, `{restrictions}` | termos unidos por vírgula, ou `(nenhuma)` |
| `{preferences_list}`, `{restrictions_list}` | listas em JSON |
| `{dish_instruction}` | instrução para escolher o 1º prato ou o prato de `--dish` |
| `{price}`, `{city}` | valores das opções |
| `{user_id}` | id ou `(novo usuário)` |
| `{user_id_json}` | id em JSON ou `null` |

---

## `dinner_crew.intake`

[intake.py](../../src/dinner_crew/intake.py)

### `DinnerRequest` (dataclass)

| Campo | Tipo | Padrão |
|---|---|---|
| `preferences` | `list[str]` | `[]` |
| `restrictions` | `list[str]` | `[]` |
| `price` | `str` | `"media"` |
| `city` | `str` | `"São Paulo"` |
| `user_id` | `str \| None` | `None` |
| `dish` | `str \| None` | `None` (prato fixado) |

### `class RequestParser`

`RequestParser(data_dir=None)` constrói o vocabulário a partir de `user_profiles.csv` (termos),
`restaurants.csv` (cidades) e `dishes.csv` (nomes) da base indicada. Atributo público: `vocab` (`set[str]`, termos normalizados).

#### `parse(text, previous=None) -> ParseResult`

Devolve `ParseResult(request, understood)`: o pedido mesclado sobre `previous` e a lista de
mudanças em português. Regras:

| Detectado | Efeito |
|---|---|
| nome exato de prato (o mais longo que aparecer) | `dish` = prato |
| termos do vocabulário (tolerância singular/plural; ignora `CONTEXT_WORDS`) | substituem `preferences`; soltam `dish` se nenhum prato foi citado |
| `RESTRICTION_PATTERNS` | acrescentados a `restrictions` |
| `PRICE_PATTERNS` (primeiro que casar: baixa, alta, media) | `price` |
| nome de cidade ou `CITY_ALIASES` (`sp`, `rio`, `rj`) | `city` |
| `u<número>` | `user_id` |

`norm(text)` — minúsculas, sem acentos.

---

## `dinner_crew.pipeline`

[pipeline.py](../../src/dinner_crew/pipeline.py)

| Nome | Descrição |
|---|---|
| `Recommenders(dataset="toy")` | treina os três modelos na base indicada; atributos `dataset`, `food`, `wine`, `restaurant`, `dishes` |
| `KNN_NEIGHBORS` | `{"toy": 3, "large": 10}` — `k` do Surprise por base |
| `run_recommenders(req, recs) -> dict` | `{"food", "chosen_dish", "wine", "restaurant"}` (mesmo formato do `--dry-run`); `chosen_dish=None` e `wine`/`restaurant=None` se nenhum prato atende às restrições |
| `summarize(result, req=None) -> str` | versão offline do Anfitrião: parágrafo com prato, vinho, restaurante, preços e total prato + vinho; cita só as preferências que aparecem no prato |
| `render_plan(result, req=None) -> str` | plano em markdown, sem LLM: resumo + seções com ingredientes/uva, preços, alternativas, linha **Recomendador** e avisos |
| `brl(value) -> str` | formata reais: `brl(1250) == "R$ 1.250"` |
| `build_crew_inputs(req) -> dict` | valores dos placeholders dos YAML (ver tabela em `dinner_crew.crew`) |
| `RECOMMENDER_LABELS` | descrição de cada biblioteca usada em `render_plan` |

---

## `dinner_crew.app`

[app.py](../../src/dinner_crew/app.py) — interface Streamlit (`uv run streamlit run src/dinner_crew/app.py`).

| Elemento | Chave em `st.session_state` |
|---|---|
| modo (`Sem IA (offline)` / `Com IA (CrewAI + OpenAI)`) | `mode` |
| base de dados (`toy` / `large`) | `dataset` |
| usuário, cidade, preço, restrições, preferências | `user`, `city`, `price`, `restrictions`, `preferences` |
| prato fixado | `dish` |
| histórico do chat (`role`, `content`, `raw`) | `messages` |
| mensagem enviada | `chat_input` |

Modelos e parser ficam em `st.cache_resource`, um por base. Ao trocar de base, usuário, cidade,
preferências e prato fixado que não existam na nova base são limpos. A mensagem enviada é
processada antes de o painel ser desenhado, para que o pedido interpretado atualize os widgets.

---

## `dinner_crew.observability`

[observability.py](../../src/dinner_crew/observability.py)

| Nome | Descrição |
|---|---|
| `setup_tracing() -> client \| None` | se `LANGFUSE_PUBLIC_KEY` e `LANGFUSE_SECRET_KEY` existem, conecta (`get_client()` + `auth_check()`) e instrumenta CrewAI e OpenAI (OpenInference). Sucesso vale para o processo todo; falha devolve `None`, avisa em stderr e é tentada de novo após `RETRY_AFTER_S` (30 s) |
| `kickoff_traced(crew, inputs, *, user_id=None, session_id=None, tags=None)` | roda `crew.kickoff(inputs=...)`; com tracing ativo, dentro de um span raiz `dinner-plan` (input = inputs, output = plano) com `user_id`, `session_id` e `tags` propagados, e chama `flush()` no fim |

Variáveis: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` (padrão do SDK:
`https://cloud.langfuse.com`; no projeto, `http://localhost:3000` ou `http://langfuse-web:3000`
dentro do compose).

---

## `dinner_crew.main`

[main.py](../../src/dinner_crew/main.py)

| Função | Descrição |
|---|---|
| `parse_args(argv=None) -> Namespace` | define as opções da CLI ([Referência da CLI](cli.md)) |
| `fail(message, code) -> int` | escreve `Erro: <message>` em stderr e devolve `code` |
| `main(argv=None) -> int` | valida entradas, define `DINNER_DATASET` a partir de `--dataset`, monta um `DinnerRequest`, chama `pipeline.run_recommenders`; com `--dry-run` imprime JSON, senão executa a crew com `pipeline.build_crew_inputs` |

`crewai` só é importado dentro de `main()` quando a crew vai rodar (import lento).

---

## Testes

`tests/`, executados com `uv run pytest` (sem rede, sem chave).

| Arquivo | Cobre |
|---|---|
| `test_food_lightfm.py` | rankings, restrições, fallback, usuário conhecido, determinismo |
| `test_wine_implicit.py` | tipo do vinho, faixa de preço, relaxamento, sinal fraco, erro, determinismo |
| `test_restaurant_surprise.py` | vizinhos, fallbacks, revisita, outras cidades, escala 1–5, determinismo |
| `test_tools.py` | nomes, descrições e JSON das tools |
| `test_cli.py` | códigos de saída, `--dry-run`, montagem da crew (4 agentes, Anfitrião sem tool) sem `kickoff` |
| `test_intake.py` | extração de preferências, restrições, preço, cidade, usuário; contexto entre mensagens |
| `test_pipeline_app.py` | plano e resumo por template, inputs da crew, fluxo do chat e troca de base via `streamlit.testing.v1.AppTest` |
| `test_observability.py` | tracing desligado sem chaves, fallback com Langfuse inacessível, nova tentativa após o intervalo |
| `test_large_dataset.py` | base large igual à saída do gerador, tamanhos, integridade referencial, ingredientes/preços, recomendações coerentes |
