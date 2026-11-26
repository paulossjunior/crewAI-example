"""Shared vocabularies and the Recommendation result type returned by every recommender.

The tuples below are the closed categorical vocabularies used across the toy datasets and the
LightFM / implicit / Surprise recommenders. Values are kept in Portuguese because they must match
the CSV contents verbatim.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

# Dish attributes.
PROTEINS = ("carne_vermelha", "ave", "porco", "peixe", "frutos_do_mar", "vegetal", "queijo")
SAUCES = ("cremoso", "tomate", "leve", "picante", "intenso", "doce")
INTENSITIES = ("leve", "media", "intensa")
# Restaurant price tiers and diner dietary restrictions.
PRICES = ("baixa", "media", "alta")  # ordered: index = tier
RESTRICTIONS = ("vegetariano", "vegano", "sem_gluten", "sem_lactose")
# Wine attributes.
WINE_TYPES = ("tinto", "branco", "rose", "espumante")
WINE_BODIES = ("leve", "medio", "encorpado")

# Upper bound on items in any Recommendation; enforced in Recommendation.__post_init__.
MAX_ITEMS = 3


@dataclass
class Item:
    """A single recommended entity (dish, wine or restaurant).

    Attributes:
        name: Human-readable name of the recommended entity.
        score: Recommender-specific relevance score; higher means more relevant. Scales are not
            comparable across libraries.
        explanation: Short human-readable justification for the recommendation.
        attributes: Extra entity metadata (e.g. protein, wine type, price tier) passed through
            to the caller.
    """

    name: str
    score: float
    explanation: str
    attributes: dict = field(default_factory=dict)


@dataclass
class Recommendation:
    """Uniform result returned by every recommender tool.

    Attributes:
        technique: Recommendation technique used: ``"hybrid"``, ``"implicit-feedback-als"`` or
            ``"explicit-rating-knn"``.
        library: Library that produced the result: ``"lightfm"``, ``"implicit"`` or ``"surprise"``.
        items: Recommended items, ordered by relevance. Truncated to ``MAX_ITEMS`` on creation.
        warning: Optional caveat for the caller (e.g. cold-start fallback), or ``None``.
    """

    technique: str  # "hybrid" | "implicit-feedback-als" | "explicit-rating-knn"
    library: str  # "lightfm" | "implicit" | "surprise"
    items: list[Item]
    warning: str | None = None

    def __post_init__(self) -> None:
        """Truncate ``items`` to at most ``MAX_ITEMS`` entries."""
        self.items = self.items[:MAX_ITEMS]

    def to_dict(self) -> dict:
        """Convert the recommendation to a plain dict.

        Returns:
            A recursively converted dict, with nested ``Item`` objects as dicts.
        """
        return asdict(self)

    def to_json(self) -> str:
        """Serialize the recommendation to pretty-printed JSON.

        Returns:
            A JSON string indented by 2 spaces. Non-ASCII characters (e.g. Portuguese accents) are
            kept as-is rather than escaped.
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
