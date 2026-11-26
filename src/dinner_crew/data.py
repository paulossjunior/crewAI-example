"""Loaders for the toy datasets in ``data/``."""

from __future__ import annotations

import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _read_csv(name: str, data_dir: Path | None = None) -> list[dict]:
    with open((data_dir or DATA_DIR) / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _split(value: str) -> list[str]:
    return [v.strip() for v in value.split(";") if v.strip()]


def load_dishes(data_dir: Path | None = None) -> list[dict]:
    rows = _read_csv("dishes.csv", data_dir)
    for row in rows:
        row["tags"] = _split(row["tags"])
        row["suitable_for"] = _split(row["suitable_for"])
    return rows


def load_wines(data_dir: Path | None = None) -> list[dict]:
    return _read_csv("wines.csv", data_dir)


def load_user_profiles(data_dir: Path | None = None) -> dict[str, list[str]]:
    return {r["user_id"]: _split(r["preferences"]) for r in _read_csv("user_profiles.csv", data_dir)}


def load_dish_likes(data_dir: Path | None = None) -> list[dict]:
    return _read_csv("dish_likes.csv", data_dir)


def load_wine_orders(data_dir: Path | None = None) -> list[dict]:
    rows = _read_csv("wine_orders.csv", data_dir)
    for row in rows:
        row["count"] = int(row["count"])
    return rows


def load_restaurants(data_dir: Path | None = None) -> list[dict]:
    return _read_csv("restaurants.csv", data_dir)


def load_ratings(data_dir: Path | None = None) -> list[dict]:
    rows = _read_csv("ratings.csv", data_dir)
    for row in rows:
        row["rating"] = int(row["rating"])
    return rows
