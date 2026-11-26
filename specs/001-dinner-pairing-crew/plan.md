# Implementation Plan: Dinner Pairing Crew

**Branch**: `001-dinner-pairing-crew` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-dinner-pairing-crew/spec.md`

## Summary

CLI that builds a dinner plan with a 3-agent CrewAI crew (sequential). Each agent calls one tool
wrapping a pure-Python recommender: dishes via TF-IDF content-based filtering, wines via
rule-based (knowledge-based) pairing, restaurants via user-based collaborative filtering. The
last task composes a markdown plan citing each technique. See [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (`>=3.12,<3.14`, crewai constraint)

**Primary Dependencies**: crewai, scikit-learn, numpy, python-dotenv; dev: pytest

**Storage**: local CSV/JSON in `data/`

**Testing**: pytest (offline, no LLM)

**Target Platform**: macOS/Linux terminal

**Project Type**: CLI + library (single project)

**Performance Goals**: recommenders < 100 ms each; full run < 2 min (LLM-bound)

**Constraints**: deterministic recommenders; only external call = OpenAI

**Scale/Scope**: ~18 dishes, ~15 wines, ~12 restaurants, 8 users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. One agent, one technique | Food=content-based, Wine=knowledge-based, Concierge=CF; each via own tool naming technique | ✅ |
| II. Pure deterministic core | `recommenders/` imports no CrewAI; ties broken by name | ✅ |
| III. Local versioned data | `data/*.csv|json` committed; only OpenAI external | ✅ |
| IV. Didactic simplicity | flat package, 3 recommenders + 3 thin tools + crew + CLI; deps justified below | ✅ |
| V. Tests & secrets | pytest per recommender offline; `.env` ignored, `.env.example` provided | ✅ |

Post-design re-check: ✅ no violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-dinner-pairing-crew/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   └── recommenders.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
pyproject.toml
.python-version
.env.example
data/
├── dishes.csv
├── wines.csv
├── pairing_rules.json
├── restaurants.csv
└── ratings.csv
src/dinner_crew/
├── __init__.py
├── models.py              # Recommendation, Item dataclasses + vocabularies
├── data.py                # loaders for data/
├── recommenders/
│   ├── __init__.py
│   ├── content_based.py   # FoodRecommender
│   ├── knowledge_based.py # WineRecommender
│   └── collaborative.py   # RestaurantRecommender
├── tools/
│   ├── __init__.py
│   └── recommender_tools.py
├── config/
│   ├── agents.yaml
│   └── tasks.yaml
├── crew.py                # @CrewBase DinnerCrew
└── main.py                # argparse CLI, entry point `dinner-crew`
tests/
├── test_content_based.py
├── test_knowledge_based.py
├── test_collaborative.py
├── test_tools.py
└── test_cli.py
```

**Structure Decision**: single project, `src/` layout, packaged with `uv` (hatchling build) so
`uv run dinner-crew` works.

## Complexity Tracking

| Item | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| scikit-learn dependency | TF-IDF + cosine is the didactic content-based core | hand-rolled TF-IDF adds code readers must audit |
| YAML agent/task config | idiomatic CrewAI layout | inline Python strings are less readable for prompts |
