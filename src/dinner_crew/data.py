"""Loaders for the datasets in ``data/`` (``toy``) and ``data/large/`` (``large``).

Each loader reads one CSV with ``csv.DictReader`` and returns its rows. Cells holding lists are
``;``-separated and are split into ``list[str]``; numeric columns are cast to ``int`` where noted.
All other values are returned as strings.

Which dataset is read: an explicit ``data_dir`` argument wins; otherwise the ``DINNER_DATASET``
environment variable (``toy`` or ``large``, default ``toy``) picks it.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

# src/dinner_crew/data.py -> parents[2] is the repository root.
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATASETS = {"toy": DATA_DIR, "large": DATA_DIR / "large"}


def dataset_dir(name: str | None = None) -> Path:
    """Directory of a named dataset.

    Args:
        name: ``"toy"`` or ``"large"``. Defaults to ``$DINNER_DATASET``, then ``"toy"``.

    Returns:
        The dataset directory.

    Raises:
        ValueError: If the name is unknown.
    """
    name = name or os.getenv("DINNER_DATASET") or "toy"
    if name not in DATASETS:
        raise ValueError(f"Base desconhecida: {name!r}; use {sorted(DATASETS)}")
    return DATASETS[name]


def _read_csv(name: str, data_dir: Path | None = None) -> list[dict]:
    """Read a CSV file into a list of row dicts.

    Args:
        name: File name relative to the data directory.
        data_dir: Directory containing the file. Defaults to ``dataset_dir()``.

    Returns:
        One dict per row, keyed by header, with string values.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    with open((data_dir or dataset_dir()) / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _split(value: str) -> list[str]:
    """Split a ``;``-separated cell into a list of trimmed, non-empty strings.

    Args:
        value: Raw cell value, e.g. ``"a; b;;c"``.

    Returns:
        The stripped parts with empty entries dropped, e.g. ``["a", "b", "c"]``.
    """
    return [v.strip() for v in value.split(";") if v.strip()]


def load_dishes(data_dir: Path | None = None) -> list[dict]:
    """Load ``dishes.csv``.

    Args:
        data_dir: Directory containing the CSV. Defaults to ``dataset_dir()``.

    Returns:
        Dish rows, with ``tags``, ``suitable_for`` and ``ingredients`` split into lists of strings
        and ``price_brl`` cast to ``int``.

    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If the ``tags`` or ``suitable_for`` column is missing.
    """
    rows = _read_csv("dishes.csv", data_dir)
    for row in rows:
        row["tags"] = _split(row["tags"])
        row["suitable_for"] = _split(row["suitable_for"])
        row["ingredients"] = _split(row["ingredients"])
        row["price_brl"] = int(row["price_brl"])
    return rows


def load_wines(data_dir: Path | None = None) -> list[dict]:
    """Load ``wines.csv``.

    Args:
        data_dir: Directory containing the CSV. Defaults to ``dataset_dir()``.

    Returns:
        Wine rows, with ``price_brl`` (bottle price) cast to ``int``.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    rows = _read_csv("wines.csv", data_dir)
    for row in rows:
        row["price_brl"] = int(row["price_brl"])
    return rows


def load_user_profiles(data_dir: Path | None = None) -> dict[str, list[str]]:
    """Load ``user_profiles.csv`` as a user-to-preferences mapping.

    Args:
        data_dir: Directory containing the CSV. Defaults to ``dataset_dir()``.

    Returns:
        Mapping from ``user_id`` to that user's list of preference tags.

    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If the ``user_id`` or ``preferences`` column is missing.
    """
    return {r["user_id"]: _split(r["preferences"]) for r in _read_csv("user_profiles.csv", data_dir)}


def load_dish_likes(data_dir: Path | None = None) -> list[dict]:
    """Load ``dish_likes.csv`` (user-dish interactions).

    Args:
        data_dir: Directory containing the CSV. Defaults to ``dataset_dir()``.

    Returns:
        Interaction rows with string values.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    return _read_csv("dish_likes.csv", data_dir)


def load_wine_orders(data_dir: Path | None = None) -> list[dict]:
    """Load ``wine_orders.csv`` (implicit feedback: how often each wine was ordered).

    Args:
        data_dir: Directory containing the CSV. Defaults to ``dataset_dir()``.

    Returns:
        Order rows, with ``count`` cast to ``int``.

    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If the ``count`` column is missing.
        ValueError: If a ``count`` value is not an integer.
    """
    rows = _read_csv("wine_orders.csv", data_dir)
    for row in rows:
        row["count"] = int(row["count"])
    return rows


def load_restaurants(data_dir: Path | None = None) -> list[dict]:
    """Load ``restaurants.csv``.

    Args:
        data_dir: Directory containing the CSV. Defaults to ``dataset_dir()``.

    Returns:
        Restaurant rows, with ``avg_ticket_brl`` (average spend per person) cast to ``int``.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    rows = _read_csv("restaurants.csv", data_dir)
    for row in rows:
        row["avg_ticket_brl"] = int(row["avg_ticket_brl"])
    return rows


def load_ratings(data_dir: Path | None = None) -> list[dict]:
    """Load ``ratings.csv`` (explicit user ratings).

    Args:
        data_dir: Directory containing the CSV. Defaults to ``dataset_dir()``.

    Returns:
        Rating rows, with ``rating`` cast to ``int``.

    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If the ``rating`` column is missing.
        ValueError: If a ``rating`` value is not an integer.
    """
    rows = _read_csv("ratings.csv", data_dir)
    for row in rows:
        row["rating"] = int(row["rating"])
    return rows
