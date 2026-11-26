# Sobre os sistemas de recomendação usados

O projeto usa três bibliotecas — LightFM, implicit e Surprise — e cada uma está no agente cujo
**tipo de dado** ela modela melhor. Este é o ponto central: não existe "o melhor recomendador";
existe o recomendador adequado ao sinal que você tem.

## Os três tipos de sinal

| Sinal | Exemplo no projeto | O que significa a ausência | Biblioteca |
|---|---|---|---|
| **Explícito** | nota 1–5 de um restaurante | "não avaliou" — sem informação | Surprise |
| **Implícito** | quantas vezes um vinho foi pedido com um prato | "não pediu" — talvez não conheça, talvez não goste | implicit |
| **Interações + atributos** | curtidas de pratos + ingredientes do prato + preferências declaradas | pode ser compensada pelos atributos | LightFM |

Uma nota 2 é uma opinião negativa clara. Um vinho nunca pedido com um prato não é: pode ser
apenas desconhecido. Tratar os dois da mesma forma é um erro clássico, e é por isso que notas e
pedidos vão para modelos diferentes.

---

## Surprise — filtragem colaborativa sobre notas explícitas (restaurantes)

[Surprise](https://surpriselib.com/) é uma biblioteca acadêmica para avaliar e usar algoritmos de
predição de notas. O projeto usa `KNNWithMeans`, o "vizinhos mais próximos" com correção pela média.

**A ideia:** pessoas que concordaram no passado tendem a concordar no futuro. Para prever a nota
de `u1` para a Osteria, olhamos usuários que avaliam como `u1` e que já foram à Osteria.

**Similaridade (Pearson):** compara os usuários só nos restaurantes que ambos avaliaram, depois de
subtrair a média de cada um. Isso importa: um usuário que dá 5 para tudo que gosta e outro que dá 4
têm o mesmo gosto, só escalas diferentes. Sem centralizar, pareceriam diferentes.

**Predição:**

```text
nota_prevista(u, i) = média(u) + Σ sim(u,v) · (nota(v,i) − média(v)) / Σ sim(u,v)
```

somando sobre os `k = 3` vizinhos mais parecidos que avaliaram `i`. Em palavras: parta da média de
`u` e ajuste pelo quanto os vizinhos gostaram de `i` *acima ou abaixo da média deles*.

**Por que KNN e não SVD?** O SVD (fatoração de matrizes, também disponível no Surprise)
costuma prever melhor, mas sua explicação é "fatores latentes". O KNN permite dizer ao usuário
"pessoas parecidas com você (u2, u3) adoraram este lugar" — e um projeto didático precisa que o
agente consiga justificar a sugestão.

**Limitação — cold start:** um usuário sem notas não tem vizinhos. Por isso o recomendador cai
para a popularidade (nota média do restaurante) e avisa.

---

## implicit — ALS sobre feedback implícito (vinhos)

[implicit](https://github.com/benfred/implicit) é especializada em dados de comportamento:
cliques, compras, plays. O projeto usa `AlternatingLeastSquares` (ALS).

**A ideia:** fatorar a matriz prato×vinho em vetores latentes — cada prato e cada vinho vira um
vetor de 8 números — de forma que o produto escalar prato·vinho seja alto quando eles "combinam".
Pratos com padrões de pedido parecidos acabam com vetores parecidos.

**Confiança, não nota:** no modelo de Hu, Koren e Volinsky (a base do ALS implícito), cada célula
vira duas coisas: uma *preferência* binária (pediu ou não) e uma *confiança* que cresce com a
contagem (`1 + alpha·count`). Dez pedidos de Malbec com Bife ancho pesam mais que três pedidos de
Tannat. Células vazias têm preferência zero mas confiança baixa — o modelo não as trata como
rejeição forte.

**O truque do "prato como usuário":** a biblioteca fala em usuários e itens. Aqui, as "linhas" da
matriz são pratos. Pedir recomendações para um prato devolve vinhos que costumam sair com pratos
de vetor parecido — inclusive vinhos que nunca foram pedidos com *este* prato. `similar_users`
revela esses pratos parecidos, e o projeto os usa na explicação ("pratos com padrão de pedidos
parecido: Picanha na brasa, Kafta grelhada").

**Por que os cortes de relevância?** O ALS dá um score para *todo* vinho. Com poucos dados, a
cauda é ruído: um tinto encorpado podia aparecer em 3º lugar para Sushi com score 0,2. O corte em
30% do melhor score remove essa cauda, e o aviso de "sinal fraco" (melhor score abaixo de 0,2)
diz ao usuário quando nenhum vinho da faixa de preço tem afinidade real — em vez de fingir confiança.

**Isso substituiu regras de harmonização.** A primeira versão do projeto (feature 001) usava
regras explícitas ("carne vermelha + intensa → tinto encorpado"). As regras eram transparentes,
mas o conhecimento precisava ser escrito à mão. Com o ALS, o conhecimento de harmonização está
*implícito no histórico de pedidos*. É uma troca real: ganha-se a capacidade de aprender padrões
que ninguém escreveu, perde-se a explicação em forma de regra.

---

## LightFM — modelo híbrido (pratos)

[LightFM](https://making.lyst.com/lightfm/docs/home.html) combina filtragem colaborativa com
conteúdo. O projeto usa a perda WARP, que otimiza diretamente a ordem do ranking.

**A ideia:** em vez de aprender um vetor por usuário e um por prato, o LightFM aprende um vetor
por **feature**. Um prato é a soma dos vetores dos seus atributos (`attr:italiana`,
`attr:cogumelos`, `attr:cremoso`…) mais um vetor de identidade. Um usuário é a soma dos vetores
das suas preferências (`pref:massa`, `pref:tomate`…) mais um vetor de identidade. O treino ajusta
esses vetores para que usuários fiquem perto dos pratos que curtiram.

**O ganho — cold start resolvido:** como um usuário é a soma das suas features, um usuário que
nunca existiu pode ser montado na hora a partir de `--prefs`. A CLI faz exatamente isso: se você
passa `--prefs "massa,tomate"` sem `--user`, o recomendador cria um vetor com `pref:massa` e
`pref:tomate` e o compara com todos os pratos. Se você passa `--user u1`, a identidade de `u1` entra
também, e o histórico dele pesa na resposta.

**O lado colaborativo:** o modelo aprende que quem declara "cogumelos" (`u1`, `u8`) também curtiu
Salmão na manteiga de limão. Por isso, para "cogumelos, cremoso, ervas", o Salmão pode aparecer
acima do Risoto: não pelo ingrediente, mas porque pessoas com esse perfil curtiram os dois. Isso
é o comportamento esperado de um modelo híbrido, e é por isso que a explicação de cada item
diferencia "atributos em comum" de "padrão de curtidas de usuários com perfil parecido".

**Sobre os scores:** os valores do LightFM (muitas vezes negativos) não são probabilidades nem
notas. Só a ordem importa.

**Hiperparâmetros:** 16 dimensões, 150 épocas, taxa de aprendizado 0,05. Foram escolhidos
testando combinações nos dados toy e conferindo se os rankings faziam sentido (carne → Picanha,
Bife; peixe leve → Sushi). Com 8 usuários e 32 curtidas, valores muito pequenos de épocas deixavam
o modelo sem convergir, e a perda BPR colapsava para o mesmo ranking em qualquer consulta.

**Sobre o pacote:** o `lightfm` original (1.17, de 2023) não compila no Python 3.12. O projeto usa
o fork `rectools-lightfm`, mantido pela equipe do RecTools, com a mesma API (`import lightfm`).

---

## Comparação

| | Surprise (KNN) | implicit (ALS) | LightFM (híbrido) |
|---|---|---|---|
| Dado | notas explícitas | contagens implícitas | interações + atributos |
| Usuário novo | fallback por popularidade | n/a (o "usuário" é o prato) | resolvido pelas features |
| Item novo | sem notas → média global | sem pedidos → sinal fraco | resolvido pelas features |
| Explicação | vizinhos e similaridades | pratos parecidos, contagem | atributos em comum |
| Interpretação do score | nota prevista 1–5 | afinidade relativa | só a ordem |

## Alternativas consideradas

- **Surprise SVD** para restaurantes: melhor acurácia típica, explicação pior.
- **implicit BPR** para vinhos: instável com tão poucos dados.
- **LightFM para restaurantes**: possível, mas desperdiçaria o ponto forte do LightFM
  (features) num dado que só tem notas.
- **Manter os recomendadores escritos à mão** (TF-IDF, regras, CF com numpy): são mais
  transparentes para estudo, mas o objetivo da feature 002 era mostrar bibliotecas reais.
  O histórico dessa decisão está em [Sobre o Spec Kit neste projeto](spec-kit-no-projeto.md).
