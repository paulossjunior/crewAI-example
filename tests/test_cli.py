import json

import pytest

from dinner_crew.main import main


@pytest.fixture
def no_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")  # empty -> treated as missing; .env won't override


def test_missing_key_exits_2(no_key, capsys):
    assert main(["--prefs", "cogumelos"]) == 2
    assert "OPENAI_API_KEY" in capsys.readouterr().err


def test_invalid_price_exits_2():
    with pytest.raises(SystemExit) as exc:
        main(["--price", "carissimo"])
    assert exc.value.code == 2


def test_invalid_restriction_exits_2(capsys):
    assert main(["--restrictions", "paleo"]) == 2
    assert "vegetariano" in capsys.readouterr().err


def test_unknown_dish_exits_2():
    assert main(["--dish", "Pizza de abacaxi"]) == 2


def test_dry_run_runs_three_recommenders_without_llm(no_key, capsys):
    assert main(["--prefs", "cogumelos,cremoso", "--user", "u1", "--dry-run"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["food"]["library"] == "lightfm"
    assert out["wine"]["library"] == "implicit"
    assert out["restaurant"]["library"] == "surprise"
    assert out["chosen_dish"] == out["food"]["items"][0]["name"]


def test_dry_run_pinned_dish(capsys):
    assert main(["--dish", "Bife ancho com chimichurri", "--dry-run"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["chosen_dish"] == "Bife ancho com chimichurri"
    assert out["restaurant"]["items"][0]["name"] == "Parrilla Buenos Aires"


def test_crew_builds_without_kickoff(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")
    from dinner_crew.crew import DinnerCrew

    crew = DinnerCrew().crew()
    assert len(crew.agents) == 4
    assert [t.agent.role for t in crew.tasks][-1] == "Anfitrião do Jantar"
    tool_names = [a.tools[0].name if a.tools else None for a in crew.agents]
    assert tool_names == [
        "food_lightfm_recommender",
        "wine_implicit_recommender",
        "restaurant_surprise_recommender",
        None,  # the host has no tool
    ]
