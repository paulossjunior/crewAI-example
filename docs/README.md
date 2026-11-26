# Documentação — Dinner Pairing Crew

Um exemplo didático de [CrewAI](https://github.com/crewAIInc/crewAI) em que três agentes montam um
plano de jantar (prato → vinho → restaurante). Cada agente usa uma biblioteca de recomendação
diferente: **LightFM**, **implicit** e **Surprise**. O projeto foi construído com
[GitHub Spec Kit](https://github.com/github/spec-kit) (desenvolvimento guiado por especificação).

A documentação segue o framework [Diátaxis](https://diataxis.fr): escolha a seção pelo que você
precisa agora.

## 🎓 Tutorial — aprender fazendo

- [Primeiros passos com o Dinner Pairing Crew](tutorial/primeiros-passos.md): instale, rode os
  recomendadores e veja a recomendação mudar ao alterar os dados (≈15 min).

## 🛠️ Guias práticos — resolver uma tarefa

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
