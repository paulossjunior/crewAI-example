# Anatomia de um pedido: do texto ao plano de jantar

Este texto acompanha um único pedido real, do momento em que o usuário digita até o plano aparecer
na tela, para mostrar o papel de cada peça. O pedido é:

> *quero massa com tomate, sou u1* — na base `toy`, cidade padrão São Paulo, faixa de preço padrão
> `media`.

## 1. Entender o pedido (sem IA)

A primeira coisa que acontece não envolve nenhum modelo de linguagem. O `RequestParser`
(`intake.py`) normaliza o texto (minúsculas, sem acentos) e procura palavras conhecidas:

- `massa` e `tomate` estão no vocabulário de preferências (que vem dos perfis em
  `user_profiles.csv`) → viram `preferences`;
- `u1` casa com o padrão de id de usuário → vira `user_id`;
- nada indica preço, cidade ou restrição → valem os padrões (ou o que já estava no pedido anterior).

O resultado é um `DinnerRequest` — a mesma estrutura que a CLI monta a partir das opções. Daqui em
diante, CLI e interface seguem o mesmo caminho (`pipeline.py`).

Por que regras e não um LLM aqui? Ver [Sobre a interface de chat](interface-de-chat.md).

## 2. Escolher o prato — LightFM

O `FoodRecommender` monta, na hora, um "usuário" a partir de duas features ativas: `pref:massa` e
`pref:tomate`, mais a identidade de `u1` (que tem histórico de curtidas). O modelo compara esse
vetor com o de cada prato — que é a soma das features dos seus atributos — e devolve:

| Prato | Score | Por quê |
|---|---|---|
| **Spaghetti al pomodoro** | 0,13 | atributos em comum: massa, tomate |
| Fettuccine ao funghi | −0,15 | atributo em comum: massa |
| Lasanha à bolonhesa | −0,55 | atributos em comum: massa, tomate |

A Lasanha tem os dois termos, mas fica atrás do Fettuccine: o lado colaborativo do LightFM pesa o
histórico de `u1` e de quem tem perfil parecido. Os scores negativos não são problema — só a ordem
importa. O primeiro da lista é o prato escolhido.

## 3. Harmonizar o vinho — implicit

O `WineRecommender` olha para a linha do Spaghetti na matriz prato × vinho de pedidos. O ALS já
aprendeu um vetor para cada prato e cada vinho; o produto deles dá a afinidade:

| Vinho | Score | Por quê |
|---|---|---|
| **Chianti Classico** (R$ 139) | 0,99 | pedido 9× com este prato |
| Rosé da Provence (R$ 145) | 0,91 | pedido 2× com este prato |
| Malbec de Mendoza (R$ 119) | 0,46 | nunca pedido com este prato — mas sai com pratos parecidos (Lasanha, Enchiladas) |

O Malbec mostra o que o ALS acrescenta a uma simples contagem: ele recomenda algo que nunca foi
pedido com o Spaghetti porque pratos com padrão de pedidos parecido costumam levá-lo. Antes de
ranquear, o recomendador filtrou só vinhos da faixa `media`.

## 4. Indicar o restaurante — Surprise

O prato é italiano, então o `RestaurantRecommender` procura restaurantes italianos em São Paulo que
`u1` ainda não avaliou: Osteria del Porto e Cantina da Vila. Para cada um, o KNN acha os usuários
que avaliam parecido com `u1` (Pearson): `u2` (0,94) e `u3` (0,79). Os dois adoraram a Osteria e não
gostaram da Cantina:

| Restaurante | Nota prevista | Ticket médio |
|---|---|---|
| **Osteria del Porto** | 4,48 | R$ 230 |
| Cantina da Vila | 2,39 | R$ 65 |

## 5. Escrever o plano

Aqui os dois modos se separam.

**Sem IA:** `pipeline.summarize()` preenche um template com os dados das três recomendações e
calcula o total prato + vinho (R$ 42 + R$ 139 = R$ 181). `render_plan()` acrescenta as seções com
ingredientes, uva, preços, alternativas e a linha **Recomendador**. Leva menos de um segundo.

**Com IA:** o pedido vira um dicionário de placeholders (`build_crew_inputs`) e a crew roda em
sequência:

1. **Food Sommelier** lê sua tarefa, chama `food_lightfm_recommender` com `["massa", "tomate"]` e
   `u1`, recebe o JSON do passo 2 e escreve um relatório curto.
2. **Wine Sommelier** recebe esse relatório como `context`, extrai o nome exato do prato, chama
   `wine_implicit_recommender` e relata o vinho com uva, preço e justificativa.
3. **Dinner Concierge** recebe o relatório do prato, chama `restaurant_surprise_recommender` com a
   culinária e a cidade.
4. **Anfitrião** não tem ferramenta: recebe os três relatórios e escreve o resumo caloroso e as
   seções finais. O prompt proíbe acrescentar itens, ingredientes ou preços que não estejam nos
   relatórios.

Os itens do plano são os mesmos do modo sem IA — vêm das mesmas ferramentas. O que muda é o texto.

## 6. Registrar (se o Langfuse estiver ligado)

No modo com IA, tudo isso fica gravado como um trace `dinner-plan`: cada agente, cada chamada de
ferramenta com seus argumentos e resposta, e cada chamada ao modelo com prompt, tokens e custo. Ver
[Sobre a observabilidade](observabilidade.md).

## O que este caminho mostra

- **Decidir e redigir são separados.** Os recomendadores decidem *o quê*; os agentes decidem *como
  dizer*. Por isso os itens são iguais nos dois modos e repetíveis entre execuções.
- **Cada etapa depende da anterior.** O vinho depende do prato; o restaurante, da culinária do prato.
  É isso que torna o processo sequencial a escolha natural.
- **Cada biblioteca responde a um tipo de dado diferente** — curtidas e atributos, pedidos, notas.
  Ver [Sobre os sistemas de recomendação](sistemas-de-recomendacao.md).
