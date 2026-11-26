"""CrewAI tools: each one exposes a recommender built on a different library to one agent.

- food_lightfm_recommender         -> LightFM (hybrid)
- wine_implicit_recommender        -> implicit (ALS, implicit feedback)
- restaurant_surprise_recommender  -> Surprise (KNN, explicit ratings)

Models are trained once, lazily, on first use, on the dataset named by ``$DINNER_DATASET``.
"""

from __future__ import annotations

import json
import os
from functools import cache

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from dinner_crew.pipeline import Recommenders
from dinner_crew.recommenders.food_lightfm import FoodRecommender
from dinner_crew.recommenders.restaurant_surprise import RestaurantRecommender
from dinner_crew.recommenders.wine_implicit import WineRecommender


# @cache: training happens once per dataset and process, not per tool call.
@cache
def _recommenders_for(dataset: str) -> Recommenders:
    return Recommenders(dataset)


def recommenders() -> Recommenders:
    """Return the trained models for the dataset in ``$DINNER_DATASET`` (default toy).

    Cached per dataset, so a long-running process (the Streamlit UI) can switch datasets.

    Returns:
        The shared ``Recommenders`` (food, wine, restaurant), trained on first use.
    """
    return _recommenders_for(os.getenv("DINNER_DATASET") or "toy")


def food_recommender() -> FoodRecommender:
    """Return the shared LightFM food recommender."""
    return recommenders().food


def wine_recommender() -> WineRecommender:
    """Return the shared implicit (ALS) wine recommender."""
    return recommenders().wine


def restaurant_recommender() -> RestaurantRecommender:
    """Return the shared Surprise (KNN) restaurant recommender."""
    return recommenders().restaurant


class FoodArgs(BaseModel):
    """Arguments schema for ``FoodLightFMTool``; field descriptions are shown to the LLM."""

    preferences: list[str] = Field(default_factory=list, description="Termos de sabor/ingredientes, ex.: ['cogumelos', 'cremoso']")
    restrictions: list[str] = Field(default_factory=list, description="Restrições: vegetariano, vegano, sem_gluten, sem_lactose")
    user_id: str | None = Field(default=None, description="Id do usuário (ex.: u1) ou null para usuário novo")


class FoodLightFMTool(BaseTool):
    """CrewAI adapter exposing the LightFM hybrid food recommender to an agent."""

    name: str = "food_lightfm_recommender"
    # The LLM reads `description` to decide when to call this tool.
    description: str = (
        "Recomenda até 3 pratos com LightFM, um modelo HÍBRIDO (conteúdo + colaborativo): aprende com "
        "curtidas de outros usuários e com atributos dos pratos e termos de preferência. Retorna JSON."
    )
    args_schema: type[BaseModel] = FoodArgs

    def _run(self, preferences: list[str] | None = None, restrictions: list[str] | None = None, user_id: str | None = None) -> str:
        """Recommend up to 3 dishes.

        Args:
            preferences: Flavor/ingredient terms; ``None`` is treated as empty.
            restrictions: Dietary restrictions to filter by; ``None`` is treated as empty.
            user_id: Known user id, or ``None`` for a cold-start user.

        Returns:
            A ``Recommendation`` serialized as JSON.
        """
        return food_recommender().recommend(preferences or [], restrictions or [], user_id).to_json()


class WineArgs(BaseModel):
    """Arguments schema for ``WineImplicitTool``; field descriptions are shown to the LLM."""

    dish_name: str = Field(description="Nome exato do prato escolhido")
    price: str = Field(default="media", description="Faixa de preço: baixa, media ou alta")


class WineImplicitTool(BaseTool):
    """CrewAI adapter exposing the implicit (ALS) wine-pairing recommender to an agent."""

    name: str = "wine_implicit_recommender"
    # The LLM reads `description` to decide when to call this tool.
    description: str = (
        "Recomenda até 3 vinhos para um prato com a biblioteca implicit (ALS sobre FEEDBACK IMPLÍCITO: "
        "histórico de quantas vezes cada vinho foi pedido com cada prato), filtrando por preço. Retorna JSON."
    )
    args_schema: type[BaseModel] = WineArgs

    def _run(self, dish_name: str, price: str = "media") -> str:
        """Recommend up to 3 wines for a dish within a price band.

        Args:
            dish_name: Exact name of the chosen dish.
            price: Price band: ``baixa``, ``media`` or ``alta``.

        Returns:
            A ``Recommendation`` serialized as JSON, or ``{"error": ...}`` JSON if the input is invalid.
        """
        try:
            return wine_recommender().recommend(dish_name, price).to_json()
        except ValueError as exc:
            # Return the error as JSON so the agent can read it and retry instead of the crew crashing.
            return json.dumps({"error": str(exc)}, ensure_ascii=False)


class RestaurantArgs(BaseModel):
    """Arguments schema for ``RestaurantSurpriseTool``; field descriptions are shown to the LLM."""

    cuisine: str = Field(description="Culinária do prato, ex.: italiana")
    city: str = Field(description="Cidade, ex.: São Paulo")
    user_id: str | None = Field(default=None, description="Id do usuário (ex.: u1) ou null")


class RestaurantSurpriseTool(BaseTool):
    """CrewAI adapter exposing the Surprise (KNN) restaurant recommender to an agent."""

    name: str = "restaurant_surprise_recommender"
    # The LLM reads `description` to decide when to call this tool.
    description: str = (
        "Recomenda até 3 restaurantes com Surprise (KNN user-based sobre NOTAS EXPLÍCITAS 1-5: prevê a "
        "nota a partir de usuários com gosto parecido), filtrando por culinária e cidade. Retorna JSON."
    )
    args_schema: type[BaseModel] = RestaurantArgs

    def _run(self, cuisine: str, city: str, user_id: str | None = None) -> str:
        """Recommend up to 3 restaurants matching a cuisine and city.

        Args:
            cuisine: Cuisine of the chosen dish (e.g. ``italiana``).
            city: City to search in.
            user_id: Known user id for personalized predicted ratings, or ``None``.

        Returns:
            A ``Recommendation`` serialized as JSON.
        """
        return restaurant_recommender().recommend(cuisine, city, user_id).to_json()
