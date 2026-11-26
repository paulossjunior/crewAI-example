# Arquitetura do projeto

## Visão geral

O projeto separa duas responsabilidades que costumam se misturar em exemplos de agentes:
**decidir o que recomendar** e **conversar sobre a recomendação**. A primeira é feita por modelos
de recomendação clássicos, determinísticos e testáveis. A segunda é feita por agentes CrewAI
movidos a LLM, que orquestram as chamadas e redigem o plano.

```text
                ┌──────────────────────────── CLI (main.py) ────────────────────────────┐
                │  valida entradas · --dry-run chama recomendadores direto · kickoff()  │
                └───────────────────────────────────┬───────────────────────────────────┘
                                                    │ inputs
 ┌──────────────────────────────── Crew (crew.py, processo sequencial) ─────────────────────────────┐
 │                                                                                                   │
 │  Food Sommelier ──context──▶ Wine Sommelier ──context──▶ Concierge ──▶ plano em markdown          │
 │       │ LLM                       │ LLM                       │ LLM                               │
 └───────┼───────────────────────────┼───────────────────────────┼───────────────────────────────────┘
         ▼ tool call                 ▼ tool call                 ▼ tool call
  food_lightfm_recommender   wine_implicit_recommender   restaurant_surprise_recommender   (tools/)
         │                           │                           │
  FoodRecommender             WineRecommender             RestaurantRecommender            (recommenders/)
   LightFM                     implicit ALS                Surprise KNNWithMeans
         │                           │                           │
  dishes · user_profiles      dishes · wines              restaurants · ratings            (data/)
  dish_likes                  wine_orders
```

## As três camadas

**Recomendadores (`recommenders/`)** são classes Python comuns que treinam um modelo no
construtor e respondem a `recommend(...)` com uma `Recommendation`. Não sabem que existe CrewAI.
Isso permite testá-los em milissegundos, sem rede e sem custo, e reutilizá-los em qualquer outro
contexto (um notebook, uma API).

**Tools (`tools/`)** são adapters finos: um schema pydantic que diz ao LLM quais argumentos
existem, uma descrição que diz quando usar a tool, e um `_run` que chama o recomendador e devolve
JSON. Nenhuma lógica de recomendação mora aqui. Se mora, ela escapa dos testes e passa a depender
do LLM para ser exercitada.

**Agentes e tarefas (`config/*.yaml` + `crew.py`)** definem papéis e instruções em linguagem
natural. Ficam em YAML porque são, na prática, prompts: lê-los e ajustá-los é mais fácil fora do
código Python. Essa é também a estrutura que o `crewai create crew` gera, então quem conhece CrewAI
se localiza de imediato.

## Por que processo sequencial com `context`

A dependência entre as etapas é rígida: o vinho depende do prato, o restaurante depende da
culinária do prato. Um processo hierárquico, com um agente gerente decidindo a ordem, acrescentaria
uma chamada de LLM e uma fonte de variação sem nenhum ganho. Com `Process.sequential`, a ordem é a
dos métodos `@task`, e o `context` de cada tarefa entrega ao agente seguinte a saída das anteriores.

A última tarefa acumula duas funções — recomendar o restaurante e compor o plano — para evitar um
quarto agente que só formataria texto.

## Como o LLM é mantido "no chão"

O maior risco de um agente recomendador é inventar itens plausíveis que não existem. Três
mecanismos reduzem isso:

1. **As tools devolvem JSON com nomes exatos**, não texto livre. O agente copia nomes em vez de
   parafraseá-los.
2. **Os backstories proíbem explicitamente** citar itens fora do resultado da tool.
3. **A escolha é delegada ao recomendador**: a tarefa do Food Sommelier pede o 1º prato da lista
   (ou o fixado por `--dish`), em vez de deixar o LLM escolher por gosto.

Nenhum desses mecanismos é uma garantia formal — é por isso que existe o `--dry-run`, que mostra
exatamente o que os recomendadores decidiram, sem LLM no meio.

## Determinismo

Os três modelos usam semente fixa e uma única thread. Treinamento paralelo reordena operações
de ponto flutuante e pode mudar rankings entre execuções; com uma thread e semente fixa, a mesma
entrada produz sempre a mesma saída. Empates são resolvidos pelo nome do item. O custo — treino
mais lento — é irrelevante com dados deste tamanho.

O texto do plano não é determinístico (vem do LLM), mas os itens recomendados são. `temperature=0`
reduz a variação do texto.

## Treinar a cada execução

Não há modelo salvo em disco: cada processo treina os três modelos ao iniciar (menos de um
segundo com os dados toy). Isso mantém o fluxo "edite o CSV, rode de novo" sem um passo de
re-treino ou cache para invalidar. Dentro de um processo, as factories com `@cache` em
`tools/recommender_tools.py` garantem que cada modelo treine uma só vez, mesmo que o agente chame a
tool várias vezes.

Num sistema real, com milhões de interações, o treino seria um job separado e os modelos seriam
carregados de um artefato versionado.

## Import tardio do CrewAI

`main.py` importa `dinner_crew.crew` (e, com ele, o CrewAI) só depois de validar entradas e
decidir que a crew vai rodar. O import do CrewAI leva alguns segundos; sem isso, um `--dry-run` ou
um erro de digitação em `--price` pagariam esse custo à toa.

## Limitações conhecidas

- Os dados são pequenos e foram escritos à mão para codificar gostos plausíveis. Os modelos
  "funcionam" porque os dados foram desenhados para isso; não há avaliação offline (precision@k,
  RMSE) porque não haveria dados suficientes para separar treino e teste de forma significativa.
- O LightFM recomenda pratos que o usuário já curtiu. Para um jantar isso é aceitável; num catálogo
  real, normalmente se filtrariam os itens já consumidos.
- O filtro de cidade é por igualdade exata de texto.

Detalhes de cada modelo: [Sobre os sistemas de recomendação](sistemas-de-recomendacao.md).
