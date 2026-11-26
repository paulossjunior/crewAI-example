"""Wine recommender with implicit (ALS on implicit feedback).

Technique: nobody rated wines; we only know how often each wine was *ordered* together with each
dish (``data/wine_orders.csv``). That is implicit feedback: counts express confidence, absence is
not a dislike. Alternating Least Squares factorizes the dish x wine confidence matrix into latent
factors. Here the dish plays the role of the "user": a dish's factor vector scores every wine, so
wines ordered with *similar dishes* score high even if never ordered with this one.
"""

from __future__ import annotations

import numpy as np
from implicit.als import AlternatingLeastSquares
from scipy.sparse import csr_matrix

from dinner_crew.data import load_dishes, load_wine_orders, load_wines
from dinner_crew.models import PRICES, Item, Recommendation

TECHNIQUE = "implicit-feedback-als"
LIBRARY = "implicit"
MIN_RELATIVE_SCORE = 0.3
WEAK_SIGNAL = 0.2


class WineRecommender:
    def __init__(self, dishes=None, wines=None, orders=None, factors: int = 8, seed: int = 42) -> None:
        self.dishes = dishes if dishes is not None else load_dishes()
        self.wines = wines if wines is not None else load_wines()
        orders = orders if orders is not None else load_wine_orders()

        self.dish_idx = {d["name"]: i for i, d in enumerate(self.dishes)}
        self.wine_idx = {w["name"]: j for j, w in enumerate(self.wines)}
        rows = [self.dish_idx[o["dish"]] for o in orders if o["wine"] in self.wine_idx]
        cols = [self.wine_idx[o["wine"]] for o in orders if o["wine"] in self.wine_idx]
        vals = [float(o["count"]) for o in orders if o["wine"] in self.wine_idx]
        self.orders = csr_matrix((vals, (rows, cols)), shape=(len(self.dishes), len(self.wines)))

        self.model = AlternatingLeastSquares(
            factors=factors, regularization=0.05, alpha=2.0, iterations=30, random_state=seed, num_threads=1
        )
        self.model.fit(self.orders, show_progress=False)

    def similar_dishes(self, dish: int, n: int = 2) -> list[str]:
        ids, _ = self.model.similar_users(dish, N=n + 1)
        return [self.dishes[i]["name"] for i in ids if i != dish][:n]

    def recommend(self, dish_name: str, price: str = "media", k: int = 3) -> Recommendation:
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

        ids, scores = self.model.recommend(
            d, self.orders[d], N=len(candidates), filter_already_liked_items=False, items=np.array(candidates)
        )
        ranked = sorted(zip(ids, scores), key=lambda s: (-round(float(s[1]), 6), self.wines[s[0]]["name"]))
        # Relevance cut: drop the tail far below the best match (weak latent signal on tiny data).
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
                attributes={k: w[k] for k in ("type", "body", "price", "notes")},
            ))
        return Recommendation(TECHNIQUE, LIBRARY, items, warning=warning)
