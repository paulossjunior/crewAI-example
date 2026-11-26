"""Shared vocabularies and the Recommendation result type returned by every recommender."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

PROTEINS = ("carne_vermelha", "ave", "porco", "peixe", "frutos_do_mar", "vegetal", "queijo")
SAUCES = ("cremoso", "tomate", "leve", "picante", "intenso", "doce")
INTENSITIES = ("leve", "media", "intensa")
PRICES = ("baixa", "media", "alta")  # ordered: index = tier
RESTRICTIONS = ("vegetariano", "vegano", "sem_gluten", "sem_lactose")
WINE_TYPES = ("tinto", "branco", "rose", "espumante")
WINE_BODIES = ("leve", "medio", "encorpado")

MAX_ITEMS = 3


@dataclass
class Item:
    name: str
    score: float
    explanation: str
    attributes: dict = field(default_factory=dict)


@dataclass
class Recommendation:
    technique: str  # "hybrid" | "implicit-feedback-als" | "explicit-rating-knn"
    library: str  # "lightfm" | "implicit" | "surprise"
    items: list[Item]
    warning: str | None = None

    def __post_init__(self) -> None:
        self.items = self.items[:MAX_ITEMS]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
