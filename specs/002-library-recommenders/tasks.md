# Tasks: Library-Backed Recommender Tools

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/recommenders.md](contracts/recommenders.md)

**Tests**: included (constitution V).

## Phase 1: Setup

- [X] T001 Add deps `rectools-lightfm`, `implicit`, `scikit-surprise`; drop `scikit-learn` in `pyproject.toml`
- [X] T002 Add `library` field to `Recommendation` in `src/dinner_crew/models.py`; add loaders for new CSVs and remove `load_rules` in `src/dinner_crew/data.py`

## Phase 2: User Story 1 - Prato via LightFM (P1) 🎯 MVP

- [X] T003 [P] [US1] Create `data/user_profiles.csv` (u1–u8 preference terms) and `data/dish_likes.csv` (≈4 likes per user, consistent with profiles)
- [X] T004 [P] [US1] Tests in `tests/test_food_lightfm.py` (mushroom prefs → mushroom dish in top-3; vegan filter; popularity fallback; determinism; known user personalization)
- [X] T005 [US1] Implement `FoodRecommender` in `src/dinner_crew/recommenders/food_lightfm.py`

## Phase 3: User Story 2 - Vinho via implicit (P2)

- [X] T006 [P] [US2] Create `data/wine_orders.csv` (3 wines per dish with counts); delete `data/pairing_rules.json`
- [X] T007 [P] [US2] Tests in `tests/test_wine_implicit.py` (Bife → tinto encorpado first; price tier respected; relaxation with synthetic wines; unknown dish error; determinism)
- [X] T008 [US2] Implement `WineRecommender` in `src/dinner_crew/recommenders/wine_implicit.py`

## Phase 4: User Story 3 - Restaurante via Surprise (P3)

- [X] T009 [P] [US3] Tests in `tests/test_restaurant_surprise.py` (u1 italiana SP → Osteria first, unrated only, neighbors cited; unknown user fallback; other-city fallback; 1–5 range; determinism)
- [X] T010 [US3] Implement `RestaurantRecommender` in `src/dinner_crew/recommenders/restaurant_surprise.py`

## Phase 5: Integration (tools, crew, CLI)

- [X] T011 Rewrite tools per contract in `src/dinner_crew/tools/recommender_tools.py`; update `tests/test_tools.py`
- [X] T012 [P] Update agent/task text in `src/dinner_crew/config/agents.yaml` and `src/dinner_crew/config/tasks.yaml`
- [X] T013 Update `src/dinner_crew/main.py` (new recommenders, `--user` feeds food) and `tests/test_cli.py`
- [X] T014 Remove old modules `content_based.py`, `knowledge_based.py`, `collaborative.py` and their tests

## Phase 6: Polish

- [X] T015 [P] Update `README.md` (libraries table, LightFM fork note)
- [X] T016 Run full suite + dry-run validation

## Dependencies

T001–T002 → US1, US2, US3 (independent) → T011–T014 → T015–T016.
