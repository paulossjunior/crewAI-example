from dinner_crew.data import load_ratings, load_restaurants
from dinner_crew.recommenders.restaurant_surprise import RestaurantRecommender

rec = RestaurantRecommender()
RESTAURANTS = {r["name"]: r for r in load_restaurants()}
RATED_BY_U1 = {r["restaurant"] for r in load_ratings() if r["user_id"] == "u1"}


def test_known_user_gets_unrated_restaurants_from_similar_users():
    result = rec.recommend("italiana", "São Paulo", "u1")
    assert (result.technique, result.library) == ("explicit-rating-knn", "surprise")
    assert result.warning is None
    names = [i.name for i in result.items]
    assert names[0] == "Osteria del Porto"
    for name in names:
        assert name not in RATED_BY_U1
        assert (RESTAURANTS[name]["cuisine"], RESTAURANTS[name]["city"]) == ("italiana", "São Paulo")
    assert "u2" in result.items[0].explanation


def test_unknown_user_falls_back_to_popularity():
    result = rec.recommend("italiana", "São Paulo", "u99")
    assert result.warning and "popularidade" in result.warning.lower()
    assert result.items[0].name == "Osteria del Porto"


def test_no_user_falls_back():
    assert rec.recommend("japonesa", "São Paulo", None).warning


def test_other_city_fallback():
    result = rec.recommend("argentina", "Rio de Janeiro", "u1")
    assert result.warning and "outras cidades" in result.warning
    assert [i.name for i in result.items] == ["Parrilla Buenos Aires"]


def test_unrated_restaurant_uses_global_mean():
    item = rec.recommend("italiana", "Rio de Janeiro", "u1").items[0]
    assert item.name == "Pasta & Basta"
    assert item.score == round(rec.trainset.global_mean, 4)


def test_predictions_within_scale():
    for user in ["u1", "u2", "u4", "u7", "u8"]:
        for cuisine in ["italiana", "japonesa", "brasileira", "francesa", "árabe", "mexicana"]:
            for item in rec.recommend(cuisine, "São Paulo", user).items:
                assert 1.0 <= item.score <= 5.0


def test_deterministic_across_retraining():
    assert rec.recommend("italiana", "São Paulo", "u4").to_json() == RestaurantRecommender().recommend("italiana", "São Paulo", "u4").to_json()


def test_revisit_when_all_city_restaurants_already_rated():
    # u1 already rated the only French restaurant in São Paulo
    result = rec.recommend("francesa", "São Paulo", "u1")
    assert result.warning and "revisitar" in result.warning
    assert result.items[0].name == "Bistrô Le Petit"
    assert result.items[0].score == 3.0
