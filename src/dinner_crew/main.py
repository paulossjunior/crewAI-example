"""CLI entry point: ``uv run dinner-crew --prefs "cogumelos,cremoso" --user u1``.

Builds a dinner plan (dish, wine, restaurant). By default it runs the three-agent
CrewAI crew, which needs ``OPENAI_API_KEY``. With ``--dry-run`` it calls the three
recommenders (LightFM food, implicit wine, Surprise restaurant) directly, skips the
LLM, and prints their results as JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from dotenv import load_dotenv

from dinner_crew.data import DATASETS, dataset_dir, load_dishes
from dinner_crew.intake import DinnerRequest
from dinner_crew.models import PRICES, RESTRICTIONS
from dinner_crew.pipeline import Recommenders, build_crew_inputs, run_recommenders


def _csv(value: str | None) -> list[str]:
    """Split a comma-separated string into a list of trimmed, non-empty items.

    Args:
        value: Raw comma-separated text, or ``None``.

    Returns:
        The stripped items in their original order. Empty when ``value`` is ``None``
        or has no non-blank items.
    """
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the ``dinner-crew`` command-line arguments.

    Args:
        argv: Arguments to parse, without the program name. ``None`` means ``sys.argv[1:]``.

    Returns:
        A namespace with ``prefs``, ``restrictions``, ``price``, ``city``, ``user``,
        ``dish`` and ``dry_run``. ``prefs`` and ``restrictions`` are still raw
        comma-separated strings at this point.
    """
    p = argparse.ArgumentParser(prog="dinner-crew", description="Monta um plano de jantar com 3 agentes CrewAI.")
    p.add_argument("--prefs", default="", help='termos separados por vírgula, ex.: "cogumelos,cremoso"')
    p.add_argument("--restrictions", default="", help=f"separadas por vírgula: {', '.join(RESTRICTIONS)}")
    p.add_argument("--price", default="media", choices=PRICES)
    p.add_argument("--city", default="São Paulo")
    p.add_argument("--user", default=None, help="id do usuário, ex.: u1")
    p.add_argument("--dish", default=None, help="fixa o prato pelo nome exato")
    p.add_argument("--dataset", default="toy", choices=sorted(DATASETS), help="base de dados: toy ou large")
    p.add_argument("--dry-run", action="store_true", help="só roda os recomendadores (sem LLM) e imprime JSON")
    return p.parse_args(argv)


def fail(message: str, code: int) -> int:
    """Print an error message to stderr and return the given exit code.

    Args:
        message: Text shown after the ``Erro:`` prefix.
        code: Exit code to hand back to the caller.

    Returns:
        ``code`` unchanged, so callers can write ``return fail(...)``.
    """
    print(f"Erro: {message}", file=sys.stderr)
    return code


def main(argv: list[str] | None = None) -> int:
    """Run the ``dinner-crew`` CLI.

    Validates the input, trains the food recommender, and then either prints the
    recommenders' output as JSON (``--dry-run``) or runs the CrewAI crew and prints
    its final answer.

    Args:
        argv: Arguments to parse, without the program name. ``None`` means ``sys.argv[1:]``.

    Returns:
        The process exit code:

        * ``0``: success.
        * ``1``: no dish fits the restrictions and ``--dish`` was not given.
        * ``2``: invalid input (unknown restriction or dish) or ``OPENAI_API_KEY`` is missing.
    """
    args = parse_args(argv)
    load_dotenv()

    prefs, restrictions = _csv(args.prefs), _csv(args.restrictions)
    invalid = [r for r in restrictions if r not in RESTRICTIONS]
    if invalid:
        return fail(f"restrição inválida {invalid}; use: {', '.join(RESTRICTIONS)}.", 2)

    # Check --dish against the CSV before training: it is cheap, and a typo fails fast.
    # The crew's tools read the dataset from the environment (see tools/recommender_tools.py).
    os.environ["DINNER_DATASET"] = args.dataset
    dishes = {d["name"]: d for d in load_dishes(dataset_dir(args.dataset))}
    if args.dish and args.dish not in dishes:
        return fail(f"prato desconhecido {args.dish!r}; opções: {', '.join(sorted(dishes))}.", 2)

    req = DinnerRequest(prefs, restrictions, args.price, args.city, args.user, args.dish)
    result = run_recommenders(req, Recommenders(args.dataset))
    if result["chosen_dish"] is None:
        print(result["food"]["warning"])
        return 1

    if args.dry_run:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if not os.getenv("OPENAI_API_KEY"):
        return fail("defina OPENAI_API_KEY no ambiente ou no arquivo .env.", 2)

    from dinner_crew.crew import DinnerCrew  # lazy: crewai import is slow

    # build_crew_inputs fills the {placeholders} in the YAML configs (see pipeline.py).
    inputs = build_crew_inputs(req)
    output = DinnerCrew().crew().kickoff(inputs=inputs)
    print(output.raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
