"""Restaurant recommender with Surprise (user-based KNN on explicit ratings).

Technique: users rated restaurants explicitly from 1 to 5 (``data/ratings.csv``). Surprise's
``KNNWithMeans`` computes Pearson similarity between users and predicts:

    r_hat(u, i) = mean(u) + sum_v sim(u, v) * (r(v, i) - mean(v)) / sum_v sim(u, v)

over the k most similar users who rated *i*. Mean-centering corrects for harsh vs lenient raters.
Unknown users (or items no neighbor rated) fall back to the restaurant's average rating, and
restaurants nobody rated yet fall back to the global mean rating.

Ratings are loaded with ``Dataset.load_from_file`` so the module does not depend on pandas.
"""

from __future__ import annotations

from pathlib import Path

from surprise import Dataset, KNNWithMeans, Reader

from dinner_crew.data import dataset_dir, load_ratings, load_restaurants
from dinner_crew.models import Item, Recommendation

TECHNIQUE = "explicit-rating-knn"
LIBRARY = "surprise"
MIN_SUPPORT = 3


class RestaurantRecommender:
    """Recommends restaurants of a cuisine in a city using user-based KNN on explicit ratings.

    Attributes:
        restaurants: Restaurant catalog rows (dicts with ``name``, ``cuisine``, ``city``,
            ``neighborhood`` and ``price``).
        trainset: Surprise ``Trainset`` built from every row of ``ratings.csv``.
        algo: Fitted ``KNNWithMeans`` model (Pearson similarity, user-based).
        k: Maximum number of neighbors considered per prediction.
        rated: Maps each user id to the set of restaurant names that user has rated.
        own_rating: Maps ``(user_id, restaurant)`` to the rating that user gave.
        item_mean: Maps each rated restaurant name to its mean rating across all users.
    """

    def __init__(self, data_dir: Path | None = None, neighbors: int = 3) -> None:
        """Loads the data and fits the KNN model.

        Args:
            data_dir: Directory containing the restaurant catalog and ``ratings.csv``.
                Defaults to ``dataset_dir()`` (``$DINNER_DATASET``).
            neighbors: Number of most similar users (k) the KNN model uses per prediction.
        """
        data_dir = data_dir or dataset_dir()
        self.restaurants = load_restaurants(data_dir)
        ratings = load_ratings(data_dir)

        reader = Reader(line_format="user item rating", sep=",", skip_lines=1, rating_scale=(1, 5))
        self.trainset = Dataset.load_from_file(str(data_dir / "ratings.csv"), reader=reader).build_full_trainset()
        # min_support: ignore similarities computed from fewer than 3 co-rated restaurants, which
        # are mostly noise (Pearson 1.0 from 2 ratings) on sparse data.
        self.algo = KNNWithMeans(
            k=neighbors, sim_options={"name": "pearson", "user_based": True, "min_support": MIN_SUPPORT}, verbose=False
        )
        self.algo.fit(self.trainset)
        self.k = neighbors

        self.rated: dict[str, set[str]] = {}
        self.own_rating: dict[tuple[str, str], int] = {}
        totals: dict[str, list[int]] = {}
        for r in ratings:
            self.rated.setdefault(r["user_id"], set()).add(r["restaurant"])
            self.own_rating[(r["user_id"], r["restaurant"])] = r["rating"]
            totals.setdefault(r["restaurant"], []).append(r["rating"])
        self.item_mean = {name: sum(v) / len(v) for name, v in totals.items()}

    def _neighbors(self, user_id: str, restaurant: str) -> list[tuple[str, float]]:
        """The k most similar users (sim > 0) who rated the restaurant: what KNN used.

        Mirrors the neighbor selection of ``KNNWithMeans`` so the explanation text can name the
        users behind a prediction. An empty list means KNN has no usable neighbor for this item.

        Args:
            user_id: Raw id of a user present in the trainset.
            restaurant: Name of a restaurant present in the trainset.

        Returns:
            Up to ``k`` ``(raw_user_id, pearson_similarity)`` pairs, most similar first (ties
            broken by user id), keeping only positive similarities.

        Raises:
            ValueError: If the user or the restaurant is not part of the trainset.
        """
        # Surprise indexes users/items by internal integer ids; convert raw ids in and back out.
        u = self.trainset.to_inner_uid(user_id)
        i = self.trainset.to_inner_iid(restaurant)
        raters = [(v, self.algo.sim[u, v]) for v, _ in self.trainset.ir[i] if v != u]
        raters.sort(key=lambda s: (-s[1], self.trainset.to_raw_uid(s[0])))
        return [(self.trainset.to_raw_uid(v), float(s)) for v, s in raters[: self.k] if s > 0]

    def recommend(self, cuisine: str, city: str, user_id: str | None = None, k: int = 3) -> Recommendation:
        """Recommends up to ``k`` restaurants of ``cuisine``, preferably in ``city``.

        Candidates come from the first non-empty pool, in this order:

        1. Restaurants of the cuisine in the city that the user has not rated.
        2. Restaurants of the cuisine in the city the user already rated (a revisit).
        3. Unrated restaurants of the cuisine in any city.

        Each candidate is scored by the first applicable rule:

        - Already rated by the user: the user's own rating.
        - Known user with positive-similarity neighbors who rated it: the KNN prediction.
        - Rated by someone: the restaurant's mean rating (popularity fallback).
        - Never rated: the trainset's global mean rating.

        Args:
            cuisine: Cuisine to match exactly against the catalog.
            city: Preferred city.
            user_id: Raw id of the user; ``None`` or an unknown id triggers the popularity fallback.
            k: Maximum number of items to return.

        Returns:
            A ``Recommendation`` with items sorted by descending score (ties by name) and a
            warning explaining any pool relaxation or fallback, or no items if nothing matches.
        """
        known_user = user_id in self.rated
        already = self.rated.get(user_id, set())

        def pool(any_city: bool, include_rated: bool = False) -> list[dict]:
            return [r for r in self.restaurants
                    if r["cuisine"] == cuisine and (any_city or r["city"] == city)
                    and (include_rated or r["name"] not in already)]

        # Order of preference: new places in the city -> revisit places in the city -> other cities.
        warnings = []
        candidates = pool(any_city=False)
        if not candidates and (candidates := pool(any_city=False, include_rated=True)):
            warnings.append(f"Você já avaliou todos os restaurantes '{cuisine}' em {city}; sugerindo revisitar.")
        if not candidates and (candidates := pool(any_city=True)):
            warnings.append(f"Nenhum restaurante '{cuisine}' em {city}; sugerindo de outras cidades.")
        if not candidates:
            return Recommendation(TECHNIQUE, LIBRARY, [], warning=f"Nenhum restaurante '{cuisine}' disponível.")

        scored, fallback = [], False
        for r in candidates:
            if r["name"] in already:
                # Revisit: the user's actual rating beats any prediction for an item they know.
                est = float(self.own_rating[(user_id, r["name"])])
                scored.append((est, r, f"Você mesmo já deu nota {est:.0f} a este restaurante."))
                continue
            # Guard: _neighbors raises for users/items absent from the trainset.
            neigh = self._neighbors(user_id, r["name"]) if known_user and r["name"] in self.item_mean else []
            if neigh:
                est = self.algo.predict(user_id, r["name"]).est
                who = ", ".join(f"{v} (pearson {s:.2f})" for v, s in neigh)
                why = f"Nota prevista {est:.2f} pelo KNN a partir de usuários parecidos: {who}."
            else:
                fallback = True
                if r["name"] in self.item_mean:
                    est = self.item_mean[r["name"]]
                    why = f"Popularidade: nota média {est:.2f} entre todos os usuários."
                else:
                    # No ratings at all: global mean is a neutral prior instead of ranking it last.
                    est = self.trainset.global_mean
                    why = f"Sem avaliações ainda; usando a média global {est:.2f}."
            scored.append((round(float(est), 4), r, why))

        if fallback:
            reason = "usuário sem histórico" if not known_user else "nenhum usuário parecido avaliou alguns itens"
            warnings.append(f"Fallback por popularidade ({reason}).")

        scored.sort(key=lambda s: (-s[0], s[1]["name"]))
        items = [Item(r["name"], est, why, {key: r[key] for key in ("cuisine", "city", "neighborhood", "price", "avg_ticket_brl")})
                 for est, r, why in scored[:k]]
        return Recommendation(TECHNIQUE, LIBRARY, items, warning=" ".join(warnings) or None)
