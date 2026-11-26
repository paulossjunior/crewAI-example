# Contract: Recommenders & CrewAI Tools

Pure modules in `src/dinner_crew/recommenders/` (no CrewAI import). All return
`Recommendation` (see [data-model.md](../data-model.md)). Deterministic.

| Function | Technique |
|---|---|
| `FoodRecommender.recommend(preferences, restrictions, k=3)` | `content-based` |
| `WineRecommender.recommend(dish_name, price, k=3)` | `knowledge-based` |
| `RestaurantRecommender.recommend(cuisine, city, user_id, k=3)` | `collaborative-filtering` |

Errors: `WineRecommender.recommend` with unknown dish → `ValueError`.

## CrewAI tools (`src/dinner_crew/tools/`)

| Tool `name` | Args schema | Wraps |
|---|---|---|
| `food_content_based_recommender` | `preferences: list[str]`, `restrictions: list[str]` | FoodRecommender |
| `wine_knowledge_based_recommender` | `dish_name: str`, `price: str` | WineRecommender |
| `restaurant_collaborative_filtering_recommender` | `cuisine: str`, `city: str`, `user_id: str \| None` | RestaurantRecommender |

Each `_run` returns `Recommendation` serialized as JSON string (UTF-8, `ensure_ascii=False`).
Each tool `description` names its technique.
