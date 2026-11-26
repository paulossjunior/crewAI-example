# Implementation Plan: Streamlit Chat UI

**Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

## Summary

Streamlit chat page over a shared pipeline. A rule-based parser turns messages into a
`DinnerRequest`; the pipeline runs the three recommenders and renders a template plan (offline) or
hands the request to the CrewAI crew (AI mode).

## Technical Context

**Dependencies**: + `streamlit` (1.67) · **Testing**: pytest + `streamlit.testing.v1.AppTest`

## Decisions

| Decision | Rationale | Alternatives |
|---|---|---|
| Streamlit `st.chat_input` + `st.chat_message` | chat UI in ~150 lines, Python only | AG-UI + CopilotKit (React project); third-party crewai-playground (alpha) |
| Rule-based intake (`intake.py`) | offline, deterministic, testable; works in both modes | LLM extraction (needs key, non-deterministic) |
| `pipeline.py` shared by CLI and UI | one place for run/render/inputs (FR-007) | duplicating logic in `app.py` |
| Parse chat message before drawing sidebar | Streamlit forbids changing widget state after the widget is drawn in the same run | `st.rerun()` round-trip |
| `st.cache_resource` for models/parser | train once per server process | retrain per message |

## Constitution Check (v2.1.0)

All principles ✅. Technology section amended (MINOR) to allow the second entry point with a
mandatory offline mode.

## Source Changes

```text
src/dinner_crew/intake.py     # DinnerRequest, RequestParser
src/dinner_crew/pipeline.py   # Recommenders, run_recommenders, render_plan, build_crew_inputs
src/dinner_crew/app.py        # Streamlit UI
src/dinner_crew/main.py       # now uses pipeline
tests/test_intake.py, tests/test_pipeline_app.py
```
