# Referência das telas da interface

Capturas da interface Streamlit (`src/dinner_crew/app.py`) e do Langfuse, feitas na aplicação
rodando via Docker Compose, na base `toy`, com o pedido *quero massa com tomate, sou u1*. Como usar
cada recurso: [Como usar a interface](../guias/como-usar-a-interface.md).

## Tela inicial

![Tela inicial: painel lateral com modo, base, usuário, cidade, faixa de preço, restrições e preferências; à direita, a saudação com exemplos de pedido e a caixa de chat](../assets/telas/01-tela-inicial.png)

| Elemento | Chave de estado | Valor inicial |
|---|---|---|
| **Modo** | `mode` | Sem IA (offline) |
| **Base de dados** | `dataset` | toy (pequena) — a legenda abaixo mostra pratos, vinhos, restaurantes e usuários da base |
| **Usuário** | `user` | (novo usuário) |
| **Cidade** | `city` | São Paulo |
| **Faixa de preço** | `price` | media |
| **Restrições** | `restrictions` | nenhuma |
| **Preferências** | `preferences` | nenhuma; as opções são o vocabulário dos perfis da base |
| **Recomendar com estes filtros** | — | refaz o plano com o painel atual, sem mensagem |
| **Nova conversa** | — | limpa histórico, usuário, preferências, restrições, prato fixado, preço e cidade |
| Caixa de chat | `chat_input` | pedido em texto livre |

## Resposta no modo sem IA — resumo

![Resposta sem IA: a linha Entendi, o Resumo do anfitrião com prato, vinho, restaurante e total, e o painel lateral já preenchido com u1, massa e tomate](../assets/telas/02-pedido-sem-ia.png)

| Parte | Origem |
|---|---|
| *Entendi: …* | `RequestParser.parse` — o que esta mensagem mudou no pedido |
| **Resumo do anfitrião** | `pipeline.summarize` — template; inclui preços e total prato + vinho |
| Painel lateral | o pedido interpretado escrito nas chaves dos widgets |

## Resposta no modo sem IA — seções

![Seções Vinho e Restaurante: escolha, uva ou bairro, preço ou ticket médio, justificativa do recomendador, alternativas e a linha Recomendador](../assets/telas/02b-pedido-sem-ia-secoes.png)

Cada seção (🍽️ Prato, 🍷 Vinho, 📍 Restaurante) traz, nesta ordem: **Escolha** com ingredientes ou
uva e preço; a justificativa do recomendador; **Alternativas** com os mesmos campos; a linha
**Recomendador**; e, se houver, um aviso ⚠️.

## Saída dos recomendadores (JSON)

![Área expansível Ver saída dos recomendadores com o JSON do restaurante: city, neighborhood, price, avg_ticket_brl e warning](../assets/telas/03-saida-json.png)

O conteúdo é o mesmo do `--dry-run` da CLI: `food`, `chosen_dish`, `wine` e `restaurant`, cada um
com `technique`, `library`, `items` e `warning`. Formato:
[Referência do código › models](codigo.md#dinner_crewmodels).

## Refinamento

![Mensagem e um vinho mais caro? com a resposta Entendi: preço: alta e um novo resumo com o Champagne brut e total de R$ 462](../assets/telas/04-refinamento.png)

A mensagem é lida por cima do pedido anterior: só `price` muda. Na base `toy`, o vinho passa a ser o
Champagne brut, com aviso de sinal fraco na seção do vinho.

## Modo com IA — progresso

![Painel de status Os agentes estão trabalhando, com o aviso para não interagir e as linhas Food Sommelier concluiu e Wine Sommelier harmonizando o vinho](../assets/telas/05-com-ia-progresso.png)

Atualizado pelo `task_callback` da crew: uma linha ao começar e outra ao concluir cada um dos quatro
agentes. Ao fim, o rótulo vira **Plano pronto!** (ou **A crew falhou**, com o erro no chat).

## Modo com IA — resposta do Anfitrião

![Resposta com IA: o painel Plano pronto! recolhido, a linha Entendi e o Resumo do anfitrião escrito pelo agente](../assets/telas/06-com-ia-resposta.png)

Mesmos itens do modo sem IA; o texto é escrito pelo agente Anfitrião (tarefa `write_summary`).

## Base grande

![Base large selecionada: legenda com 176 pratos, 149 vinhos, 404 restaurantes e 1500 usuários; pedido de peixe cru em Recife para u0100 com um ceviche no resumo](../assets/telas/07-base-grande.png)

Ao trocar de base, valores que não existem na nova base (usuário, cidade, preferências, prato fixado)
são limpos.

## Langfuse — lista de traces

![Tela Tracing do Langfuse filtrada por traces raiz: uma linha dinner-plan por pedido com IA, com horário, input e output](../assets/telas/08-langfuse-traces.png)

Projeto **dinner-crew** → **Tracing**. Cada linha é um pedido feito no modo com IA (trace
`dinner-plan`).

## Langfuse — um trace aberto

![Trace aberto: no topo, duração, custo de US$ 0,002, 8 mil tokens, usuário u1 e as tags streamlit e toy; ao centro, a árvore com DinnerCrew.kickoff, os agentes, as gerações ChatCompletion e as chamadas de ferramenta; à direita, o input com os placeholders e o output com o plano](../assets/telas/09-langfuse-trace.png)

| Área | Conteúdo |
|---|---|
| Cabeçalho | duração, custo total, tokens, sessão, usuário e tags (`streamlit`/`cli`, `toy`/`large`) |
| Árvore (**Tree**) | `dinner-plan` → `DinnerCrew.kickoff` → agentes → gerações e ferramentas; cada nó com duração e, nas gerações, custo |
| Painel direito | **Input** (os placeholders enviados à crew) e **Output** (o plano final) do nó selecionado |

Como ler um trace: [Sobre a observabilidade](../explicacao/observabilidade.md).
