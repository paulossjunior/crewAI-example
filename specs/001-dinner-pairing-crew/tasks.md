---

description: "Task list for Dinner Pairing Crew"
---

# Tasks: Dinner Pairing Crew

**Input**: Design documents from `/specs/001-dinner-pairing-crew/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included — constitution principle V requires pytest tests for every recommender.

**Organization**: Tasks grouped by user story. US4 (P1, full CLI) integrates US1–US3, so it is
sequenced last although P1; US1 alone is the MVP.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4 from spec.md

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create `pyproject.toml` (name `dinner-crew`, `requires-python = ">=3.12,<3.14"`, deps crewai, scikit-learn, numpy, python-dotenv; dev group pytest; hatchling build with `src/dinner_crew`; script `dinner-crew = "dinner_crew.main:main"`) and `.python-version` (`3.12`) per research.md R1
- [X] T002 [P] Create `.env.example` (`OPENAI_API_KEY=`, `OPENAI_MODEL=gpt-4o-mini`) and ensure `.env` is in `.gitignore`
- [X] T003 [P] Create package skeleton `src/dinner_crew/__init__.py`, `src/dinner_crew/recommenders/__init__.py`, `src/dinner_crew/tools/__init__.py`, `tests/__init__.py`
- [X] T004 Run `uv sync` to create lockfile and environment

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T005 Implement vocabularies (data-model.md `Vocabularies`: `protein`, `sauce`, `intensity`, `price` ordered, `restrictions`, wine `type`/`body`) and `Recommendation`/`Item` dataclasses with `to_dict()`/`to_json()` (data-model.md `Recommendation.technique`, `Recommendation.items` max 3, `Recommendation.warning`, `Item.name|score|explanation|attributes`) in `src/dinner_crew/models.py`
- [X] T006 Implement loaders `load_dishes`, `load_wines`, `load_rules`, `load_restaurants`, `load_ratings` (csv/json from `data/`, path resolved relative to repo root, `;`-split for data-model.md `Dish.tags` and `Dish.suitable_for`) in `src/dinner_crew/data.py`

**Checkpoint**: models + loaders ready.

---

## Phase 3: User Story 1 - Recomendar pratos (Priority: P1) 🎯 MVP

**Goal**: top-3 dishes via content-based filtering, respecting restrictions.

**Independent Test**: `uv run pytest tests/test_content_based.py`.

### Tests for User Story 1

- [X] T007 [P] [US1] Tests in `tests/test_content_based.py`: "cogumelos, cremoso" ranks Risoto de cogumelos first; `vegetariano` excludes meat/fish (data-model.md `Dish.suitable_for`); determinism (two calls equal); empty/unknown prefs → catalog order + warning; technique == `content-based`

### Implementation for User Story 1

- [X] T008 [P] [US1] Create `data/dishes.csv` with ~18 dishes across italiana, japonesa, brasileira, francesa, mexicana, árabe, using data-model.md `Dish.protein`, `Dish.sauce`, `Dish.intensity` vocabularies, `Dish.tags`, `Dish.suitable_for`; include "Risoto de cogumelos" and "Bife ancho com chimichurri"
- [X] T009 [US1] Implement `FoodRecommender` (TF-IDF over cuisine+protein+sauce+intensity+tags, cosine vs preference terms, restriction filter, ties by name, explanation lists matched terms) in `src/dinner_crew/recommenders/content_based.py` per research.md R4

**Checkpoint**: US1 tests green.

---

## Phase 4: User Story 2 - Harmonizar vinho (Priority: P2)

**Goal**: up to 3 wines via pairing rules + price tier with relaxation.

**Independent Test**: `uv run pytest tests/test_knowledge_based.py`.

### Tests for User Story 2

- [X] T010 [P] [US2] Tests in `tests/test_knowledge_based.py`: Bife ancho → only tinto encorpado, rules cited; fish dish → no tinto encorpado; price with no match → relaxed + warning (data-model.md `Wine.price` ordering); unknown dish → `ValueError`; technique == `knowledge-based`

### Implementation for User Story 2

- [X] T011 [P] [US2] Create `data/wines.csv` (~15 wines covering data-model.md `Wine.type`, `Wine.body`, `Wine.price`) and `data/pairing_rules.json` (~10 rules, data-model.md `PairingRule.when` keys ⊆ protein/sauce/intensity, `PairingRule.recommend`, `PairingRule.why`)
- [X] T012 [US2] Implement `WineRecommender` (fire rules, specificity-weighted score, price filter, adjacent-tier relaxation, ties by name) in `src/dinner_crew/recommenders/knowledge_based.py` per research.md R5

**Checkpoint**: US2 tests green.

---

## Phase 5: User Story 3 - Restaurante via filtragem colaborativa (Priority: P3)

**Goal**: up to 3 restaurants by predicted rating from similar users.

**Independent Test**: `uv run pytest tests/test_collaborative.py`.

### Tests for User Story 3

- [X] T013 [P] [US3] Tests in `tests/test_collaborative.py`: known user gets only unrated restaurants of cuisine+city sorted by prediction, explanation cites similar users; unknown user → popularity fallback + warning; no restaurant in city → other cities + warning; predictions within data-model.md `Rating.rating` range 1–5; technique == `collaborative-filtering`

### Implementation for User Story 3

- [X] T014 [P] [US3] Create `data/restaurants.csv` (~12 restaurants, cuisines matching dishes, cities São Paulo + Rio de Janeiro, data-model.md `Restaurant.price`) and `data/ratings.csv` (users u1–u8, data-model.md `Rating.rating` int 1–5, unique per user/restaurant, with clear taste clusters)
- [X] T015 [US3] Implement `RestaurantRecommender` (user×item matrix, mean-centered cosine, top-k=3 neighbors, prediction formula, fallbacks, clipping, ties by name) in `src/dinner_crew/recommenders/collaborative.py` per research.md R6

**Checkpoint**: US3 tests green.

---

## Phase 6: User Story 4 - Plano de jantar completo pela CLI (Priority: P1)

**Goal**: one command → 3-agent crew → markdown plan.

**Independent Test**: `uv run pytest tests/test_tools.py tests/test_cli.py` + quickstart V7.

### Tests for User Story 4

- [X] T016 [P] [US4] Tests in `tests/test_tools.py`: each tool `_run` returns valid JSON with correct `technique`; tool names/descriptions match contracts/recommenders.md
- [X] T017 [P] [US4] Tests in `tests/test_cli.py`: missing `OPENAI_API_KEY` → exit 2 + message; invalid price/restriction/dish → exit 2; `--dry-run` prints JSON for 3 recommenders without LLM; crew builds with dummy key (3 agents, 3 tasks) without kickoff

### Implementation for User Story 4

- [X] T018 [US4] Implement three `BaseTool` subclasses with pydantic args schemas per contracts/recommenders.md in `src/dinner_crew/tools/recommender_tools.py`
- [X] T019 [P] [US4] Write agents (food_sommelier, wine_sommelier, concierge; role/goal/backstory naming technique, "never invent items") in `src/dinner_crew/config/agents.yaml`
- [X] T020 [P] [US4] Write tasks (recommend_dish, pair_wine with context dish, recommend_restaurant_and_compose_plan with context both, expected markdown sections per contracts/cli.md) in `src/dinner_crew/config/tasks.yaml`
- [X] T021 [US4] Implement `@CrewBase DinnerCrew` (LLM from env per research.md R3, tools per agent, sequential process) in `src/dinner_crew/crew.py`
- [X] T022 [US4] Implement argparse CLI per contracts/cli.md (validation, `.env` loading, key check, `--dry-run`, no-dish early exit, kickoff with inputs) in `src/dinner_crew/main.py`

**Checkpoint**: full suite green; V7 produces plan.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T023 [P] Write `README.md` (what it is, the three techniques, setup, usage, Spec Kit flow pointer to `specs/001-dinner-pairing-crew/`)
- [X] T024 Run quickstart.md validations V1–V6, V8 and fix issues

---

## Dependencies & Execution Order

- Setup (T001–T004) → Foundational (T005–T006) → US1, US2, US3 (independent of each other) → US4 → Polish.
- Within each story: data + tests [P] → recommender implementation.
- US4 depends on US1–US3 recommenders.

## Parallel Example

```text
After Phase 2:  T007+T008 (US1) | T010+T011 (US2) | T013+T014 (US3)
Then:           T009 | T012 | T015
US4:            T016, T017, T019, T020 in parallel → T018 → T021 → T022
```

## Implementation Strategy

1. MVP = Phase 1–3 (content-based dish recommender, testable offline).
2. Add US2, US3 (each adds one technique, independently testable).
3. US4 wires everything into the CrewAI crew + CLI.
4. Polish: README + quickstart validation.
