"""Turn a free-text dinner request into structured inputs, without an LLM.

Rule-based intake used by the chat UI: it looks for known preference terms (the vocabulary of
``data/user_profiles.csv``), dietary restrictions, price words, cities, a user id (``u1``) and
exact dish names. Messages are read in the context of the previous request, so a follow-up like
"e um vinho mais barato?" changes only the price and keeps everything else.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, replace
from pathlib import Path

from dinner_crew.data import load_dishes, load_restaurants, load_user_profiles

RESTRICTION_PATTERNS = {
    "vegetariano": r"\bvegetarian[oa]s?\b",
    "vegano": r"\bvegan[oa]s?\b",
    "sem_gluten": r"\bsem gluten\b",
    "sem_lactose": r"\bsem lactose\b",
}
PRICE_PATTERNS = {
    "baixa": r"\b(barat[oa]s?|economic[oa]s?|em conta|mais em conta)\b",
    "alta": r"\b(car[oa]s?|sofisticad[oa]s?|especial|premium)\b",
    "media": r"\b(preco medio|medi[oa])\b",
}
# Words that talk *about* the dinner, not about taste ("e um vinho mais barato?"), even if a
# user profile happens to list them as a preference.
CONTEXT_WORDS = {"vinho", "vinhos", "prato", "pratos", "jantar", "comida", "restaurante", "restaurantes"}
CITY_ALIASES = {"sp": "São Paulo", "rio": "Rio de Janeiro", "rj": "Rio de Janeiro"}


def norm(text: str) -> str:
    """Lowercase and strip accents so "Camarão" and "camarao" match."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


@dataclass
class DinnerRequest:
    """Structured dinner request shared by the CLI, the UI and the crew."""

    preferences: list[str] = field(default_factory=list)
    restrictions: list[str] = field(default_factory=list)
    price: str = "media"
    city: str = "São Paulo"
    user_id: str | None = None
    dish: str | None = None


@dataclass
class ParseResult:
    """Updated request plus what this message changed (for the "Entendi: ..." summary)."""

    request: DinnerRequest
    understood: list[str]


class RequestParser:
    """Keyword-based parser over the project's vocabularies."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.vocab = {norm(t) for terms in load_user_profiles(data_dir).values() for t in terms}
        self.cities = {norm(r["city"]): r["city"] for r in load_restaurants(data_dir)}
        self.dishes = {norm(d["name"]): d["name"] for d in load_dishes(data_dir)}

    def _match_term(self, token: str) -> str | None:
        # Naive singular/plural tolerance: "cogumelo" -> "cogumelos", "tomates" -> "tomate".
        for candidate in (token, token + "s", token.rstrip("s")):
            if candidate in self.vocab:
                return candidate
        return None

    def parse(self, text: str, previous: DinnerRequest | None = None) -> ParseResult:
        """Parse ``text`` on top of ``previous`` and report what changed.

        Args:
            text: The user's message, in Portuguese.
            previous: The request so far; ``None`` starts from defaults.

        Returns:
            A ``ParseResult`` with the merged request and human-readable changes.
        """
        req = replace(previous) if previous else DinnerRequest()
        req.preferences, req.restrictions = list(req.preferences), list(req.restrictions)
        t = norm(text)
        understood: list[str] = []

        # Longest name first: "tacos de porco" must not lose to a shorter overlapping name.
        dish = next((self.dishes[k] for k in sorted(self.dishes, key=len, reverse=True) if k in t), None)
        if dish:
            req.dish = dish
            understood.append(f"prato fixado: {dish}")

        terms = []
        for token in re.findall(r"[a-z_]+", t):
            term = None if token in CONTEXT_WORDS else self._match_term(token)
            if term and term not in terms:
                terms.append(term)
        if terms:
            req.preferences = terms
            if not dish:
                req.dish = None  # new tastes replace a previously pinned dish
            understood.append("preferências: " + ", ".join(terms))

        for restriction, pattern in RESTRICTION_PATTERNS.items():
            if re.search(pattern, t) and restriction not in req.restrictions:
                req.restrictions.append(restriction)
                understood.append(f"restrição: {restriction}")

        for price, pattern in PRICE_PATTERNS.items():
            if re.search(pattern, t):
                req.price = price
                understood.append(f"preço: {price}")
                break

        city = next((name for key, name in self.cities.items() if key in t), None)
        if city is None:
            city = next((name for alias, name in CITY_ALIASES.items() if re.search(rf"\b{alias}\b", t)), None)
        if city:
            req.city = city
            understood.append(f"cidade: {city}")

        if m := re.search(r"\b(u\d+)\b", t):
            req.user_id = m.group(1)
            understood.append(f"usuário: {req.user_id}")

        return ParseResult(req, understood)
