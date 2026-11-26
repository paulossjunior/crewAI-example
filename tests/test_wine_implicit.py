import pytest

from dinner_crew.data import load_wine_orders, load_wines
from dinner_crew.recommenders.wine_implicit import WineRecommender

rec = WineRecommender()
WINES = {w["name"]: w for w in load_wines()}


def test_red_meat_gets_full_bodied_red():
    result = rec.recommend("Bife ancho com chimichurri", price="media")
    assert (result.technique, result.library) == ("implicit-feedback-als", "implicit")
    top = WINES[result.items[0].name]
    assert (top["type"], top["body"]) == ("tinto", "encorpado")
    assert result.warning is None


def test_price_tier_respected():
    for price in ["baixa", "media", "alta"]:
        for item in rec.recommend("Sushi de salmão", price=price).items:
            assert WINES[item.name]["price"] == price


def test_light_fish_never_gets_full_bodied_red():
    for item in rec.recommend("Sushi de salmão", price="media").items:
        w = WINES[item.name]
        assert not (w["type"] == "tinto" and w["body"] == "encorpado")


def test_price_relaxed_when_tier_empty():
    no_premium = [w for w in load_wines() if w["price"] != "alta"]
    orders = [o for o in load_wine_orders() if WINES[o["wine"]]["price"] != "alta"]
    result = WineRecommender(wines=no_premium, orders=orders).recommend("Coq au vin", price="alta")
    assert result.warning and "relaxada" in result.warning
    assert all(WINES[i.name]["price"] == "media" for i in result.items)


def test_weak_signal_warns():
    result = rec.recommend("Enchiladas de queijo", price="alta")
    assert result.warning and "Sinal fraco" in result.warning


def test_unknown_dish_raises():
    with pytest.raises(ValueError):
        rec.recommend("Prato inexistente")


def test_deterministic_across_retraining():
    assert rec.recommend("Feijoada").to_json() == WineRecommender().recommend("Feijoada").to_json()
