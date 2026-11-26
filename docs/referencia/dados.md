# Referência dos arquivos de dados

Todos em `data/`, CSV UTF-8 com cabeçalho. Listas dentro de uma célula usam `;`. Carregados por
`src/dinner_crew/data.py`.

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

## `dishes.csv` — catálogo de pratos (19 linhas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `name` | texto, único | nome do prato; usado como id em todos os arquivos |
| `cuisine` | texto | culinária; liga o prato a `restaurants.csv` |
| `protein`, `sauce`, `intensity` | vocabulário | atributos; viram features do LightFM |
| `tags` | lista `;` | ingredientes e sabores; viram features do LightFM |
| `suitable_for` | lista `;` | restrições que o prato atende; vazio = nenhuma |

Usado por: LightFM (features de item), implicit (linhas da matriz), CLI (validação de `--dish`).

## `user_profiles.csv` — perfis de preferência (8 linhas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `user_id` | texto, único | `u1` … `u8` |
| `preferences` | lista `;` | termos de preferência; viram features `pref:<termo>` do LightFM |

Os termos daqui formam o vocabulário aceito em `--prefs`.

## `dish_likes.csv` — curtidas (32 linhas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `user_id` | texto | usuário de `user_profiles.csv` |
| `dish` | texto | prato de `dishes.csv` |

Interação binária (curtiu). Usado por: LightFM (interações) e fallback de popularidade de pratos.

## `wines.csv` — catálogo de vinhos (16 linhas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `name` | texto, único | nome do vinho |
| `type`, `body`, `price` | vocabulário | `price` é o filtro de `--price` |
| `notes` | texto | descrição livre exibida nos atributos |

## `wine_orders.csv` — pedidos prato×vinho (57 linhas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `dish` | texto | prato de `dishes.csv` |
| `wine` | texto | vinho de `wines.csv` |
| `count` | inteiro > 0 | vezes que o vinho foi pedido com o prato |

Feedback implícito do implicit (ALS). Ausência de linha = nenhum pedido (não significa rejeição).

## `restaurants.csv` — restaurantes (13 linhas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `name` | texto, único | nome do restaurante |
| `cuisine` | texto | igual a `dishes.csv.cuisine` |
| `city` | texto | comparado exatamente com `--city` |
| `neighborhood` | texto | exibido nos atributos |
| `price` | vocabulário | exibido; não filtra |

## `ratings.csv` — notas explícitas (46 linhas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `user_id` | texto | usuário (não precisa existir em `user_profiles.csv`) |
| `restaurant` | texto | restaurante de `restaurants.csv` |
| `rating` | inteiro 1–5 | nota |

Uma linha por par (usuário, restaurante). Lido diretamente pelo Surprise
(`Dataset.load_from_file`), por isso nomes de restaurante não podem conter vírgula.
