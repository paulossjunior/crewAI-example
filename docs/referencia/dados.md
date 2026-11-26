# Referência dos arquivos de dados

CSV UTF-8 com cabeçalho; listas dentro de uma célula usam `;`. Carregados por
`src/dinner_crew/data.py`. Duas bases com os mesmos arquivos e colunas:

| Base | Pasta | Origem |
|---|---|---|
| `toy` | `data/` | escrita à mão (contagens abaixo) |
| `large` | `data/large/` | gerada por `scripts/generate_large_data.py`, semente 42 |

A base é escolhida por `--dataset`, pelo seletor da interface ou por `DINNER_DATASET`.

## Vocabulários

Definidos em `src/dinner_crew/models.py`.

| Campo | Valores |
|---|---|
| `protein` | `carne_vermelha`, `ave`, `porco`, `peixe`, `frutos_do_mar`, `vegetal`, `queijo` |
| `sauce` | `cremoso`, `tomate`, `leve`, `picante`, `intenso`, `doce` |
| `intensity` | `leve`, `media`, `intensa` |
| `price` | `baixa`, `media`, `alta` (ordenado) |
| restrições | `vegetariano`, `vegano`, `sem_gluten`, `sem_lactose` |
| vinho `type` | `tinto`, `branco`, `rose`, `espumante` |
| vinho `body` | `leve`, `medio`, `encorpado` |

## `dishes.csv` — catálogo de pratos (toy: 19 · large: 176)

| Coluna | Tipo | Descrição |
|---|---|---|
| `name` | texto, único | nome do prato; usado como id em todos os arquivos |
| `cuisine` | texto | culinária; liga o prato a `restaurants.csv` |
| `protein`, `sauce`, `intensity` | vocabulário | atributos; viram features do LightFM |
| `tags` | lista `;` | ingredientes e sabores; viram features do LightFM |
| `suitable_for` | lista `;` | restrições que o prato atende; vazio = nenhuma |
| `ingredients` | lista `;` | ingredientes legíveis, exibidos no plano |
| `price_brl` | inteiro | preço do prato em reais |

Usado por: LightFM (features de item), implicit (linhas da matriz), CLI (validação de `--dish`).

## `user_profiles.csv` — perfis de preferência (toy: 8 · large: 1.500)

| Coluna | Tipo | Descrição |
|---|---|---|
| `user_id` | texto, único | toy: `u1` … `u8` · large: `u0001` … `u1500` |
| `preferences` | lista `;` | termos de preferência; viram features `pref:<termo>` do LightFM |

Os termos daqui formam o vocabulário aceito em `--prefs`.

## `dish_likes.csv` — curtidas (toy: 32 · large: ~14,9 mil)

| Coluna | Tipo | Descrição |
|---|---|---|
| `user_id` | texto | usuário de `user_profiles.csv` |
| `dish` | texto | prato de `dishes.csv` |

Interação binária (curtiu). Usado por: LightFM (interações) e fallback de popularidade de pratos.

## `wines.csv` — catálogo de vinhos (toy: 16 · large: 149)

| Coluna | Tipo | Descrição |
|---|---|---|
| `name` | texto, único | nome do vinho |
| `type`, `body`, `price` | vocabulário | `price` é o filtro de `--price` |
| `notes` | texto | descrição livre exibida nos atributos |
| `grape` | texto | uva(s) |
| `price_brl` | inteiro | preço da garrafa em reais |

## `wine_orders.csv` — pedidos prato×vinho (toy: 57 · large: ~1,4 mil)

| Coluna | Tipo | Descrição |
|---|---|---|
| `dish` | texto | prato de `dishes.csv` |
| `wine` | texto | vinho de `wines.csv` |
| `count` | inteiro > 0 | vezes que o vinho foi pedido com o prato |

Feedback implícito do implicit (ALS). Ausência de linha = nenhum pedido (não significa rejeição).

## `restaurants.csv` — restaurantes (toy: 13 · large: 404, em 8 cidades)

| Coluna | Tipo | Descrição |
|---|---|---|
| `name` | texto, único | nome do restaurante |
| `cuisine` | texto | igual a `dishes.csv.cuisine` |
| `city` | texto | comparado exatamente com `--city` |
| `neighborhood` | texto | exibido nos atributos |
| `price` | vocabulário | exibido; não filtra |
| `avg_ticket_brl` | inteiro | ticket médio por pessoa em reais |

## `ratings.csv` — notas explícitas (toy: 46 · large: ~37 mil)

| Coluna | Tipo | Descrição |
|---|---|---|
| `user_id` | texto | usuário (não precisa existir em `user_profiles.csv`) |
| `restaurant` | texto | restaurante de `restaurants.csv` |
| `rating` | inteiro 1–5 | nota |

Uma linha por par (usuário, restaurante). Lido diretamente pelo Surprise
(`Dataset.load_from_file`), por isso nomes de restaurante não podem conter vírgula.
