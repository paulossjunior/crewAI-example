<!--
Sync Impact Report
- Version change: 1.0.0 → 2.0.0 (MAJOR: Principle I redefined)
- Modified principles:
  - I. One Agent, One Explicit Recommendation Technique → I. One Agent, One Recommender Library
  - II. Pure, Deterministic Recommenders → wording: library-backed recommenders allowed, fixed seeds
  - IV. Didactic Simplicity → recommender libraries listed as sanctioned dependencies
- Added sections: none
- Removed sections: none
- Templates: no template files modified
- Deferred TODOs: none
-->

# Dinner Pairing Crew Constitution

## Core Principles

### I. One Agent, One Recommender Library

Each CrewAI agent MUST be backed by a distinct, established recommender library and technique,
exposed to the agent as a CrewAI tool:

- Food agent → **LightFM** (hybrid content + collaborative, user/item features).
- Wine agent → **implicit** (implicit-feedback ALS over order counts).
- Restaurant agent → **Surprise** (explicit-rating collaborative filtering, KNN).

The library and technique MUST be named in the tool's description and in code docstrings. Agents
MUST obtain recommendations by calling their tool; the LLM MUST NOT invent items absent from the
tool output.

**Rationale**: the project teaches how real recommender libraries, each suited to a different
kind of feedback data, compare when orchestrated by agents.

### II. Pure, Deterministic Recommenders (LLM-Free Core)

Recommender logic MUST live in Python modules with no dependency on CrewAI or an LLM; they may
use the libraries named in Principle I. Given the same input and data, a recommender MUST return
the same ranked output: models use fixed random seeds and a single thread, ties broken by name. CrewAI tools are thin adapters over these modules.

**Rationale**: deterministic cores are easy to test, debug and explain; the LLM only orchestrates
and narrates.

### III. Local Versioned Toy Data

All catalogs and ratings (dishes, wines, pairing rules, restaurants, user ratings) MUST be small
local files (CSV or JSON) committed to the repository. The only external service permitted at
runtime is the OpenAI LLM used by CrewAI. No databases, web scraping or third-party APIs.

**Rationale**: anyone can clone and run the example offline (except the LLM) with reproducible
results.

### IV. Didactic Simplicity

Code MUST stay small and readable: prefer standard library and well-known libraries, flat module
layout, no speculative abstractions (YAGNI). Any added dependency or layer MUST be justified in
the plan's Complexity Tracking table.

**Rationale**: this is a toy example; clarity beats extensibility.

### V. Tested Recommenders & Safe Secrets

- Every recommender MUST have pytest unit tests that run without network access or API keys.
- Tests MUST NOT call the LLM; crew wiring may be smoke-tested with the LLM mocked or skipped.
- Secrets (e.g., `OPENAI_API_KEY`) MUST be loaded from environment / `.env`; `.env` MUST be
  git-ignored and a `.env.example` MUST document required variables.

**Rationale**: fast, free, reliable tests; no credential leaks.

## Technology & Constraints

- Language: Python 3.12+, dependency and environment management with `uv`.
- Orchestration: CrewAI (agents, tasks, tools); LLM provider: OpenAI.
- Recommenders: `lightfm` (via the `rectools-lightfm` fork, since upstream 1.17 does not build on
  Python 3.12), `implicit`, `scikit-surprise`, plus `numpy`/`scipy`.
- Entry point: a single CLI command that takes user preferences and prints the dinner plan.

## Development Workflow

- Features follow Spec Kit flow: specify → (clarify) → plan → tasks → implement.
- Recommender tests are written alongside or before the implementation and MUST pass before the
  crew wiring is considered done.
- Each change MUST keep `uv run pytest` green.

## Governance

This constitution supersedes other project practices. Amendments are made via
`/speckit-constitution`, documented in the Sync Impact Report, and versioned with semantic
versioning: MAJOR for principle removals/redefinitions, MINOR for new principles or materially
expanded guidance, PATCH for clarifications. Every plan MUST include a Constitution Check against
these principles; violations MUST be justified in Complexity Tracking or removed.

**Version**: 2.0.0 | **Ratified**: 2026-11-26 | **Last Amended**: 2026-11-26
