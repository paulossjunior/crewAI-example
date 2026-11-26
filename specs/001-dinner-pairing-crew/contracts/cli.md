# Contract: CLI

```text
uv run dinner-crew [--prefs TERMS] [--restrictions LIST] [--price {baixa,media,alta}]
                   [--city CITY] [--user USER_ID] [--dish NAME] [--dry-run]
```

| Option | Format | Default |
|---|---|---|
| `--prefs` | comma-separated terms, e.g. `"cogumelos,cremoso,ervas"` | empty |
| `--restrictions` | comma-separated, from restriction vocabulary | empty |
| `--price` | price tier | `media` |
| `--city` | exact city name | `São Paulo` |
| `--user` | user id, e.g. `u1` | none (new user) |
| `--dish` | exact dish name to pin | none |
| `--dry-run` | run the 3 recommenders only, print their JSON, no LLM | off |

## Behavior

- **Success**: prints markdown plan to stdout, exit code 0. Plan has headings
  `## 🍽️ Prato`, `## 🍷 Vinho`, `## 📍 Restaurante`, each naming its technique.
- **`OPENAI_API_KEY` missing** (and not `--dry-run`): stderr
  `Erro: defina OPENAI_API_KEY no ambiente ou no arquivo .env.`, exit code 2.
- **Invalid price / restriction / unknown `--dish`**: stderr message listing valid values,
  exit code 2.
- **No dish satisfies restrictions**: prints message, exit code 1, crew not run.
