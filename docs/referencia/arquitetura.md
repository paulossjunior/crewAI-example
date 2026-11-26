# Referência da arquitetura do software

Cinco visões do sistema, do mais geral ao mais detalhado. O porquê das decisões está em
[Arquitetura do projeto](../explicacao/arquitetura.md); o caminho de um pedido real, com números,
em [Anatomia de um pedido](../explicacao/anatomia-de-um-pedido.md).

## 1. Contexto

Quem usa o sistema e com quais sistemas externos ele fala.

```mermaid
flowchart LR
    pessoa(["Usuário"])
    sistema["Dinner Pairing Crew<br/>CLI + interface Streamlit"]
    openai[("OpenAI API<br/>gpt-4o-mini")]
    langfuse[("Langfuse<br/>self-hosted, opcional")]
    dados[("CSVs locais<br/>data/ e data/large/")]

    pessoa -- "pedido em texto livre<br/>ou opções da CLI" --> sistema
    sistema -- "plano de jantar" --> pessoa
    sistema -- "só no modo com IA:<br/>prompts dos 4 agentes" --> openai
    sistema -- "traces: agentes, tools,<br/>tokens e custo" --> langfuse
    sistema -- "treino dos modelos<br/>a cada processo" --> dados
```

| Sistema externo | Quando é usado | Obrigatório |
|---|---|---|
| OpenAI API | modo com IA (CLI sem `--dry-run`, interface em "Com IA") | só para esse modo |
| Langfuse | modo com IA, com `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` definidas | não |

## 2. Componentes

Os módulos de `src/dinner_crew/` e suas dependências. As setas apontam de quem usa para quem é usado.

```mermaid
flowchart TB
    subgraph entrada["Entradas"]
        main["main.py<br/>CLI dinner-crew"]
        app["app.py<br/>interface Streamlit"]
        intake["intake.py<br/>RequestParser, DinnerRequest"]
    end

    pipeline["pipeline.py<br/>Recommenders · run_recommenders<br/>summarize · render_plan · build_crew_inputs"]

    subgraph ia["Modo com IA"]
        crew["crew.py<br/>DinnerCrew (@CrewBase)"]
        yaml["config/agents.yaml<br/>config/tasks.yaml"]
        tools["tools/recommender_tools.py<br/>3 BaseTool"]
        obs["observability.py<br/>kickoff_traced"]
    end

    subgraph rec["recommenders/ — sem CrewAI, sem LLM"]
        food["food_lightfm.py<br/>FoodRecommender"]
        wine["wine_implicit.py<br/>WineRecommender"]
        rest["restaurant_surprise.py<br/>RestaurantRecommender"]
    end

    data["data.py<br/>loaders · dataset_dir()"]
    models["models.py<br/>Item · Recommendation"]

    app --> intake
    main --> pipeline
    app --> pipeline
    main --> obs
    app --> obs
    obs --> crew
    crew --> yaml
    crew --> tools
    tools --> pipeline
    pipeline --> food & wine & rest
    food & wine & rest --> data
    food & wine & rest --> models
```

| Camada | Módulos | Depende de CrewAI | Depende de LLM |
|---|---|---|---|
| Entradas | `main.py`, `app.py`, `intake.py` | só ao rodar a crew (import tardio) | não |
| Pipeline | `pipeline.py` | não | não |
| Modo com IA | `crew.py`, `config/*.yaml`, `tools/`, `observability.py` | sim | sim |
| Recomendadores | `recommenders/*.py` | não | não |
| Dados | `data.py`, `models.py` | não | não |

## 3. Sequência de um pedido no modo com IA

```mermaid
sequenceDiagram
    actor U as Usuário
    participant App as app.py
    participant P as intake + pipeline
    participant C as DinnerCrew
    participant A as Agentes (LLM)
    participant T as Tools
    participant R as Recomendadores
    participant L as Langfuse

    U->>App: "quero massa com tomate, sou u1"
    App->>P: parse → DinnerRequest
    P->>R: run_recommenders (prato escolhido)
    App->>C: kickoff_traced(inputs)
    C-->>L: span raiz dinner-plan
    loop Food Sommelier, Wine Sommelier, Concierge
        C->>A: tarefa + context das anteriores
        A->>T: chamada de ferramenta (args JSON)
        T->>R: recommend(...)
        R-->>T: Recommendation
        T-->>A: JSON com itens, scores e warning
        A-->>C: relatório da tarefa
        C-->>App: task_callback (painel de progresso)
    end
    C->>A: Anfitrião: write_summary com os 3 relatórios
    A-->>C: plano em markdown
    C-->>L: flush (agentes, tools, gerações, tokens, custo)
    C-->>App: CrewOutput.raw
    App-->>U: Entendi + plano
```

No modo sem IA, o fluxo termina no terceiro passo: `pipeline.render_plan` escreve o plano a partir
do resultado de `run_recommenders`, sem crew, sem LLM e sem trace.

## 4. Implantação (Docker Compose)

```mermaid
flowchart LR
    subgraph host["Máquina local — todas as portas em 127.0.0.1"]
        nav(["Navegador"])
        subgraph compose["projeto Compose dinner-crew"]
            app["app<br/>dinner-crew:latest<br/>:8501"]
            web["langfuse-web<br/>:3000"]
            worker["langfuse-worker<br/>:3030"]
            pg[("postgres<br/>:5432")]
            ch[("clickhouse<br/>:8123 · :9000")]
            redis[("redis<br/>:6379")]
            minio[("minio<br/>:9090 · :9091")]
        end
    end
    openai[("OpenAI API")]

    nav --> app
    nav --> web
    app -- "LANGFUSE_HOST=http://langfuse-web:3000" --> web
    app -- "HTTPS" --> openai
    web --> pg & ch & redis & minio
    worker --> pg & ch & redis & minio
```

Serviços, imagens, volumes e variáveis: [Referência da instalação Docker](instalacao-docker.md).

## 5. Dados

Os sete arquivos CSV de cada base e como se relacionam. Colunas completas:
[Referência dos arquivos de dados](dados.md).

```mermaid
erDiagram
    DISH ||--o{ DISH_LIKE : "curtido em"
    USER_PROFILE ||--o{ DISH_LIKE : "curte"
    DISH ||--o{ WINE_ORDER : "pedido com"
    WINE ||--o{ WINE_ORDER : "pedido com"
    RESTAURANT ||--o{ RATING : "avaliado em"
    DISH }o..o{ RESTAURANT : "mesma cuisine"

    DISH {
        string name PK
        string cuisine
        string protein
        string sauce
        string intensity
        list tags
        list suitable_for
        list ingredients
        int price_brl
    }
    USER_PROFILE {
        string user_id PK
        list preferences
    }
    DISH_LIKE {
        string user_id FK
        string dish FK
    }
    WINE {
        string name PK
        string type
        string body
        string price
        string grape
        int price_brl
    }
    WINE_ORDER {
        string dish FK
        string wine FK
        int count
    }
    RESTAURANT {
        string name PK
        string cuisine
        string city
        string neighborhood
        string price
        int avg_ticket_brl
    }
    RATING {
        string user_id
        string restaurant FK
        int rating
    }
```

| Recomendador | Lê |
|---|---|
| LightFM (`FoodRecommender`) | `DISH`, `USER_PROFILE`, `DISH_LIKE` |
| implicit (`WineRecommender`) | `DISH`, `WINE`, `WINE_ORDER` |
| Surprise (`RestaurantRecommender`) | `RESTAURANT`, `RATING` |
