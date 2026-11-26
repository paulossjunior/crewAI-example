"""Shared dinner pipeline: run the three recommenders and render a plan without an LLM.

Used by the CLI, the CrewAI tools and the Streamlit UI. ``summarize`` is the offline stand-in for
the Host agent: it turns the three recommendations into a short, human paragraph.
``build_crew_inputs`` produces the placeholder values that ``config/tasks.yaml`` expects.
"""

from __future__ import annotations

import json

from dinner_crew.data import dataset_dir
from dinner_crew.intake import DinnerRequest, norm
from dinner_crew.recommenders.food_lightfm import FoodRecommender
from dinner_crew.recommenders.restaurant_surprise import RestaurantRecommender
from dinner_crew.recommenders.wine_implicit import WineRecommender

RECOMMENDER_LABELS = {
    "lightfm": "LightFM — modelo híbrido (curtidas de usuários parecidos + atributos dos pratos + suas preferências)",
    "implicit": "implicit — ALS sobre feedback implícito (histórico de vinhos pedidos com cada prato)",
    "surprise": "Surprise — KNN user-based sobre notas explícitas (usuários com gosto parecido)",
}


# More KNN neighbors on the large dataset: predictions average over more similar users.
KNN_NEIGHBORS = {"toy": 3, "large": 10}


class Recommenders:
    """The three models trained on one dataset (≈0.1 s on toy data, ≈2 s on large)."""

    def __init__(self, dataset: str = "toy") -> None:
        data_dir = dataset_dir(dataset)
        self.dataset = dataset
        self.food = FoodRecommender(data_dir=data_dir)
        self.wine = WineRecommender(data_dir=data_dir)
        self.restaurant = RestaurantRecommender(data_dir=data_dir, neighbors=KNN_NEIGHBORS[dataset])
        self.dishes = {d["name"]: d for d in self.food.dishes}


def run_recommenders(req: DinnerRequest, recs: Recommenders) -> dict:
    """Run dish -> wine -> restaurant for ``req``.

    Returns:
        ``{"food", "chosen_dish", "wine", "restaurant"}`` with ``Recommendation`` dicts, the same
        shape as the CLI's ``--dry-run`` output. ``chosen_dish`` is ``None`` (and wine/restaurant
        are omitted) when no dish satisfies the restrictions.
    """
    food = recs.food.recommend(req.preferences, req.restrictions, req.user_id)
    chosen = req.dish or (food.items[0].name if food.items else None)
    result = {"food": food.to_dict(), "chosen_dish": chosen, "wine": None, "restaurant": None}
    if chosen:
        dish = recs.dishes[chosen]
        result["wine"] = recs.wine.recommend(chosen, req.price).to_dict()
        result["restaurant"] = recs.restaurant.recommend(dish["cuisine"], req.city, req.user_id).to_dict()
    return result


BODY_TEXT = {"leve": "leve", "medio": "de corpo médio", "encorpado": "encorpado"}
TYPE_TEXT = {"tinto": "tinto", "branco": "branco", "rose": "rosé", "espumante": "espumante"}


def brl(value: int | float) -> str:
    """Format a price in Brazilian reais: ``brl(62) == "R$ 62"``."""
    return f"R$ {value:,.0f}".replace(",", ".")


def _details(item: dict) -> str:
    """Ingredients/grape and price line for one recommended item."""
    a = item["attributes"]
    if "ingredients" in a:
        return f"🧾 Ingredientes: {', '.join(a['ingredients'])} · 💰 {brl(a['price_brl'])}"
    if "grape" in a:
        return (f"🍇 Uva: {a['grape']} · {TYPE_TEXT[a['type']]} {BODY_TEXT[a['body']]} · "
                f"💰 {brl(a['price_brl'])} a garrafa")
    if "avg_ticket_brl" in a:
        return f"📍 {a['neighborhood']}, {a['city']} · 💰 ticket médio {brl(a['avg_ticket_brl'])} por pessoa"
    return ""


def _pick(rec: dict | None, chosen: str | None = None) -> dict | None:
    if not rec or not rec["items"]:
        return None
    return next((i for i in rec["items"] if i["name"] == chosen), rec["items"][0])


def _section(title: str, rec: dict | None, chosen: str | None = None) -> str:
    if rec is None:
        return ""
    lines = [f"## {title}"]
    items = rec["items"]
    pick = _pick(rec, chosen)
    if pick:
        lines.append(f"**Escolha:** {pick['name']}  \n{_details(pick)}  \n{pick['explanation']}")
        others = [i for i in items if i is not pick]
        if others:
            lines.append("**Alternativas:**\n" + "\n".join(f"- {i['name']} — {_details(i)}" for i in others))
    else:
        lines.append("_Nenhuma sugestão disponível._")
    lines.append(f"**Recomendador:** {RECOMMENDER_LABELS[rec['library']]}")
    if rec["warning"]:
        lines.append(f"> ⚠️ {rec['warning']}")
    return "\n\n".join(lines)


def summarize(result: dict, req: DinnerRequest | None = None) -> str:
    """Offline Host: a short, human paragraph that ties the three recommendations together.

    The LLM-backed Host agent (``config/agents.yaml``) writes this freely; this template version
    keeps the UI and the ``--dry-run``-style output useful without an API key.
    """
    dish = _pick(result["food"], result["chosen_dish"])
    if dish is None:
        return "Não encontrei nenhum prato que atenda às suas restrições. 😕"
    d = dish["attributes"]
    dish_words = norm(" ".join([*d["ingredients"], d["sauce"], d["intensity"], d["protein"]]))
    likes = [t for t in (req.preferences if req else []) if norm(t) in dish_words][:3]
    taste = f", bem no estilo do que você pediu ({', '.join(likes)})" if likes else ""
    text = [
        f"Para hoje, minha sugestão é **{dish['name']}** ({brl(d['price_brl'])}), um prato da culinária "
        f"{d['cuisine']} feito com {', '.join(d['ingredients'][:4])}{taste}."
    ]
    wine = _pick(result["wine"])
    if wine:
        w = wine["attributes"]
        why = ("pedido com frequência com esse prato" if "nunca pedido" not in wine["explanation"]
               else "muito pedido com pratos parecidos")
        text.append(
            f"Para acompanhar, abra um **{wine['name']}** ({brl(w['price_brl'])}), um {TYPE_TEXT[w['type']]} "
            f"{BODY_TEXT[w['body']]} de {w['grape']}, com notas de {w['notes']} — {why}."
        )
    place = _pick(result["restaurant"])
    if place:
        r = place["attributes"]
        text.append(
            f"E se preferir sair de casa, vá ao **{place['name']}**, em {r['neighborhood']} ({r['city']}), "
            f"com ticket médio de {brl(r['avg_ticket_brl'])} por pessoa."
        )
    if wine:
        text.append(f"Prato e vinho saem por cerca de {brl(d['price_brl'] + wine['attributes']['price_brl'])}. Bom apetite! 🍷")
    return " ".join(text)


def render_plan(result: dict, req: DinnerRequest | None = None) -> str:
    """Render a markdown dinner plan from ``run_recommenders`` output (no LLM involved).

    The plan starts with the Host summary, followed by one section per recommender with
    ingredients/grape and prices for every item.
    """
    if result["chosen_dish"] is None:
        return "Não encontrei nenhum prato que atenda às suas restrições. 😕"
    parts = [
        "## 🗣️ Resumo do anfitrião\n\n" + summarize(result, req),
        _section("🍽️ Prato", result["food"], result["chosen_dish"]),
        _section("🍷 Vinho", result["wine"]),
        _section("📍 Restaurante", result["restaurant"]),
    ]
    return "\n\n".join(p for p in parts if p)


def build_crew_inputs(req: DinnerRequest) -> dict:
    """Placeholder values for ``config/agents.yaml`` and ``config/tasks.yaml``."""
    dish_instruction = (
        f'O usuário fixou o prato "{req.dish}": escolha exatamente esse prato.'
        if req.dish
        else "Escolha o 1º prato da lista retornada."
    )
    return {
        "preferences": ", ".join(req.preferences) or "(nenhuma)",
        "restrictions": ", ".join(req.restrictions) or "(nenhuma)",
        "preferences_list": json.dumps(req.preferences, ensure_ascii=False),
        "restrictions_list": json.dumps(req.restrictions, ensure_ascii=False),
        "dish_instruction": dish_instruction,
        "price": req.price,
        "city": req.city,
        "user_id": req.user_id or "(novo usuário)",
        "user_id_json": json.dumps(req.user_id),
    }
