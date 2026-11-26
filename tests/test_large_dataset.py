import filecmp
import importlib.util
from pathlib import Path

import pytest

from dinner_crew.data import (
    dataset_dir,
    load_dish_likes,
    load_dishes,
    load_ratings,
    load_restaurants,
    load_user_profiles,
    load_wine_orders,
    load_wines,
)
from dinner_crew.intake import DinnerRequest
from dinner_crew.pipeline import Recommenders, render_plan, run_recommenders, summarize

ROOT = Path(__file__).resolve().parents[1]
LARGE = dataset_dir("large")


@pytest.fixture(scope="module")
def recs():
    return Recommenders("large")


def test_committed_data_matches_generator(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("gen", ROOT / "scripts" / "generate_large_data.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    monkeypatch.setattr(gen, "OUT", tmp_path)
    gen.main()
    for csv_file in LARGE.glob("*.csv"):
        assert filecmp.cmp(csv_file, tmp_path / csv_file.name, shallow=False), f"{csv_file.name} is stale"


def test_sizes():
    assert len(load_dishes(LARGE)) > 150
    assert len(load_wines(LARGE)) > 100
    assert len(load_restaurants(LARGE)) > 350
    assert len(load_user_profiles(LARGE)) == 1500
    assert len(load_dish_likes(LARGE)) > 10_000
    assert len(load_ratings(LARGE)) > 30_000


def test_referential_integrity():
    dishes = {d["name"] for d in load_dishes(LARGE)}
    wines = {w["name"] for w in load_wines(LARGE)}
    restaurants = {r["name"] for r in load_restaurants(LARGE)}
    users = set(load_user_profiles(LARGE))
    assert all(r["dish"] in dishes and r["user_id"] in users for r in load_dish_likes(LARGE))
    assert all(o["dish"] in dishes and o["wine"] in wines for o in load_wine_orders(LARGE))
    assert all(r["restaurant"] in restaurants and 1 <= r["rating"] <= 5 for r in load_ratings(LARGE))
    assert not any("," in name for name in restaurants)  # Surprise reads ratings.csv with sep=","


def test_every_item_has_ingredients_and_prices():
    assert all(d["ingredients"] and d["price_brl"] > 0 for d in load_dishes(LARGE))
    assert all(w["grape"] and w["price_brl"] > 0 for w in load_wines(LARGE))
    assert all(r["avg_ticket_brl"] > 0 for r in load_restaurants(LARGE))


def test_vegan_dishes_are_plant_based():
    for d in load_dishes(LARGE):
        if "vegano" in d["suitable_for"]:
            assert d["protein"] == "vegetal" and "vegetariano" in d["suitable_for"]


def test_food_respects_restrictions(recs):
    dishes = {d["name"]: d for d in recs.food.dishes}
    for item in recs.food.recommend(["curry", "pimenta"], ["vegano"]).items:
        assert "vegano" in dishes[item.name]["suitable_for"]


def test_red_meat_gets_full_bodied_red(recs):
    top = recs.wine.recommend("Parrilla de carne", "media").items[0].attributes
    assert (top["type"], top["body"]) == ("tinto", "encorpado")


def test_restaurant_uses_neighbors_for_known_user(recs):
    result = recs.restaurant.recommend("italiana", "São Paulo", "u0010")
    assert result.items
    assert all(i.attributes["city"] == "São Paulo" for i in result.items)
    assert any("usuários parecidos" in i.explanation for i in result.items)


def test_plan_has_summary_ingredients_and_prices(recs):
    req = DinnerRequest(["peixe", "cru"], city="Recife", user_id="u0100")
    result = run_recommenders(req, recs)
    plan = render_plan(result, req)
    assert "## 🗣️ Resumo do anfitrião" in plan
    assert "Ingredientes:" in plan and "R$" in plan and "ticket médio" in plan
    assert result["chosen_dish"] in summarize(result, req)
