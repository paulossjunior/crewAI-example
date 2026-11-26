# Feature Specification: Library-Backed Recommender Tools

**Feature Branch**: `002-library-recommenders`

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "crie tools que são recomendadores .. cada agente deve usar um desses: Surprise, LightFM ou implicit"

Supersedes the recommendation techniques of [001](../001-dinner-pairing-crew/spec.md). The dinner-plan
flow, CLI and output format of 001 stay the same.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prato por modelo híbrido (Priority: P1)

O usuário informa preferências (e opcionalmente seu id). O Food Sommelier recomenda 3 pratos com
um modelo **híbrido** que aprende tanto com curtidas de outros usuários quanto com atributos dos
pratos e termos de preferência — funcionando para usuários novos (só preferências) e conhecidos.

**Independent Test**: preferências "cogumelos, cremoso" retornam ao menos um prato com cogumelos
no top-3; restrições respeitadas; mesma entrada → mesma saída.

**Acceptance Scenarios**:

1. **Given** preferências "cogumelos, cremoso" e usuário novo, **When** pede pratos, **Then** o
   top-3 contém "Risoto de cogumelos" ou "Fettuccine ao funghi".
2. **Given** restrição "vegano", **When** pede pratos, **Then** todos os pratos são veganos.
3. **Given** nenhuma preferência reconhecida e usuário desconhecido, **When** pede pratos, **Then**
   recebe os pratos mais curtidos (popularidade) com aviso.

### User Story 2 - Vinho por feedback implícito (Priority: P2)

O Wine Sommelier recomenda até 3 vinhos para o prato com um modelo de **feedback implícito**
treinado no histórico de pedidos (quantas vezes cada vinho foi pedido com cada prato), dentro da
faixa de preço, explicando quais pratos têm padrão de pedidos parecido.

**Acceptance Scenarios**:

1. **Given** "Bife ancho com chimichurri" e faixa "media", **When** pede vinho, **Then** o 1º é um
   tinto encorpado da faixa média.
2. **Given** faixa sem nenhum vinho, **When** pede vinho, **Then** a faixa é relaxada com aviso.

### User Story 3 - Restaurante por notas explícitas (Priority: P3)

O Concierge recomenda restaurantes da culinária na cidade com **filtragem colaborativa sobre notas
explícitas** (1–5), citando os usuários vizinhos; fallback por popularidade para usuário novo.

**Acceptance Scenarios**:

1. **Given** usuário "u1", italiana, São Paulo, **When** pede restaurante, **Then** recebe só
   restaurantes não avaliados por u1, com "Osteria del Porto" em 1º.
2. **Given** usuário desconhecido, **When** pede restaurante, **Then** recebe fallback por
   popularidade com aviso.

### Edge Cases

- Prato sem histórico de pedidos → não ocorre nos dados toy; prato desconhecido → erro claro.
- Termos de preferência desconhecidos → ignorados.
- Mesma entrada → mesmas recomendações (modelos com semente fixa).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Food Sommelier MUST use a hybrid recommender (LightFM) trained on user×dish likes,
  dish attribute features and user preference-term features.
- **FR-002**: Wine Sommelier MUST use an implicit-feedback recommender (implicit ALS) trained on
  dish×wine order counts, filtering by price tier with relaxation + warning.
- **FR-003**: Concierge MUST use an explicit-rating collaborative recommender (Surprise
  KNNWithMeans, user-based) on user×restaurant ratings, with popularity fallback + warning.
- **FR-004**: Each tool's description and output MUST name its library and technique.
- **FR-005**: Restrictions, determinism, "no invented items" and CLI behavior from 001 remain.
- **FR-006**: Tests MUST run offline without API keys.

### Key Entities

- **UserProfile**: user id + declared preference terms (LightFM user features).
- **DishLike**: user liked dish (LightFM interactions).
- **WineOrder**: dish, wine, count (implicit feedback).
- **Rating**: user, restaurant, 1–5 (Surprise) — unchanged from 001.

## Success Criteria *(mandatory)*

- **SC-001**: 100% of plan sections name the library + technique used.
- **SC-002**: Recommender test suite runs offline in under 15 seconds.
- **SC-003**: Repeated runs with the same input produce identical recommendations.
- **SC-004**: 100% of recommended dishes respect dietary restrictions.

## Assumptions

- LightFM is installed from the `rectools-lightfm` fork (same API, builds on Python 3.12).
- Toy interaction data (likes, orders) is hand-crafted to encode plausible tastes and pairings.
- The 001 knowledge-based pairing rules are retired; pairing knowledge now lives in order history.
