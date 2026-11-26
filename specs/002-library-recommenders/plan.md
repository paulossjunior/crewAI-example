# Implementation Plan: Library-Backed Recommender Tools

**Branch**: `002-library-recommenders` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

## Summary

Replace the three hand-written recommenders with library-backed ones (LightFM, implicit, Surprise),
one per agent, keeping the crew, CLI and output contract of 001.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: crewai, rectools-lightfm (LightFM API), implicit, scikit-surprise, numpy, scipy

**Storage**: local CSV in `data/`

**Testing**: pytest, offline

**Project Type**: CLI + library

**Constraints**: deterministic (seeds, `num_threads=1`); LightFM fork because upstream 1.17 fails to build on 3.12

## Research / Decisions

| Decision | Rationale | Alternatives |
|---|---|---|
| LightFM → dishes | hybrid model handles cold start via user features built from `--prefs` | LightFM for restaurants (no item features needed there) |
| implicit ALS → wines, dish as "user" | order counts are implicit feedback; dish factors find wines ordered with similar dishes; `similar_users` explains | BPR (less stable on tiny data) |
| Surprise KNNWithMeans user-based Pearson → restaurants | ratings are explicit 1–5; KNN keeps "similar users" explanation | SVD (better accuracy, opaque explanation) |
| `Dataset.load_from_file` in Surprise | avoids pandas dependency | `load_from_df` |
| `rectools-lightfm` fork | maintained by RecTools team, builds on 3.12 | `lightfm-next` (less known maintainer), patching upstream |

## Constitution Check (v2.0.0)

| Principle | Status |
|---|---|
| I. One agent, one library | ✅ LightFM / implicit / Surprise |
| II. Deterministic, no CrewAI in recommenders | ✅ seeds + single thread |
| III. Local data | ✅ new CSVs in `data/` |
| IV. Simplicity | ✅ hand-written recommenders and pairing rules removed; scikit-learn dropped |
| V. Offline tests, secrets | ✅ |

## Source Changes

```text
data/user_profiles.csv        # new: LightFM user features
data/dish_likes.csv           # new: LightFM interactions
data/wine_orders.csv          # new: implicit feedback
data/pairing_rules.json       # removed
src/dinner_crew/recommenders/
├── food_lightfm.py           # FoodRecommender (LightFM)
├── wine_implicit.py          # WineRecommender (implicit ALS)
└── restaurant_surprise.py    # RestaurantRecommender (Surprise KNN)
# removed: content_based.py, knowledge_based.py, collaborative.py
src/dinner_crew/tools/recommender_tools.py   # renamed tools
src/dinner_crew/config/*.yaml                # agent/task text
src/dinner_crew/main.py                      # --user also feeds food
tests/test_food_lightfm.py, test_wine_implicit.py, test_restaurant_surprise.py
```

Contract: [contracts/recommenders.md](contracts/recommenders.md).
