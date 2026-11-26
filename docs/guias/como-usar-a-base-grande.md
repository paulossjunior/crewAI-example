# Como usar (e regenerar) a base de dados grande

O projeto tem duas bases com o mesmo formato de arquivos:

| Base | Pasta | Conteúdo |
|---|---|---|
| `toy` (padrão) | `data/` | 19 pratos, 16 vinhos, 13 restaurantes, 8 usuários — escrita à mão |
| `large` | `data/large/` | ~176 pratos, ~149 vinhos, ~400 restaurantes em 8 cidades, 1.500 usuários, ~15 mil curtidas, ~37 mil notas, ~1.400 pares prato×vinho — gerada por script |

## Escolher a base

**CLI:**

```bash
uv run dinner-crew --prefs "peixe,cru" --city Recife --user u0100 --dataset large --dry-run
```

**Interface:** no painel lateral, em **Base de dados**, escolha **large (grande)**. Usuário, cidade
e preferências que não existirem na nova base são limpos automaticamente.

**Variável de ambiente** (vale para CLI, tools da crew e testes):

```bash
DINNER_DATASET=large uv run dinner-crew --prefs "curry" --dry-run
```

A opção `--dataset` tem prioridade e também define `DINNER_DATASET` para as tools da crew.

## Encontrar ids e nomes válidos na base large

- Usuários: `u0001` … `u1500`.
- Cidades: São Paulo, Rio de Janeiro, Belo Horizonte, Curitiba, Porto Alegre, Salvador, Recife,
  Brasília.
- Pratos: `cut -d, -f1 data/large/dishes.csv | sort | less`.

## Mudar a base grande

Não edite `data/large/*.csv` à mão: um teste (`test_committed_data_matches_generator`) falha se os
arquivos não forem exatamente a saída do script. Edite `scripts/generate_large_data.py` e regenere:

```bash
uv run python scripts/generate_large_data.py
uv run pytest
```

O que dá para ajustar no script:

| Quer mudar | Edite |
|---|---|
| pratos (culinárias, bases, proteínas) | `BASES`, `P` |
| preço dos pratos | `CUISINE_PRICE`, `PROTEIN_PRICE` |
| vinhos e preços | `GRAPES`, `LEVELS`, `WINE_PRICE`, `GRAPE_OF` |
| quais vinhos "saem" com quais pratos | `RULES` (regras de harmonização usadas para simular pedidos) |
| cidades, bairros, nomes de restaurantes | `CITIES`, `CITY_WEIGHT`, `NAMES`, `TICKET` |
| número e perfis de usuários | `N_USERS`, `ARCHETYPES` |
| semente | `SEED` |

Depois de regenerar, alguns testes de `tests/test_large_dataset.py` que conferem resultados
específicos (ex.: "Parrilla de carne → tinto encorpado") podem precisar de ajuste.
