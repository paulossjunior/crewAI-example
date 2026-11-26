# Implementation Plan: Large Dataset, Host Agent, Ingredients & Prices

**Spec**: [spec.md](spec.md) · **Constitution**: 3.0.0 (Principles I and III amended)

## Decisions

| Decision | Rationale | Alternatives |
|---|---|---|
| Keep toy as default, add `data/large/` | docs/tests stay readable and stable | replace toy data |
| Generator script with seed 42, stdlib only | reproducible; committed CSVs checked by a test | random data each run; downloaded datasets (external) |
| Users from 9 taste archetypes; ratings from cuisine affinity + restaurant quality + rater bias | gives CF/hybrid models real structure to learn | uniform random (nothing to learn) |
| Wine orders simulated from the 001 pairing rules + noise, weighted sampling (score²) | reuses domain knowledge; avoids a few popular bottles dominating | top-k by affinity×popularity (caused popularity bias) |
| Surprise `min_support=3`, k=10 on large (`KNN_NEIGHBORS`) | Pearson on 1–2 co-rated items was noise (sim 1.0) | `pearson_baseline` shrinkage |
| Ratings 15–35 per user, 90% in home city | density for user-based KNN (≈74% of items predicted by neighbors) | fewer ratings (most items fell back to popularity) |
| Host = 4th agent, no tool, last task with `context` of all three | separates recommending from writing; mirrors offline `summarize()` | concierge also writing (mixed roles) |
| `dataset_dir()` + `$DINNER_DATASET`; tools cache models per dataset | CLI, tools and UI share one switch; UI can change dataset at runtime | global singleton (stuck on first dataset) |
| Prices as integer BRL columns; categorical `price` kept | filters unchanged; human-friendly display | replace tiers with numbers |

## Source Changes

```text
scripts/generate_large_data.py         # new
data/large/*.csv                       # new (generated)
data/{dishes,wines,restaurants}.csv    # + ingredients/price_brl, grape/price_brl, avg_ticket_brl
src/dinner_crew/data.py                # DATASETS, dataset_dir(), new casts
src/dinner_crew/recommenders/*.py      # data_dir param; new attributes; Surprise min_support
src/dinner_crew/pipeline.py            # Recommenders(dataset), summarize(), prices in render_plan
src/dinner_crew/tools/recommender_tools.py  # models from pipeline, cached per dataset
src/dinner_crew/config/*.yaml, crew.py # host agent + write_summary task; prices in prompts
src/dinner_crew/main.py, app.py, intake.py  # --dataset, UI switch, dataset-aware parser
tests/test_large_dataset.py            # new; crew/app/pipeline tests updated
```
