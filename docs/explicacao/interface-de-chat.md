# Sobre a interface de chat

## Por que uma interface de chat

A CLI exige saber de antemão quais opções existem (`--prefs`, `--restrictions`, `--price`…). Um
chat permite pedir do jeito que se fala — "quero algo vegetariano com cogumelos, sou u1" — e
refinar aos poucos — "e um vinho mais barato?". Isso combina com a ideia de uma crew de agentes
conversando com alguém.

A interface foi feita em [Streamlit](https://streamlit.io) porque é Python puro, reaproveita todo o
código do projeto e cabe em um arquivo (`app.py`). As alternativas avaliadas foram a pilha oficial
do CrewAI para front-end (AG-UI + CopilotKit, que exige um projeto React) e interfaces de terceiros
em versão alfa.

## Por que entender o pedido com regras, e não com IA

Seria natural usar o próprio LLM para transformar o texto em preferências. O projeto não faz isso, e
o `RequestParser` usa palavras-chave e expressões regulares. Os motivos:

- **funciona offline** — o modo sem IA precisa entender o pedido também;
- **é previsível e testável** — "carne" nunca vira "caro", e há testes para isso;
- **o vocabulário é fechado** — os recomendadores só conhecem os termos que existem nos dados; um
  LLM poderia extrair "lasanha da vovó", que nenhum modelo saberia usar.

O preço é a rigidez: termos fora do vocabulário são ignorados, e frases como "nada de carne" não são
entendidas como restrição. Para um exemplo didático, previsibilidade vale mais que flexibilidade.
Por isso cada resposta começa com "Entendi: …" — o usuário vê exatamente o que foi extraído, e o
painel lateral mostra (e permite corrigir) o pedido inteiro.

## Por que o pedido "lembra" do contexto

Cada mensagem é interpretada **por cima do pedido anterior**: o que a mensagem menciona muda, o resto
fica. "e um vinho mais caro?" só mexe no preço. Isso exige uma regra para palavras como "vinho",
"prato" e "jantar": elas falam *sobre* o pedido, não sobre gosto, e por isso nunca viram
preferência — mesmo que algum perfil de usuário liste "vinho" como preferência (o usuário `u8`
lista, e isso causou um bug antes da regra existir).

## Como o painel lateral acompanha o chat

O Streamlit reexecuta o script inteiro a cada interação, e não permite mudar o valor de um widget
depois que ele foi desenhado naquela execução. Para que o pedido interpretado apareça no painel na
mesma resposta, a mensagem do chat é lida **no começo** do script, antes do painel ser desenhado; o
pedido resultante é escrito nas chaves dos widgets, e só então o painel é desenhado. Ao trocar de
base de dados, valores que não existem na nova base (um usuário `u1` na base grande, por exemplo)
são limpos pelo mesmo motivo.

## Por que não mexer enquanto a IA trabalha

No modo com IA, a crew leva de 30 a 60 segundos (quatro agentes, várias chamadas ao modelo). Como o
Streamlit reexecuta o script a cada interação, digitar ou clicar nesse intervalo interrompe a
execução em andamento, e a crew recomeça do zero. Na primeira versão isso parecia um travamento: só
havia um spinner, e quem esperava acabava clicando.

A solução foi tornar a espera visível: um painel de status é atualizado pelo `task_callback` do
CrewAI a cada agente que termina, com um aviso para não interagir. Uma alternativa mais robusta seria
rodar a crew numa thread separada e consultar o resultado periodicamente, o que deixaria a página
utilizável durante a espera, ao custo de mais complexidade.

## Os dois modos

| | Sem IA | Com IA |
|---|---|---|
| Quem escolhe os itens | os três recomendadores | os mesmos três recomendadores, chamados pelos agentes |
| Quem escreve o texto | um template (`pipeline.summarize`) | o agente Anfitrião |
| Tempo | ~1 s | 30–60 s |
| Precisa | nada | chave da OpenAI |
| Aparece no Langfuse | não | sim |

Como os itens vêm sempre dos mesmos recomendadores, comparar os dois modos isola o que o LLM
acrescenta: a redação, não as escolhas. Ver [Anatomia de um pedido](anatomia-de-um-pedido.md).
