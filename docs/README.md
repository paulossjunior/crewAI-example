# Documentação — Dinner Pairing Crew

Um exemplo didático de [CrewAI](https://github.com/crewAIInc/crewAI) em que três agentes
especialistas montam um plano de jantar (prato → vinho → restaurante), cada um com uma biblioteca
de recomendação diferente — **LightFM**, **implicit** e **Surprise** — e um quarto agente, o
**Anfitrião**, resume tudo num texto humano com ingredientes e preços. Há uma base de dados pequena
(`toy`) e uma grande (`large`), uma CLI e uma interface de chat em Streamlit. O projeto foi construído com
[GitHub Spec Kit](https://github.com/github/spec-kit) (desenvolvimento guiado por especificação).

A documentação segue o framework [Diátaxis](https://diataxis.fr): escolha a seção pelo que você
precisa agora.

## 🎓 Tutorial — aprender fazendo

- [Primeiros passos com o Dinner Pairing Crew](tutorial/primeiros-passos.md): instale, rode os
  recomendadores e veja a recomendação mudar ao alterar os dados (≈15 min).

## 🛠️ Guias práticos — resolver uma tarefa

- [Como usar a interface gráfica (Streamlit)](guias/como-usar-a-interface.md)
- [Como usar (e regenerar) a base de dados grande](guias/como-usar-a-base-grande.md)
- [Como adicionar pratos, vinhos, restaurantes e usuários](guias/como-adicionar-dados.md)
- [Como criar uma nova tool recomendadora para um agente](guias/como-criar-uma-tool-recomendadora.md)
- [Como configurar o LLM](guias/como-configurar-o-llm.md)
- [Como evoluir o projeto com o Spec Kit](guias/como-evoluir-com-spec-kit.md)

## 📖 Referência — consultar detalhes

- [Referência da CLI `dinner-crew`](referencia/cli.md)
- [Referência do código (módulos, classes, tools)](referencia/codigo.md)
- [Referência dos arquivos de dados](referencia/dados.md)

## 💡 Explicação — entender o porquê

- [Arquitetura do projeto](explicacao/arquitetura.md)
- [Sobre os sistemas de recomendação usados](explicacao/sistemas-de-recomendacao.md)
- [Sobre o Spec Kit neste projeto](explicacao/spec-kit-no-projeto.md)
