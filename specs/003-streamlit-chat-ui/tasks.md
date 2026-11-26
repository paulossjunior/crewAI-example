# Tasks: Streamlit Chat UI

- [X] T001 Add `streamlit` dependency in `pyproject.toml`; amend constitution to 2.1.0
- [X] T002 [US1] Rule-based intake `DinnerRequest` / `RequestParser` in `src/dinner_crew/intake.py`
- [X] T003 [P] [US1] Tests in `tests/test_intake.py` (extraction, accents, price words, carne≠caro, follow-up context, dish pin)
- [X] T004 [US1] Shared pipeline in `src/dinner_crew/pipeline.py` (run, render, crew inputs)
- [X] T005 [US1][US2][US3] Streamlit app in `src/dinner_crew/app.py` (chat, sidebar sync, modes, JSON expander)
- [X] T006 [P] Tests in `tests/test_pipeline_app.py` incl. headless `AppTest` chat flow
- [X] T007 Refactor `src/dinner_crew/main.py` onto the pipeline (no behavior change)
- [X] T008 [P] Docs: `docs/guias/como-usar-a-interface.md`, reference + README updates
- [X] T009 Full suite + live `streamlit run` health check
