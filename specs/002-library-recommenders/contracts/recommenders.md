# Contract: Library Recommenders & Tools

All return `Recommendation(technique, library, items[≤3], warning)`; `Item(name, score, explanation, attributes)`.

| Class / method | Library | `technique` |
|---|---|---|
| `FoodRecommender.recommend(preferences, restrictions, user_id=None, k=3)` | `lightfm` | `hybrid` |
| `WineRecommender.recommend(dish_name, price="media", k=3)` | `implicit` | `implicit-feedback-als` |
| `RestaurantRecommender.recommend(cuisine, city, user_id=None, k=3)` | `surprise` | `explicit-rating-knn` |

Errors: unknown dish / invalid price in `WineRecommender` → `ValueError`.

| Tool name | Args |
|---|---|
| `food_lightfm_recommender` | `preferences: list[str]`, `restrictions: list[str]`, `user_id: str \| None` |
| `wine_implicit_recommender` | `dish_name: str`, `price: str` |
| `restaurant_surprise_recommender` | `cuisine: str`, `city: str`, `user_id: str \| None` |

Tool output: `Recommendation` as JSON string; description names library + technique.
