# Quickstart & Validation: Dinner Pairing Crew

## Prerequisites

- `uv` installed; Python 3.12 (auto-selected via `.python-version`).
- OpenAI API key (only for the full crew run).

## Setup

```bash
uv sync
cp .env.example .env   # then set OPENAI_API_KEY
```

## Validation scenarios

| # | Command | Expected |
|---|---|---|
| V1 | `uv run pytest` | all green, no network, < 10 s (SC-005) |
| V2 | `uv run dinner-crew --prefs "cogumelos,cremoso" --dry-run` | JSON of 3 recommenders; risoto de cogumelos in top dishes (US1) |
| V3 | `uv run dinner-crew --prefs "carne,defumado" --restrictions vegetariano --dry-run` | no meat/fish dish (SC-002) |
| V4 | `uv run dinner-crew --dish "Bife ancho com chimichurri" --price media --dry-run` | tintos encorpados, rules cited (US2) |
| V5 | `uv run dinner-crew --prefs "massa,tomate" --user u9 --dry-run` | restaurant section has popularity-fallback warning (US3) |
| V6 | `OPENAI_API_KEY= uv run dinner-crew --prefs x` | clear error, exit 2 (FR-012) |
| V7 | `uv run dinner-crew --prefs "cogumelos,cremoso,ervas" --user u1` | markdown plan with 3 sections, each naming technique (US4) |
| V8 | run V2 twice and `diff` | identical output (SC-006) |

Interfaces: [contracts/cli.md](contracts/cli.md), [contracts/recommenders.md](contracts/recommenders.md).
