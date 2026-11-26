# Dinner Pairing Crew 🍽️🍷📍

Toy example of [CrewAI](https://github.com/crewAIInc/crewAI) built with
[GitHub Spec Kit](https://github.com/github/spec-kit) (spec-driven development).

Three agents put together a dinner plan. Each one uses a recommender built on a **different
library**, exposed to it as a CrewAI tool. Each library fits a different kind of feedback data:

| Agent | Recommends | Library | Technique | Data | Code |
|---|---|---|---|---|---|
| Food Sommelier | dish | **LightFM** | hybrid (content + collaborative, WARP loss); new users are represented by their `--prefs` terms, so cold start works | user×dish likes + dish attributes + user preference terms | [food_lightfm.py](src/dinner_crew/recommenders/food_lightfm.py) |
| Wine Sommelier | wine | **implicit** | ALS on implicit feedback; the dish plays the "user", so wines ordered with similar dishes rank high | dish×wine order counts | [wine_implicit.py](src/dinner_crew/recommenders/wine_implicit.py) |
| Concierge | restaurant | **Surprise** | user-based KNNWithMeans (Pearson) on explicit 1–5 ratings | user×restaurant ratings | [restaurant_surprise.py](src/dinner_crew/recommenders/restaurant_surprise.py) |

Pipeline (sequential): dish → wine for that dish → restaurant serving that cuisine → markdown plan.

The recommenders are deterministic (fixed seeds, single thread) and never call the LLM. The LLM
only orchestrates the agents and writes the plan.

> **LightFM note:** upstream `lightfm` 1.17 does not build on Python 3.12, so the project depends
> on [`rectools-lightfm`](https://github.com/feldlime/rectools-lightfm), a maintained fork with the
> same `import lightfm` API.

## Setup

```bash
uv sync                      # Python 3.12 is picked from .python-version
cp .env.example .env         # then set OPENAI_API_KEY (and optionally OPENAI_MODEL)
```

## Usage

```bash
# Full crew (needs OPENAI_API_KEY)
uv run dinner-crew --prefs "cogumelos,cremoso,ervas" --user u1 --price media --city "São Paulo"

# Recommenders only, no LLM: prints the JSON each tool would give the agents
uv run dinner-crew --prefs "cogumelos,cremoso" --user u1 --dry-run

# Pin a dish, add restrictions
uv run dinner-crew --dish "Bife ancho com chimichurri" --dry-run
uv run dinner-crew --prefs "tomate,ervas" --restrictions vegano,sem_gluten --dry-run
```

Options: `--prefs`, `--restrictions` (`vegetariano`, `vegano`, `sem_gluten`, `sem_lactose`),
`--price` (`baixa|media|alta`), `--city`, `--user` (`u1`…`u8`; unknown → popularity fallback),
`--dish`, `--dry-run`. See [contracts/cli.md](specs/001-dinner-pairing-crew/contracts/cli.md).

## Tests

```bash
uv run pytest     # offline, no API key needed
```

## Toy data

[data/](data/): 19 dishes, 16 wines, 13 restaurants; 8 users with preference profiles, dish likes
and restaurant ratings; 57 dish×wine order counts.
Edit them and see how the recommendations change.

## Spec Kit artifacts

- Constitution: [.specify/memory/constitution.md](.specify/memory/constitution.md)
- Feature 001 (crew, CLI, original hand-written recommenders): [specs/001-dinner-pairing-crew/](specs/001-dinner-pairing-crew/)
- Feature 002 (library-backed recommender tools): [specs/002-library-recommenders/](specs/002-library-recommenders/)

The `/speckit-*` skills live in [.claude/skills/](.claude/skills/) (Claude Code integration).
