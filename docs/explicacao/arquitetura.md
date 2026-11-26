# Arquitetura do projeto

## Visão geral

O projeto separa duas responsabilidades que costumam se misturar em exemplos de agentes:
**decidir o que recomendar** e **conversar sobre a recomendação**. A primeira é feita por modelos
de recomendação clássicos, determinísticos e testáveis. A segunda é feita por agentes CrewAI
movidos a LLM, que orquestram as chamadas e redigem o plano.

```text
        ┌──────────── CLI (main.py) ────────────┐   ┌──────── Streamlit (app.py) ────────┐
        │ opções → DinnerRequest · --dataset    │   │ texto livre → intake.py → Request  │
        └───────────────────┬───────────────────┘   └─────────────────┬──────────────────┘
                            └──────────────┬────────────────────────────┘
                                           ▼
                         pipeline.py (Recommenders por base · run · summarize · render)
                          │ modo sem IA: resumo + plano por template
                          │ modo com IA: kickoff(inputs) ▼
 ┌──────────────────────────── Crew (crew.py, processo sequencial) ─────────────────────────────┐
 │ Food Sommelier ─▶ Wine Sommelier ─▶ Concierge ─▶ Anfitrião (sem tool) ─▶ plano em markdown    │
 │      │ tool            │ tool            │ tool        ▲ context das três tarefas             │
 └──────┼─────────────────┼─────────────────┼─────────────────────────────────────────────────────┘
        ▼                 ▼                 ▼
   LightFM           implicit ALS     Surprise KNNWithMeans                      (recommenders/)
        │                 │                 │
   dishes · user_profiles · dish_likes · wines · wine_orders · restaurants · ratings
        data/ (toy, à mão)   ou   data/large/ (gerada por scripts/generate_large_data.py)
```

## Dois pontos de entrada, um pipeline

A CLI (`main.py`) e a interface Streamlit (`app.py`) não têm lógica própria de recomendação:
ambas montam um `DinnerRequest` e chamam `pipeline.py`. A diferença está só em como o pedido
chega — opções de linha de comando ou texto livre interpretado por `intake.py` — e em como a
resposta sai. O parser do chat é baseado em regras, não em LLM, para que a interface funcione
offline e de forma previsível; o LLM entra apenas no modo "Com IA", redigindo o plano.

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

## Por que um quarto agente, o Anfitrião

Numa primeira versão, o Concierge recomendava o restaurante **e** redigia o plano final. Separar
essas funções tem duas vantagens. Cada especialista fica com um só trabalho (chamar sua tool e
justificar o resultado), o que deixa os prompts curtos e as saídas mais fiéis. E a redação final
ganha um agente cujo único objetivo é escrever bem — um parágrafo caloroso com preços e o custo de
prato + vinho — sem acesso a nenhuma tool, portanto sem como "buscar" algo novo: ele só pode
reorganizar o que os especialistas entregaram, e o prompt proíbe acrescentar itens, ingredientes ou
preços.

O modo sem IA tem um equivalente: `pipeline.summarize()`, um template que produz o mesmo tipo de
resumo a partir dos dados das três recomendações.

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

Não há modelo salvo em disco: cada processo treina os três modelos ao iniciar (≈0,1 s na base toy,
≈2 s na large, quase tudo no LightFM). Isso mantém o fluxo "edite o CSV, rode de novo" sem um passo de
re-treino ou cache para invalidar. Dentro de um processo, o cache por base em
`tools/recommender_tools.py` (e o `st.cache_resource` na interface) garante que cada modelo treine
uma só vez por base, mesmo que o agente chame a tool várias vezes.

## Duas bases de dados

A base `toy` existe para ler: dá para conferir cada recomendação à mão, e é nela que estão os
exemplos da documentação e a maioria dos testes. A base `large` existe para ver os modelos
trabalharem com volume — 1.500 usuários, ~37 mil notas — e é gerada por um script com semente fixa,
não escrita à mão. Um teste garante que os CSVs commitados são exatamente a saída do script, então
a base grande é reproduzível e revisável pelo código que a gera. Todos os módulos leem a base a
partir de `dataset_dir()`, que segue `--dataset`, o seletor da interface ou `DINNER_DATASET`.

Num sistema real, com milhões de interações, o treino seria um job separado e os modelos seriam
carregados de um artefato versionado.

## Import tardio do CrewAI

`main.py` importa `dinner_crew.crew` (e, com ele, o CrewAI) só depois de validar entradas e
decidir que a crew vai rodar. O import do CrewAI leva alguns segundos; sem isso, um `--dry-run` ou
um erro de digitação em `--price` pagariam esse custo à toa.

## Observabilidade

Agentes de LLM são difíceis de depurar olhando só a saída final: o plano pode estar errado porque
uma tool devolveu outra coisa, porque um agente leu mal o `context` ou porque o LLM ignorou uma
instrução. Por isso cada execução da crew pode ser registrada no Langfuse, um servidor de tracing
que roda localmente via Docker Compose.

A instrumentação é feita por bibliotecas OpenInference, sem espalhar código de tracing pela
aplicação: uma instrumenta o CrewAI (agentes, tarefas, tools) e outra a SDK da OpenAI (cada chamada
ao modelo, com tokens e custo). `observability.kickoff_traced` só acrescenta um span raiz com o
pedido, o usuário, a sessão do chat e tags. Os recomendadores não aparecem como chamadas de LLM
porque não usam LLM; aparecem como chamadas de tool, com a entrada e o JSON devolvido.

O tracing é opcional por desenho: sem chaves, não liga; com o Langfuse fora do ar, a aplicação
avisa e segue, tentando reconectar a cada 30 s. Assim, os testes continuam offline e a interface
não depende da ordem em que os containers sobem.

## Limitações conhecidas

- Os dados são sintéticos: a base toy foi escrita à mão e a large foi gerada a partir de perfis de
  gosto e regras de harmonização. Os modelos "funcionam" porque os dados foram desenhados com
  estrutura para eles aprenderem; ainda não há avaliação offline (precision@k, RMSE), que a base
  large já permitiria fazer.
- O LightFM recomenda pratos que o usuário já curtiu. Para um jantar isso é aceitável; num catálogo
  real, normalmente se filtrariam os itens já consumidos.
- O filtro de cidade é por igualdade exata de texto.

Detalhes de cada modelo: [Sobre os sistemas de recomendação](sistemas-de-recomendacao.md).
