"""CLI entry point: ``uv run dinner-crew --prefs "cogumelos,cremoso" --user u1``."""

from __future__ import annotations

import argparse
import json
import os
import sys

from dotenv import load_dotenv

from dinner_crew.data import load_dishes
from dinner_crew.models import PRICES, RESTRICTIONS
from dinner_crew.recommenders.food_lightfm import FoodRecommender
from dinner_crew.recommenders.restaurant_surprise import RestaurantRecommender
from dinner_crew.recommenders.wine_implicit import WineRecommender


def _csv(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="dinner-crew", description="Monta um plano de jantar com 3 agentes CrewAI.")
    p.add_argument("--prefs", default="", help='termos separados por vírgula, ex.: "cogumelos,cremoso"')
    p.add_argument("--restrictions", default="", help=f"separadas por vírgula: {', '.join(RESTRICTIONS)}")
    p.add_argument("--price", default="media", choices=PRICES)
    p.add_argument("--city", default="São Paulo")
    p.add_argument("--user", default=None, help="id do usuário, ex.: u1")
    p.add_argument("--dish", default=None, help="fixa o prato pelo nome exato")
    p.add_argument("--dry-run", action="store_true", help="só roda os recomendadores (sem LLM) e imprime JSON")
    return p.parse_args(argv)


def fail(message: str, code: int) -> int:
    print(f"Erro: {message}", file=sys.stderr)
    return code


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    load_dotenv()

    prefs, restrictions = _csv(args.prefs), _csv(args.restrictions)
    invalid = [r for r in restrictions if r not in RESTRICTIONS]
    if invalid:
        return fail(f"restrição inválida {invalid}; use: {', '.join(RESTRICTIONS)}.", 2)

    dishes = {d["name"]: d for d in load_dishes()}
    if args.dish and args.dish not in dishes:
        return fail(f"prato desconhecido {args.dish!r}; opções: {', '.join(sorted(dishes))}.", 2)

    food_rec = FoodRecommender()

    food = food_rec.recommend(prefs, restrictions, args.user)
    if not food.items and not args.dish:
        print(food.warning)
        return 1

    if args.dry_run:
        dish = dishes[args.dish or food.items[0].name]
        result = {
            "food": food.to_dict(),
            "chosen_dish": dish["name"],
            "wine": WineRecommender().recommend(dish["name"], args.price).to_dict(),
            "restaurant": RestaurantRecommender().recommend(dish["cuisine"], args.city, args.user).to_dict(),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if not os.getenv("OPENAI_API_KEY"):
        return fail("defina OPENAI_API_KEY no ambiente ou no arquivo .env.", 2)

    from dinner_crew.crew import DinnerCrew  # lazy: crewai import is slow

    dish_instruction = (
        f'O usuário fixou o prato "{args.dish}": escolha exatamente esse prato.'
        if args.dish
        else "Escolha o 1º prato da lista retornada."
    )
    inputs = {
        "preferences": ", ".join(prefs) or "(nenhuma)",
        "restrictions": ", ".join(restrictions) or "(nenhuma)",
        "preferences_list": json.dumps(prefs, ensure_ascii=False),
        "restrictions_list": json.dumps(restrictions, ensure_ascii=False),
        "dish_instruction": dish_instruction,
        "price": args.price,
        "city": args.city,
        "user_id": args.user or "(novo usuário)",
        "user_id_json": json.dumps(args.user),
    }
    output = DinnerCrew().crew().kickoff(inputs=inputs)
    print(output.raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
