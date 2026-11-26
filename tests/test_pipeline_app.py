import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from dinner_crew.intake import DinnerRequest
from dinner_crew.pipeline import Recommenders, build_crew_inputs, render_plan, run_recommenders, summarize

APP = str(Path(__file__).resolve().parents[1] / "src" / "dinner_crew" / "app.py")
recs = Recommenders()


def test_render_plan_has_three_sections_and_libraries():
    plan = render_plan(run_recommenders(DinnerRequest(preferences=["massa", "tomate"], user_id="u1"), recs))
    for heading in ("## 🍽️ Prato", "## 🍷 Vinho", "## 📍 Restaurante"):
        assert heading in plan
    for library in ("LightFM", "implicit", "Surprise"):
        assert library in plan
    assert "Spaghetti al pomodoro" in plan
    assert "Osteria del Porto" in plan


def test_strict_restrictions_still_find_a_dish():
    req = DinnerRequest(preferences=["carne"], restrictions=["vegano", "sem_gluten", "sem_lactose"])
    assert run_recommenders(req, recs)["chosen_dish"] == "Ratatouille"


def test_render_plan_without_dish():
    assert "Não encontrei" in render_plan({"chosen_dish": None})


def test_build_crew_inputs():
    inputs = build_crew_inputs(DinnerRequest(preferences=["massa"], user_id="u1"))
    assert json.loads(inputs["preferences_list"]) == ["massa"]
    assert inputs["user_id_json"] == '"u1"'
    assert "1º prato" in inputs["dish_instruction"]


def test_app_offline_chat_flow():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    at.chat_input[0].set_value("quero um prato vegetariano com cogumelos, sou u1").run()
    assert not at.exception
    assert "vegetariano" in at.multiselect(key="restrictions").value
    assert at.selectbox(key="user").value == "u1"
    reply = at.chat_message[-1].markdown[0].value
    assert "Entendi" in reply and "## 🍽️ Prato" in reply and "Surprise" in reply

    at.chat_input[0].set_value("e um vinho mais caro?").run()
    assert at.radio(key="price").value == "alta"
    assert "preço: alta" in at.chat_message[-1].markdown[0].value


def test_toy_summary_mentions_items_and_total():
    req = DinnerRequest(preferences=["massa", "tomate"], user_id="u1")
    text = summarize(run_recommenders(req, recs), req)
    assert "Spaghetti al pomodoro" in text and "Chianti Classico" in text and "Osteria del Porto" in text
    assert "R$ 42" in text and "R$ 181" in text  # dish price and dish + wine total


def test_app_switches_to_large_dataset():
    at = AppTest.from_file(APP, default_timeout=180).run()
    at.radio(key="dataset").set_value("large").run()
    assert not at.exception
    at.chat_input[0].set_value("quero peixe cru, estou em Recife, sou u0100").run()
    assert not at.exception
    assert at.selectbox(key="city").value == "Recife"
    reply = at.chat_message[-1].markdown[0].value
    assert "Resumo do anfitrião" in reply and "Ceviche" in reply
