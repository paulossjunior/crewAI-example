from types import SimpleNamespace

from dinner_crew import observability


class FakeCrew:
    def __init__(self):
        self.calls = []

    def kickoff(self, inputs):
        self.calls.append(inputs)
        return SimpleNamespace(raw="plano")


def test_no_keys_runs_crew_without_tracing(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    observability._reset()
    crew = FakeCrew()
    assert observability.setup_tracing() is None
    assert observability.kickoff_traced(crew, {"a": 1}, user_id="u1").raw == "plano"
    assert crew.calls == [{"a": 1}]


def test_unreachable_langfuse_falls_back(monkeypatch, capsys):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setenv("LANGFUSE_HOST", "http://127.0.0.1:9")  # nothing listens on port 9
    observability._reset()
    try:
        assert observability.setup_tracing() is None
        assert "seguindo sem tracing" in capsys.readouterr().err
        assert observability.kickoff_traced(FakeCrew(), {}).raw == "plano"
    finally:
        observability._reset()


def test_failure_is_retried_later(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setenv("LANGFUSE_HOST", "http://127.0.0.1:9")
    observability._reset()
    try:
        assert observability.setup_tracing() is None
        first = observability._state["failed_at"]
        assert observability.setup_tracing() is None  # within RETRY_AFTER_S: no new attempt
        assert observability._state["failed_at"] == first
        monkeypatch.setattr(observability, "RETRY_AFTER_S", 0)
        observability.setup_tracing()
        assert observability._state["failed_at"] != first  # retried
    finally:
        observability._reset()
