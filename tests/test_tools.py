import json

from dinner_crew.tools.recommender_tools import FoodLightFMTool, RestaurantSurpriseTool, WineImplicitTool


def test_food_tool():
    tool = FoodLightFMTool()
    assert tool.name == "food_lightfm_recommender"
    assert "LightFM" in tool.description
    data = json.loads(tool._run(preferences=["cogumelos"], restrictions=[], user_id="u1"))
    assert (data["technique"], data["library"]) == ("hybrid", "lightfm")
    assert data["items"]


def test_wine_tool():
    tool = WineImplicitTool()
    assert tool.name == "wine_implicit_recommender"
    assert "implicit" in tool.description
    data = json.loads(tool._run(dish_name="Feijoada", price="media"))
    assert (data["technique"], data["library"]) == ("implicit-feedback-als", "implicit")
    assert "error" in json.loads(tool._run(dish_name="nada", price="media"))


def test_restaurant_tool():
    tool = RestaurantSurpriseTool()
    assert tool.name == "restaurant_surprise_recommender"
    assert "Surprise" in tool.description
    data = json.loads(tool._run(cuisine="italiana", city="São Paulo", user_id="u1"))
    assert (data["technique"], data["library"]) == ("explicit-rating-knn", "surprise")
