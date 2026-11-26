"""Optional Langfuse tracing for the CrewAI crew.

When ``LANGFUSE_PUBLIC_KEY`` and ``LANGFUSE_SECRET_KEY`` are set (and the server in
``LANGFUSE_HOST`` answers), every crew run becomes one Langfuse trace:

- a root ``dinner-plan`` span with the crew inputs and the final plan;
- child spans for each agent, task and tool call (OpenInference CrewAI instrumentation);
- child generations for each OpenAI call, with prompts, tokens and cost (OpenInference OpenAI
  instrumentation).

Without keys, or if Langfuse is unreachable, ``kickoff_traced`` just runs the crew: tracing never
breaks the app, and tests stay offline. The recommenders are not traced; they do not call the LLM.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

RETRY_AFTER_S = 30  # Langfuse may still be booting (docker compose): retry instead of giving up.
_state: dict[str, Any] = {"client": None, "failed_at": None}


def _reset() -> None:
    """Forget the connection state (used by tests)."""
    _state.update(client=None, failed_at=None)


def setup_tracing() -> Any | None:
    """Connect to Langfuse and instrument CrewAI + OpenAI; succeeds at most once per process.

    A failed attempt is retried after ``RETRY_AFTER_S`` seconds, so a long-running UI starts
    tracing as soon as Langfuse becomes reachable.

    Returns:
        The Langfuse client, or ``None`` when tracing is disabled or unavailable.
    """
    if _state["client"] is not None:
        return _state["client"]
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        return None
    if _state["failed_at"] and time.monotonic() - _state["failed_at"] < RETRY_AFTER_S:
        return None
    try:
        from langfuse import get_client
        from openinference.instrumentation.crewai import CrewAIInstrumentor
        from openinference.instrumentation.openai import OpenAIInstrumentor

        client = get_client()
        if not client.auth_check():
            raise RuntimeError("credenciais recusadas")
    except Exception as exc:  # missing server, wrong keys, network errors
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        print(f"Aviso: Langfuse indisponível em {host} ({exc}); seguindo sem tracing.", file=sys.stderr)
        _state["failed_at"] = time.monotonic()
        return None
    # skip_dep_check: the instrumentor's pinned crewai range lags behind crewai releases.
    CrewAIInstrumentor().instrument(skip_dep_check=True)
    OpenAIInstrumentor().instrument()
    _state["client"] = client
    return client


def kickoff_traced(crew, inputs: dict, *, user_id: str | None = None, session_id: str | None = None,
                   tags: list[str] | None = None):
    """Run ``crew.kickoff(inputs=...)`` inside a Langfuse trace when tracing is enabled.

    Args:
        crew: A ``crewai.Crew``.
        inputs: Placeholder values for the YAML configs.
        user_id: Shown as the trace's user (the dinner request's user id).
        session_id: Groups traces of one conversation (the Streamlit chat).
        tags: Free labels, e.g. the entry point and the dataset.

    Returns:
        The ``CrewOutput`` from ``kickoff``.
    """
    client = setup_tracing()
    if client is None:
        return crew.kickoff(inputs=inputs)

    from langfuse import propagate_attributes

    with client.start_as_current_observation(as_type="chain", name="dinner-plan", input=inputs) as span:
        with propagate_attributes(user_id=user_id, session_id=session_id, tags=tags or [],
                                  trace_name="dinner-plan"):
            output = crew.kickoff(inputs=inputs)
        span.update(output=output.raw)
    client.flush()  # short-lived CLI runs would otherwise exit before spans are exported
    return output
