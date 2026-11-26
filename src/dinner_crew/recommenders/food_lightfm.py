"""Hybrid dish recommender with LightFM.

Technique: LightFM learns embeddings for *features* instead of raw ids. Each dish is the sum of
its attribute embeddings (cuisine, protein, sauce, intensity, tags) and each user is the sum of
their preference-term embeddings (plus an identity feature for known users). Training uses the
collaborative signal (which users liked which dishes) with the WARP ranking loss.

Because users are represented by features, a brand-new user is handled by building a feature row
from their ``--prefs`` terms: that is the hybrid model's answer to the cold-start problem.

Data sources:
    * User features: identity + ``pref:<term>`` from ``data/user_profiles.csv``.
    * Item features: identity + ``attr:<term>`` from each dish's attributes.
    * Interactions: ``data/dish_likes.csv``.

When the user is unknown and none of the preference terms is known to the model, the recommender
falls back to a popularity ranking (number of likes per dish).
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from pathlib import Path

import warnings

import numpy as np

with warnings.catch_warnings():  # macOS build has no OpenMP; we train single-threaded anyway
    warnings.filterwarnings("ignore", message="LightFM was compiled without OpenMP")
    from lightfm import LightFM
    from lightfm.data import Dataset
from scipy.sparse import csr_matrix

from dinner_crew.data import load_dish_likes, load_dishes, load_user_profiles
from dinner_crew.models import Item, Recommendation

TECHNIQUE = "hybrid"
LIBRARY = "lightfm"


def normalize(term: str) -> str:
    """Canonicalize a term so user preferences and dish attributes match.

    Strips accents (NFKD + ASCII), trims whitespace, lowercases and replaces spaces with
    underscores, e.g. ``"Frango Grelhado"`` -> ``"frango_grelhado"``.

    Args:
        term: Raw term from user input, profiles or dish data.

    Returns:
        The normalized term.
    """
    stripped = unicodedata.normalize("NFKD", term).encode("ascii", "ignore").decode()
    return stripped.strip().lower().replace(" ", "_")


def dish_terms(dish: dict) -> list[str]:
    """List the normalized descriptive terms of a dish.

    Args:
        dish: Dish record with ``cuisine``, ``protein``, ``sauce``, ``intensity`` and ``tags`` keys.

    Returns:
        Normalized terms in the order cuisine, protein, sauce, intensity, then tags.
    """
    return [normalize(t) for t in (dish["cuisine"], dish["protein"], dish["sauce"], dish["intensity"], *dish["tags"])]


class FoodRecommender:
    """Hybrid (content + collaborative) dish recommender backed by LightFM.

    The model is trained once at construction time; ``recommend`` then scores eligible dishes for
    a feature row built from the request.

    Attributes:
        dishes: Dish records used as the item catalog.
        names: Dish names, in catalog order.
        like_counts: Number of likes per dish name, used for the popularity fallback.
        users: Sorted ids of known users.
        dataset: Fitted LightFM ``Dataset`` holding id and feature mappings.
        user_features: Sparse user-feature matrix for known users.
        item_features: Sparse item-feature matrix for all dishes.
        model: Trained ``LightFM`` model.
        user_id_map: Maps user id to internal user index.
        user_feature_map: Maps user feature (identity or ``pref:<term>``) to column index.
        item_id_map: Maps dish name to internal item index.
    """

    def __init__(self, dishes=None, profiles=None, likes=None, epochs: int = 150, seed: int = 42,
                 data_dir: Path | None = None) -> None:
        """Build features and interactions, then train the LightFM model.

        Args:
            dishes: Dish records; loaded from the data folder when ``None``.
            profiles: Mapping of user id to preference terms; loaded from
                ``data/user_profiles.csv`` when ``None``.
            likes: Rows with ``user_id`` and ``dish`` keys; loaded from ``data/dish_likes.csv``
                when ``None``.
            epochs: Number of training epochs.
            seed: Random seed passed to LightFM for reproducible results.
            data_dir: Dataset directory for whatever is not injected; defaults to
                ``dataset_dir()`` (``$DINNER_DATASET``).
        """
        self.dishes = dishes if dishes is not None else load_dishes(data_dir)
        profiles = profiles if profiles is not None else load_user_profiles(data_dir)
        likes = likes if likes is not None else load_dish_likes(data_dir)

        self.names = [d["name"] for d in self.dishes]
        self.like_counts = Counter(row["dish"] for row in likes)
        self.users = sorted(profiles)

        user_feats = {u: [f"pref:{normalize(t)}" for t in terms] for u, terms in profiles.items()}
        item_feats = {d["name"]: [f"attr:{t}" for t in dish_terms(d)] for d in self.dishes}

        self.dataset = Dataset()  # identity features for users and items are added by default
        self.dataset.fit(
            users=self.users,
            items=self.names,
            user_features={f for fs in user_feats.values() for f in fs},
            item_features={f for fs in item_feats.values() for f in fs},
        )
        interactions, _ = self.dataset.build_interactions((r["user_id"], r["dish"]) for r in likes)
        self.user_features = self.dataset.build_user_features(user_feats.items())
        self.item_features = self.dataset.build_item_features(item_feats.items())

        self.model = LightFM(no_components=16, loss="warp", learning_rate=0.05, random_state=seed)
        # num_threads=1: multi-threaded Hogwild updates are non-deterministic even with a fixed seed.
        self.model.fit(
            interactions,
            user_features=self.user_features,
            item_features=self.item_features,
            epochs=epochs,
            num_threads=1,
        )
        self.user_id_map, self.user_feature_map, self.item_id_map, _ = self.dataset.mapping()

    def _user_row(self, preferences: list[str], user_id: str | None) -> tuple[csr_matrix | None, list[str]]:
        """Feature row for an arbitrary request (known user identity + preference terms).

        Lets the model score both known users (identity feature plus terms) and brand-new users
        (terms only), which is how cold start is handled.

        Args:
            preferences: Raw preference terms from the request; unknown terms are ignored.
            user_id: Optional user id; its identity feature is used only if the user is known.

        Returns:
            A ``(row, known)`` tuple: a 1 x n_user_features sparse row (``None`` if no feature was
            recognized) and the normalized preference terms the model knows.
        """
        cols, known = [], []
        if user_id in self.user_id_map:
            cols.append(self.user_feature_map[user_id])
        for term in preferences:
            feat = f"pref:{normalize(term)}"
            if feat in self.user_feature_map:
                cols.append(self.user_feature_map[feat])
                known.append(normalize(term))
        if not cols:
            return None, []
        cols = sorted(set(cols))
        # Equal 1/n weights mirror the row normalization build_user_features applies at training time.
        row = csr_matrix(
            (np.full(len(cols), 1.0 / len(cols), dtype=np.float32), ([0] * len(cols), cols)),
            shape=(1, len(self.user_feature_map)),
        )
        return row, known

    def recommend(self, preferences: list[str], restrictions: list[str] | None = None, user_id: str | None = None, k: int = 3) -> Recommendation:
        """Recommend up to ``k`` dishes for the given preferences.

        Dishes are first filtered by dietary restrictions, then ranked by LightFM score. If neither
        the user nor any preference term is known, dishes are ranked by popularity instead.

        Args:
            preferences: Raw preference terms (e.g. from ``--prefs``).
            restrictions: Dietary restrictions; a dish is eligible only if every restriction is in
                its ``suitable_for`` list.
            user_id: Optional id of a known user, adding their learned history to the score.
            k: Maximum number of dishes to return.

        Returns:
            A ``Recommendation`` with the ranked items, or with an empty list and a warning when no
            dish satisfies the restrictions. The popularity fallback also carries a warning.
        """
        restrictions = restrictions or []
        eligible = [d for d in self.dishes if all(r in d["suitable_for"] for r in restrictions)]
        if not eligible:
            return Recommendation(TECHNIQUE, LIBRARY, [], warning="Nenhum prato atende às restrições informadas.")

        row, known_terms = self._user_row(preferences, user_id)
        if row is None:
            ranked = sorted(eligible, key=lambda d: (-self.like_counts[d["name"]], d["name"]))[:k]
            items = [
                self._item(d, float(self.like_counts[d["name"]]), f"Popularidade: curtido por {self.like_counts[d['name']]} usuários.")
                for d in ranked
            ]
            return Recommendation(
                TECHNIQUE, LIBRARY, items,
                warning="Preferências não reconhecidas e usuário desconhecido: ranking por popularidade.",
            )

        # The custom feature row is passed as user_features, so the single request user is index 0.
        item_ids = np.array([self.item_id_map[d["name"]] for d in eligible], dtype=np.int32)
        scores = self.model.predict(
            np.zeros(len(item_ids), dtype=np.int32), item_ids,
            user_features=row, item_features=self.item_features, num_threads=1,
        )
        # Rounding absorbs float32 noise so near-equal scores tie-break deterministically by name.
        ranked = sorted(zip(scores, eligible), key=lambda s: (-round(float(s[0]), 6), s[1]["name"]))[:k]

        items = []
        for score, d in ranked:
            matched = sorted(set(known_terms) & set(dish_terms(d)))
            basis = f"atributos em comum com suas preferências: {', '.join(matched)}" if matched else "padrão de curtidas de usuários com perfil parecido"
            who = f" + histórico de {user_id}" if user_id in self.user_id_map else ""
            items.append(self._item(d, round(float(score), 4), f"Score LightFM {score:.2f} (preferências{who}); {basis}."))
        return Recommendation(TECHNIQUE, LIBRARY, items)

    @staticmethod
    def _item(d: dict, score: float, explanation: str) -> Item:
        """Wrap a dish into an ``Item`` with its key attributes.

        Args:
            d: Dish record.
            score: Ranking score (LightFM score or like count).
            explanation: Human-readable reason for the recommendation.

        Returns:
            An ``Item`` carrying the dish name, score, explanation and its cuisine, protein, sauce
            and intensity.
        """
        return Item(d["name"], score, explanation, {k: d[k] for k in ("cuisine", "protein", "sauce", "intensity", "ingredients", "price_brl")})
