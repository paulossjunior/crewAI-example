# Documentação — Dinner Pairing Crew

Um exemplo didático de [CrewAI](https://github.com/crewAIInc/crewAI) em que três agentes
especialistas montam um plano de jantar (prato → vinho → restaurante), cada um com uma biblioteca
de recomendação diferente — **LightFM**, **implicit** e **Surprise** — e um quarto agente, o
**Anfitrião**, resume tudo num texto humano com ingredientes e preços. Há uma base de dados pequena
(`toy`) e uma grande (`large`), uma CLI, uma interface de chat em Streamlit e uma instalação com
Docker Compose que inclui o Langfuse para monitorar cada execução da crew. O projeto foi construído com
[GitHub Spec Kit](https://github.com/github/spec-kit) (desenvolvimento guiado por especificação).

A documentação segue o framework [Diátaxis](https://diataxis.fr): escolha a seção pelo que você
precisa agora.

## Funcionalidades em um olhar

| Funcionalidade | Aprender | Fazer | Consultar | Entender |
|---|---|---|---|---|
| Crew de 3 especialistas + Anfitrião | [tutorial 1](tutorial/primeiros-passos.md) | [nova tool](guias/como-criar-uma-tool-recomendadora.md) | [código](referencia/codigo.md#dinner_crewcrew) | [anatomia de um pedido](explicacao/anatomia-de-um-pedido.md) |
| LightFM · implicit · Surprise | [tutorial 1](tutorial/primeiros-passos.md) | [adicionar dados](guias/como-adicionar-dados.md) | [código](referencia/codigo.md) | [sistemas de recomendação](explicacao/sistemas-de-recomendacao.md) |
| Ingredientes e preços | [tutorial 2](tutorial/jantar-com-ia-monitorado.md) | [adicionar dados](guias/como-adicionar-dados.md) | [dados](referencia/dados.md) | [sistemas de recomendação](explicacao/sistemas-de-recomendacao.md#ingredientes-e-preços) |
| Base `toy` e base `large` | — | [base grande](guias/como-usar-a-base-grande.md) | [dados](referencia/dados.md) | [arquitetura](explicacao/arquitetura.md#duas-bases-de-dados) |
| CLI `dinner-crew` | [tutorial 1](tutorial/primeiros-passos.md) | [configurar o LLM](guias/como-configurar-o-llm.md) | [CLI](referencia/cli.md) | [arquitetura](explicacao/arquitetura.md) |
| Arquitetura do software | — | — | [5 diagramas](referencia/arquitetura.md) | [arquitetura](explicacao/arquitetura.md) |
| Interface de chat (Streamlit) | [tutorial 2](tutorial/jantar-com-ia-monitorado.md) | [usar a interface](guias/como-usar-a-interface.md) | [telas](referencia/telas-da-interface.md) | [interface de chat](explicacao/interface-de-chat.md) |
| Docker Compose + Langfuse | [tutorial 2](tutorial/jantar-com-ia-monitorado.md) | [rodar com Docker](guias/como-rodar-com-docker-e-langfuse.md) | [instalação Docker](referencia/instalacao-docker.md) | [observabilidade](explicacao/observabilidade.md) |
| Spec Kit | — | [evoluir com Spec Kit](guias/como-evoluir-com-spec-kit.md) | — | [Spec Kit no projeto](explicacao/spec-kit-no-projeto.md) |

## 🎓 Tutorial — aprender fazendo

1. [Primeiros passos com o Dinner Pairing Crew](tutorial/primeiros-passos.md): instale, rode os
   recomendadores e veja a recomendação mudar ao alterar os dados (≈15 min, sem chave de API).
2. [Seu primeiro jantar com IA, monitorado no Langfuse](tutorial/jantar-com-ia-monitorado.md): suba
   tudo com Docker, converse com a crew no chat e leia o trace de cada agente (≈20 min).

## 🛠️ Guias práticos — resolver uma tarefa

- [Como usar a interface gráfica (Streamlit)](guias/como-usar-a-interface.md)
- [Como usar (e regenerar) a base de dados grande](guias/como-usar-a-base-grande.md)
- [Como rodar com Docker (aplicação + Langfuse)](guias/como-rodar-com-docker-e-langfuse.md)
- [Como adicionar pratos, vinhos, restaurantes e usuários](guias/como-adicionar-dados.md)
- [Como criar uma nova tool recomendadora para um agente](guias/como-criar-uma-tool-recomendadora.md)
- [Como configurar o LLM](guias/como-configurar-o-llm.md)
- [Como evoluir o projeto com o Spec Kit](guias/como-evoluir-com-spec-kit.md)

## 📖 Referência — consultar detalhes

- [Referência da CLI `dinner-crew`](referencia/cli.md)
- [Referência do código (módulos, classes, tools)](referencia/codigo.md)
- [Referência dos arquivos de dados](referencia/dados.md)
- [Referência da instalação Docker (serviços, portas, volumes, variáveis)](referencia/instalacao-docker.md)
- [Referência da arquitetura do software (5 diagramas)](referencia/arquitetura.md)
- [Referência das telas da interface](referencia/telas-da-interface.md)

## 💡 Explicação — entender o porquê

- [Arquitetura do projeto](explicacao/arquitetura.md)
- [Anatomia de um pedido: do texto ao plano de jantar](explicacao/anatomia-de-um-pedido.md)
- [Sobre a interface de chat](explicacao/interface-de-chat.md)
- [Sobre a observabilidade com Langfuse](explicacao/observabilidade.md)
- [Sobre os sistemas de recomendação usados](explicacao/sistemas-de-recomendacao.md)
- [Sobre o Spec Kit neste projeto](explicacao/spec-kit-no-projeto.md)
