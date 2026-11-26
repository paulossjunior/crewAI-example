# Tasks: Large Dataset, Host Agent, Ingredients & Prices

- [X] T001 Amend constitution to 3.0.0 (Host agent; toy + large datasets)
- [X] T002 [US1] Generator `scripts/generate_large_data.py` → `data/large/*.csv`
- [X] T003 [US3] Add ingredients/prices columns to toy CSVs and generator
- [X] T004 [US1] `data.py`: `DATASETS`, `dataset_dir()`, casts for new columns
- [X] T005 [US1][US3] Recommenders accept `data_dir`; expose ingredients/grape/prices; Surprise `min_support`
- [X] T006 [US1] Tune generator (popularity bias, rating density) after evaluating results
- [X] T007 [US2][US3] `pipeline.py`: `Recommenders(dataset)`, `summarize()`, prices in `render_plan`
- [X] T008 [US2] Host agent + `write_summary` task in YAML/`crew.py`; prompts ask for ingredients/prices
- [X] T009 [US1] `--dataset` in CLI, dataset switch in UI, dataset-aware parser and tools
- [X] T010 Tests: `tests/test_large_dataset.py`, summary, UI dataset switch, crew with 4 agents
- [X] T011 Live crew run with OpenAI to validate the host output
- [X] T012 Update `docs/` and README
