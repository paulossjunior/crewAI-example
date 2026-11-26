# Sobre a observabilidade com Langfuse

## O problema

Uma crew de agentes é um programa em que parte das decisões é tomada por um modelo de linguagem.
Quando o plano sai errado, a saída final raramente diz por quê. Pode ter sido:

- a ferramenta, que devolveu outra coisa (um prato inesperado, uma lista vazia, um aviso);
- o agente, que passou argumentos errados para a ferramenta (o nome do prato com um erro de
  digitação, a cidade errada);
- o agente seguinte, que leu mal o `context` da tarefa anterior;
- o modelo, que ignorou uma instrução do prompt (como aconteceu com a linha **Recomendador**, que
  saiu repetida em todas as seções até o prompt ficar mais explícito).

Sem um registro de cada passo, depurar vira tentativa e erro. Observabilidade é ter esse registro.

## Traces, spans e gerações

O Langfuse organiza o registro em três níveis:

- **Trace**: uma execução completa — aqui, um pedido feito no modo com IA, com o nome
  `dinner-plan`.
- **Span** (ou observação): um passo dentro do trace, com início, fim, entrada e saída. Os spans
  formam uma árvore: a crew contém agentes, que contêm chamadas de ferramenta.
- **Geração**: um span especial para cada chamada ao modelo, com o prompt, a resposta, o número de
  tokens e o custo estimado.

Num trace típico deste projeto há cerca de 26 observações: a raiz, a execução da crew, 4 agentes,
3 chamadas de ferramenta e uma série de gerações. Parte das gerações são as respostas do modelo
(`ChatCompletion`); outras são contagens de tokens de entrada que o CrewAI pede à API da OpenAI
antes de algumas chamadas (`InputTokenCountResponse`).

## Como os dados chegam lá

O código da aplicação quase não sabe que o Langfuse existe. A instrumentação é feita por duas
bibliotecas do projeto [OpenInference](https://github.com/Arize-ai/openinference), que se
penduram nas bibliotecas usadas e emitem spans no padrão OpenTelemetry:

- `openinference-instrumentation-crewai` registra a crew, os agentes, as tarefas e as ferramentas;
- `openinference-instrumentation-openai` registra cada chamada ao SDK da OpenAI.

A SDK do Langfuse recebe esses spans e os envia ao servidor. O único código explícito está em
`observability.py`: ele cria o span raiz `dinner-plan` com o pedido e o plano final, e anexa
usuário, sessão e tags a todo o trace.

A alternativa seria espalhar chamadas de tracing por todos os módulos. Com instrumentação, o
tracing fica num lugar só e pode ser desligado sem mexer no resto do código.

## Usuário, sessão e tags

Três atributos tornam os traces pesquisáveis:

- **usuário**: o `user_id` do pedido (`u1`, `u0042`…), para ver tudo o que um usuário pediu;
- **sessão**: um id por conversa do chat, para ver os pedidos de uma conversa em sequência —
  inclusive os refinamentos ("e um vinho mais caro?");
- **tags**: de onde veio o pedido (`streamlit` ou `cli`) e qual base de dados foi usada (`toy` ou
  `large`).

## O que não aparece

Os três recomendadores não fazem chamadas a modelos de linguagem, então não geram gerações. Eles
aparecem como **chamadas de ferramenta**, com os argumentos recebidos e o JSON devolvido — que é
exatamente o que interessa para saber se o erro foi da recomendação ou da redação. O modo sem IA
não gera traces.

## Por que self-hosted

Os traces contêm prompts e respostas completos. Rodar o Langfuse localmente via Docker Compose mantém
esses dados na máquina e evita um novo serviço externo — a constitution do projeto só permite a
OpenAI como serviço externo, e a emenda 3.1.0 abriu exceção apenas para observabilidade local e
opcional. O custo é operar seis containers (web, worker, Postgres, ClickHouse, Redis, MinIO), que é
como o Langfuse é distribuído.

## Por que opcional e tolerante a falhas

Observabilidade não pode virar um ponto de falha. Por isso:

- sem as chaves no `.env`, nada é instrumentado nem enviado;
- se o Langfuse estiver fora do ar, a aplicação avisa uma vez e segue sem tracing;
- uma falha não é definitiva: a interface tenta reconectar a cada 30 segundos, porque no
  `docker compose up` a aplicação pode ficar pronta antes do Langfuse;
- a CLI chama `flush()` no fim, porque um processo curto poderia terminar antes de os spans serem
  enviados.

Os testes cobrem esses três comportamentos sem precisar de um Langfuse de verdade.

## Uma nota sobre o Langfuse v4

A versão 4 do Langfuse grava os dados em modo *events only* e desativou parte da API antiga
(`/api/public/traces`, `/api/public/observations`). Para consultar traces por script, use a API v2
de observações — veja [Como rodar com Docker e Langfuse](../guias/como-rodar-com-docker-e-langfuse.md#consultar-traces-pela-api).
