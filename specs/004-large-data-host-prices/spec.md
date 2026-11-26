# Feature Specification: Large Dataset, Host Agent, Ingredients & Prices

**Created**: 2026-11-26 · **Status**: Implemented

**Input**: "crie uma base de dados grande para cada agente pesquisar" · "crie um novo agente que
reúne as respostas e sumariza com um texto humano. Além disso, coloque os ingredientes e preços em
cada item"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recomendar sobre uma base grande (P1)

O usuário escolhe a base **large** (CLI `--dataset large`, seletor na UI ou `DINNER_DATASET`) e
recebe recomendações vindas de ~170 pratos, ~150 vinhos, ~400 restaurantes em 8 cidades e
1.500 usuários.

**Acceptance**: pedido "peixe cru, Recife, u0100" retorna um ceviche, um branco/espumante leve e um
restaurante de Recife; restrições continuam respeitadas.

### User Story 2 - Resumo humano do anfitrião (P1)

Depois dos três especialistas, um **Anfitrião** reúne as respostas num parágrafo caloroso que
apresenta prato, vinho e restaurante, com preços e custo aproximado de prato + vinho.

**Acceptance**: o plano começa com "## 🗣️ Resumo do anfitrião" e cita apenas itens e preços
vindos das ferramentas — com IA (agente CrewAI) e sem IA (template).

### User Story 3 - Ingredientes e preços em cada item (P1)

Cada prato mostra ingredientes e preço (R$); cada vinho mostra uva e preço da garrafa; cada
restaurante mostra ticket médio por pessoa — inclusive nas alternativas.

### Edge Cases

- Dados esparsos na base large → parte das previsões de restaurante cai para popularidade, com aviso.
- Trocar de base na UI com filtros incompatíveis (usuário/cidade inexistentes) → filtros resetados.

## Requirements *(mandatory)*

- **FR-001**: Two datasets with identical schemas; dataset chosen per run.
- **FR-002**: Large dataset generated deterministically by a committed script; committed CSVs equal its output.
- **FR-003**: Host agent without tools writes the final plan from the three task outputs.
- **FR-004**: Offline mode produces an equivalent summary by template.
- **FR-005**: `dishes.csv` gains `ingredients`, `price_brl`; `wines.csv` gains `grape`, `price_brl`;
  `restaurants.csv` gains `avg_ticket_brl` (both datasets) and recommenders expose them.

## Success Criteria *(mandatory)*

- **SC-001**: Large-dataset models train in under 5 s in total.
- **SC-002**: 100% of plan items show ingredients/grape and a price.
- **SC-003**: Full test suite stays offline and under 30 s.
