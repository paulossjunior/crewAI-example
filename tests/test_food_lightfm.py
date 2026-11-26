from dinner_crew.data import load_dishes
from dinner_crew.recommenders.food_lightfm import FoodRecommender

rec = FoodRecommender()
DISHES = {d["name"]: d for d in load_dishes()}
MUSHROOM = {"Risoto de cogumelos", "Fettuccine ao funghi"}


def test_new_user_mushroom_prefs():
    result = rec.recommend(["cogumelos", "cremoso"])
    assert (result.technique, result.library) == ("hybrid", "lightfm")
    assert len(result.items) == 3
    assert MUSHROOM & {i.name for i in result.items}
    assert result.warning is None


def test_meat_prefs_rank_red_meat():
    items = rec.recommend(["carne", "grelhado", "churrasco"]).items
    assert sum(DISHES[i.name]["protein"] == "carne_vermelha" for i in items) >= 2


def test_fish_prefs_rank_sushi_first():
    assert rec.recommend(["peixe", "leve"]).items[0].name == "Sushi de salmão"


def test_vegan_restriction():
    for item in rec.recommend(["carne"], restrictions=["vegano"]).items:
        assert "vegano" in DISHES[item.name]["suitable_for"]


def test_unknown_everything_falls_back_to_popularity():
    result = rec.recommend(["xyzzy"])
    assert result.warning and "popularidade" in result.warning
    assert len(result.items) == 3


def test_known_user_without_prefs_is_personalized():
    result = rec.recommend([], user_id="u3")
    assert result.warning is None
    assert DISHES[result.items[0].name]["protein"] in {"carne_vermelha", "porco"}


def test_deterministic_across_retraining():
    assert rec.recommend(["peixe", "leve"]).to_json() == FoodRecommender().recommend(["peixe", "leve"]).to_json()
