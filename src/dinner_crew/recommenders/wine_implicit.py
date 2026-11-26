"""Wine recommender with implicit (ALS on implicit feedback).

Technique: nobody rated wines; we only know how often each wine was *ordered* together with each
dish (``data/wine_orders.csv``). That is implicit feedback: counts express confidence, absence is
not a dislike. Alternating Least Squares factorizes the dish x wine confidence matrix into latent
factors. Here the dish plays the role of the "user": a dish's factor vector scores every wine, so
wines ordered with *similar dishes* score high even if never ordered with this one.

Confidence follows the classic implicit-feedback recipe: ``confidence = 1 + alpha * count``. Results
are filtered by price tier (relaxed to the nearest tiers when the requested one is empty), the noisy
tail is cut relative to the best score, and a warning is attached when even the best score is weak.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from implicit.als import AlternatingLeastSquares
from scipy.sparse import csr_matrix

from dinner_crew.data import load_dishes, load_wine_orders, load_wines
from dinner_crew.models import PRICES, Item, Recommendation

TECHNIQUE = "implicit-feedback-als"
LIBRARY = "implicit"
# Keep only wines scoring at least this fraction of the best score (drops the noisy tail).
MIN_RELATIVE_SCORE = 0.3
# Best score below this absolute value adds a "weak signal" warning to the result.
WEAK_SIGNAL = 0.2


class WineRecommender:
    """Recommends wines for a dish using ALS over a dish x wine order-count matrix.

    The dish plays the library's "user" role and wines are the "items". The model is trained once
    in ``__init__``; ``recommend`` then scores the wines of a price tier for a given dish.

    Attributes:
        dishes: List of dish records (each with a ``"name"`` key).
        wines: List of wine records (``"name"``, ``"type"``, ``"body"``, ``"price"``, ``"notes"``).
        dish_idx: Map from dish name to matrix row.
        wine_idx: Map from wine name to matrix column.
        orders: Sparse CSR matrix (dishes x wines) with order counts.
        model: The fitted ``AlternatingLeastSquares`` model.
    """

    def __init__(self, dishes=None, wines=None, orders=None, factors: int = 8, seed: int = 42,
                 data_dir: Path | None = None) -> None:
        """Builds the order matrix and fits the ALS model.

        Args:
            dishes: Dish records; defaults to ``load_dishes()``. Injectable for tests.
            wines: Wine records; defaults to ``load_wines()``. Injectable for tests.
            orders: Order records with ``"dish"``, ``"wine"`` and ``"count"`` keys; defaults to
                ``load_wine_orders()`` (``data/wine_orders.csv``). Orders for unknown wines are ignored.
            factors: Number of latent factors in the ALS model.
            seed: Random seed for ALS initialization, for reproducible results.
            data_dir: Dataset directory for whatever is not injected; defaults to
                ``dataset_dir()`` (``$DINNER_DATASET``).

        Raises:
            KeyError: If an order references a dish not present in ``dishes``.
        """
        self.dishes = dishes if dishes is not None else load_dishes(data_dir)
        self.wines = wines if wines is not None else load_wines(data_dir)
        orders = orders if orders is not None else load_wine_orders(data_dir)

        self.dish_idx = {d["name"]: i for i, d in enumerate(self.dishes)}
        self.wine_idx = {w["name"]: j for j, w in enumerate(self.wines)}
        rows = [self.dish_idx[o["dish"]] for o in orders if o["wine"] in self.wine_idx]
        cols = [self.wine_idx[o["wine"]] for o in orders if o["wine"] in self.wine_idx]
        vals = [float(o["count"]) for o in orders if o["wine"] in self.wine_idx]
        self.orders = csr_matrix((vals, (rows, cols)), shape=(len(self.dishes), len(self.wines)))

        # alpha scales counts into confidence (1 + alpha * count); num_threads=1 keeps results deterministic.
        self.model = AlternatingLeastSquares(
            factors=factors, regularization=0.05, alpha=2.0, iterations=30, random_state=seed, num_threads=1
        )
        self.model.fit(self.orders, show_progress=False)

    def similar_dishes(self, dish: int, n: int = 2) -> list[str]:
        """Returns the dishes whose latent order pattern is closest to ``dish``.

        Used to explain recommendations ("dishes with a similar order pattern").

        Args:
            dish: Row index of the dish in the order matrix.
            n: Maximum number of similar dishes to return.

        Returns:
            Names of up to ``n`` most similar dishes, excluding ``dish`` itself.
        """
        # Ask for n + 1 because the dish itself is usually returned as its own nearest neighbor.
        ids, _ = self.model.similar_users(dish, N=n + 1)
        return [self.dishes[i]["name"] for i in ids if i != dish][:n]

    def recommend(self, dish_name: str, price: str = "media", k: int = 3) -> Recommendation:
        """Recommends up to ``k`` wines for a dish within a price tier.

        If the requested tier has no wines, the nearest tiers are used instead and a warning is
        added. Wines scoring below ``MIN_RELATIVE_SCORE`` of the best (or non-positive) are dropped,
        but at least one wine is always returned. A best score below ``WEAK_SIGNAL`` adds a warning.

        Args:
            dish_name: Name of a known dish.
            price: Price tier; must be one of ``PRICES``.
            k: Maximum number of wines to return.

        Returns:
            A ``Recommendation`` with ranked ``Item``s (score, explanation, wine attributes) and an
            optional warning. Items are empty only if there are no wines at all.

        Raises:
            ValueError: If ``dish_name`` is unknown or ``price`` is not in ``PRICES``.
        """
        if dish_name not in self.dish_idx:
            raise ValueError(f"Prato desconhecido: {dish_name!r}")
        if price not in PRICES:
            raise ValueError(f"Faixa de preço inválida: {price!r}; use {PRICES}")
        d = self.dish_idx[dish_name]

        # Price filter; if the tier has no wine, relax to the nearest tiers.
        target, warning, candidates = PRICES.index(price), None, []
        for distance in range(len(PRICES)):
            candidates = [j for j, w in enumerate(self.wines) if abs(PRICES.index(w["price"]) - target) == distance]
            if candidates:
                if distance:
                    warning = f"Nenhum vinho na faixa '{price}'; faixa de preço relaxada."
                break
        if not candidates:
            return Recommendation(TECHNIQUE, LIBRARY, [], warning="Nenhum vinho disponível.")

        # filter_already_liked_items=False: wines already ordered with this dish are exactly what we want
        # to rank. items= restricts scoring to the price-tier candidates.
        ids, scores = self.model.recommend(
            d, self.orders[d], N=len(candidates), filter_already_liked_items=False, items=np.array(candidates)
        )
        # Round scores so float noise doesn't break ties; ties are then ordered by wine name.
        ranked = sorted(zip(ids, scores), key=lambda s: (-round(float(s[1]), 6), self.wines[s[0]]["name"]))
        # Relevance cut: drop the tail far below the best match (weak latent signal on tiny data).
        # `or ranked[:1]` guarantees at least one wine even if every score is cut.
        best = float(ranked[0][1])
        ranked = [(j, sc) for j, sc in ranked if sc > 0 and sc >= MIN_RELATIVE_SCORE * best][:k] or ranked[:1]
        if best < WEAK_SIGNAL:
            weak = f"Sinal fraco (score {best:.2f}): nenhum vinho desta faixa costuma ser pedido com pratos parecidos."
            warning = f"{warning} {weak}" if warning else weak

        similar = ", ".join(self.similar_dishes(d))
        items = []
        for j, score in ranked:
            w = self.wines[j]
            count = int(self.orders[d, j])
            history = f"pedido {count}x com este prato" if count else "nunca pedido com este prato"
            items.append(Item(
                name=w["name"],
                score=round(float(score), 4),
                explanation=f"Score ALS {score:.2f}; {history}; pratos com padrão de pedidos parecido: {similar}.",
                attributes={k: w[k] for k in ("type", "body", "price", "notes", "grape", "price_brl")},
            ))
        return Recommendation(TECHNIQUE, LIBRARY, items, warning=warning)
