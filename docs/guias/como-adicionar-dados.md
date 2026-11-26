# Como adicionar pratos, vinhos, restaurantes e usuários

Todos os dados ficam em `data/`. Os modelos são treinados a cada execução, então basta editar os
CSVs e rodar de novo. Formato de cada coluna: [Referência dos arquivos de dados](../referencia/dados.md).

Depois de qualquer alteração, rode `uv run pytest`. Alguns testes verificam rankings específicos
dos dados atuais (ex.: "Osteria del Porto em 1º para u1"); se você mudou dados de propósito,
ajuste esses testes.

## Adicionar um prato

1. Acrescente uma linha em `data/dishes.csv`. Use os vocabulários de `protein`, `sauce` e
   `intensity`; em `suitable_for`, liste só as restrições que o prato realmente atende.

   ```csv
   Nhoque ao sugo,italiana,vegetal,tomate,leve,massa;batata;tomate;manjericão,vegetariano
   ```

2. Acrescente de 2 a 4 linhas em `data/wine_orders.csv` com os vinhos que costumam ser pedidos
   com ele. **Sem pedidos, o implicit não tem sinal para o prato** e o Wine Sommelier vai devolver
   um aviso de "sinal fraco".

   ```csv
   Nhoque ao sugo,Chianti Classico,6
   Nhoque ao sugo,Rosé da Provence,3
   ```

3. (Opcional) Faça algum usuário curti-lo em `data/dish_likes.csv`. Sem curtidas, o LightFM ainda
   recomenda o prato pelos atributos, mas sem reforço colaborativo.

4. Se a culinária é nova, adicione ao menos um restaurante dela (seção abaixo); senão o Concierge
   devolve "Nenhum restaurante disponível".

## Adicionar um vinho

1. Acrescente em `data/wines.csv` (`type`, `body` e `price` dos vocabulários).
2. Acrescente linhas em `data/wine_orders.csv` ligando o vinho a pratos. Um vinho sem nenhum
   pedido só aparece se o modelo inferir afinidade, o que é raro com poucos dados.

## Adicionar um restaurante

1. Acrescente em `data/restaurants.csv`. A `cuisine` deve ser igual (inclusive acentos) à usada em
   `dishes.csv`, e `city` igual ao que será passado em `--city`.
2. Acrescente notas em `data/ratings.csv`. Sem notas, o restaurante aparece com a média global de
   todas as notas e com aviso de fallback.

## Adicionar um usuário

Um usuário existe em até três arquivos, cada um alimentando um recomendador:

| Arquivo | Alimenta | Efeito |
|---|---|---|
| `data/user_profiles.csv` | LightFM | termos de preferência do usuário (features) |
| `data/dish_likes.csv` | LightFM | pratos curtidos (interações) |
| `data/ratings.csv` | Surprise | notas 1–5 de restaurantes |

Para que `--user u9` personalize **pratos e restaurantes**, adicione-o a `user_profiles.csv` e
`dish_likes.csv` (LightFM) e dê ao menos 3 notas em `ratings.csv` que coincidam com restaurantes
avaliados por outros usuários (o Surprise precisa de itens em comum para calcular a correlação de
Pearson).

```csv
# user_profiles.csv
u9,sushi;peixe;leve
# dish_likes.csv
u9,Sushi de salmão
u9,Tempurá de legumes
# ratings.csv
u9,Sakura Liberdade,5
u9,Izakaya Kaze,5
u9,Trattoria Nonna Lina,2
```

## Verificar o efeito

```bash
uv run dinner-crew --prefs "sushi" --user u9 --dry-run
```
