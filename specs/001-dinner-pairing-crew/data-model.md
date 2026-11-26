# Data Model: Dinner Pairing Crew

All data lives in `data/` (constitution III). Categorical vocabularies are fixed below.

## Vocabularies

| Field | Values |
|---|---|
| `protein` | `carne_vermelha`, `ave`, `porco`, `peixe`, `frutos_do_mar`, `vegetal`, `queijo` |
| `sauce` | `cremoso`, `tomate`, `leve`, `picante`, `intenso`, `doce` |
| `intensity` | `leve`, `media`, `intensa` |
| `price` | `baixa`, `media`, `alta` (ordered) |
| `restrictions` | `vegetariano`, `vegano`, `sem_gluten`, `sem_lactose` |
| wine `type` | `tinto`, `branco`, `rose`, `espumante` |
| wine `body` | `leve`, `medio`, `encorpado` |

## Dish — `data/dishes.csv`

| Column | Type | Notes |
|---|---|---|
| `name` | str, unique | display name, used as id |
| `cuisine` | str | e.g. `italiana`, `japonesa`, `brasileira` |
| `protein`, `sauce`, `intensity` | vocab | used by wine rules |
| `tags` | `;`-separated str | flavor/ingredient terms (content-based features) |
| `suitable_for` | `;`-separated restrictions | dish is OK for these restrictions |

Validation: a dish is eligible iff every user restriction ∈ `suitable_for`.

## Wine — `data/wines.csv`

`name` (unique), `type`, `body`, `price`, `notes`.

## PairingRule — `data/pairing_rules.json`

```json
{"id": "R1", "when": {"protein": "carne_vermelha", "intensity": "intensa"},
 "recommend": {"types": ["tinto"], "bodies": ["encorpado"]},
 "why": "Taninos de tintos encorpados equilibram a gordura e intensidade da carne vermelha."}
```

`when` keys ⊆ {`protein`, `sauce`, `intensity`}, non-empty. Specificity = `len(when)`.

## Restaurant — `data/restaurants.csv`

`name` (unique), `cuisine`, `city`, `neighborhood`, `price`.

## Rating — `data/ratings.csv`

`user_id`, `restaurant` (→ Restaurant.name), `rating` (int 1–5). One row per (user, restaurant).
Users are implicit (ids `u1`…`u8`).

## DinnerRequest (runtime)

| Field | Type | Default |
|---|---|---|
| `preferences` | list[str] | `[]` |
| `restrictions` | list[restriction] | `[]` |
| `price` | price | `media` |
| `city` | str | `São Paulo` |
| `user_id` | str \| None | `None` |
| `dish` | str \| None | pins dish (skips choosing 1st) |

## Recommendation (runtime, returned by every recommender)

```text
Recommendation
  technique: "content-based" | "knowledge-based" | "collaborative-filtering"
  items: list[Item]            # max 3, ordered by score desc, ties by name
  warning: str | None          # fallback / relaxation notice

Item
  name: str                    # exists in data
  score: float
  explanation: str             # matched attributes / fired rules / similar users
  attributes: dict             # e.g. cuisine, type/body/price, city
```

## Relationships

Dish.cuisine ↔ Restaurant.cuisine (restaurant filter) · Dish(protein,sauce,intensity) →
PairingRule.when → Wine(type,body) · Rating(user, restaurant) → CF matrix.
