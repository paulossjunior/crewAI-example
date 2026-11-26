"""CrewAI tools: each one exposes a recommender built on a different library to one agent.

- food_lightfm_recommender         -> LightFM (hybrid)
- wine_implicit_recommender        -> implicit (ALS, implicit feedback)
- restaurant_surprise_recommender  -> Surprise (KNN, explicit ratings)

Models are trained once, lazily, on first use.
"""

from __future__ import annotations

import json
from functools import cache

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from dinner_crew.recommenders.food_lightfm import FoodRecommender
from dinner_crew.recommenders.restaurant_surprise import RestaurantRecommender
from dinner_crew.recommenders.wine_implicit import WineRecommender


@cache
def food_recommender() -> FoodRecommender:
    return FoodRecommender()


@cache
def wine_recommender() -> WineRecommender:
    return WineRecommender()


@cache
def restaurant_recommender() -> RestaurantRecommender:
    return RestaurantRecommender()


class FoodArgs(BaseModel):
    preferences: list[str] = Field(default_factory=list, description="Termos de sabor/ingredientes, ex.: ['cogumelos', 'cremoso']")
    restrictions: list[str] = Field(default_factory=list, description="Restrições: vegetariano, vegano, sem_gluten, sem_lactose")
    user_id: str | None = Field(default=None, description="Id do usuário (ex.: u1) ou null para usuário novo")


class FoodLightFMTool(BaseTool):
    name: str = "food_lightfm_recommender"
    description: str = (
        "Recomenda até 3 pratos com LightFM, um modelo HÍBRIDO (conteúdo + colaborativo): aprende com "
        "curtidas de outros usuários e com atributos dos pratos e termos de preferência. Retorna JSON."
    )
    args_schema: type[BaseModel] = FoodArgs

    def _run(self, preferences: list[str] | None = None, restrictions: list[str] | None = None, user_id: str | None = None) -> str:
        return food_recommender().recommend(preferences or [], restrictions or [], user_id).to_json()


class WineArgs(BaseModel):
    dish_name: str = Field(description="Nome exato do prato escolhido")
    price: str = Field(default="media", description="Faixa de preço: baixa, media ou alta")


class WineImplicitTool(BaseTool):
    name: str = "wine_implicit_recommender"
    description: str = (
        "Recomenda até 3 vinhos para um prato com a biblioteca implicit (ALS sobre FEEDBACK IMPLÍCITO: "
        "histórico de quantas vezes cada vinho foi pedido com cada prato), filtrando por preço. Retorna JSON."
    )
    args_schema: type[BaseModel] = WineArgs

    def _run(self, dish_name: str, price: str = "media") -> str:
        try:
            return wine_recommender().recommend(dish_name, price).to_json()
        except ValueError as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)


class RestaurantArgs(BaseModel):
    cuisine: str = Field(description="Culinária do prato, ex.: italiana")
    city: str = Field(description="Cidade, ex.: São Paulo")
    user_id: str | None = Field(default=None, description="Id do usuário (ex.: u1) ou null")


class RestaurantSurpriseTool(BaseTool):
    name: str = "restaurant_surprise_recommender"
    description: str = (
        "Recomenda até 3 restaurantes com Surprise (KNN user-based sobre NOTAS EXPLÍCITAS 1-5: prevê a "
        "nota a partir de usuários com gosto parecido), filtrando por culinária e cidade. Retorna JSON."
    )
    args_schema: type[BaseModel] = RestaurantArgs

    def _run(self, cuisine: str, city: str, user_id: str | None = None) -> str:
        return restaurant_recommender().recommend(cuisine, city, user_id).to_json()
