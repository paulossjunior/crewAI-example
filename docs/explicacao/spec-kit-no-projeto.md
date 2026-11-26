# Sobre o Spec Kit neste projeto

## O que é

O [GitHub Spec Kit](https://github.com/github/spec-kit) é um conjunto de templates, scripts e
comandos para *desenvolvimento guiado por especificação* com agentes de código. A ideia é inverter
a ordem habitual de "pedir código ao agente e corrigir depois": primeiro se escreve **o quê** e
**por quê** (spec), depois **como** (plano), depois **em que ordem** (tarefas), e só então o código.

Cada etapa produz um arquivo versionado. O código passa a ter uma trilha de decisões: dá para
abrir `specs/` e entender por que uma escolha foi feita, não só qual foi.

## Como ele está instalado aqui

`specify init --here --integration claude` criou:

- `.specify/` — templates (spec, plano, tarefas, constitution), scripts bash que criam diretórios
  e localizam a feature ativa, e `memory/constitution.md`;
- `.claude/skills/speckit-*` — os comandos, como skills do Claude Code;
- `.specify/feature.json` — aponta para a feature em andamento, para que `/speckit-plan`,
  `/speckit-tasks` e `/speckit-implement` saibam onde trabalhar.

## A constitution

`.specify/memory/constitution.md` é a lei do projeto: princípios que toda feature precisa
respeitar e que o `/speckit-plan` confere explicitamente (a seção *Constitution Check* de cada
`plan.md`). Os cinco princípios atuais:

1. **Um agente, uma biblioteca de recomendação** (LightFM, implicit, Surprise).
2. **Recomendadores determinísticos e sem LLM**, separados do CrewAI.
3. **Dados locais versionados**; o único serviço externo é a OpenAI.
4. **Simplicidade didática**; toda dependência extra é justificada.
5. **Testes offline para cada recomendador; segredos só no `.env`.**

A constitution tem versão semântica. A mudança de versão diz que tipo de mudança aconteceu: uma
versão MAJOR significa que um princípio foi redefinido e que código antigo pode ter deixado de
cumprir as regras.

## A história do projeto, contada pelos artefatos

**Constitution 1.0.0** — o Princípio I exigia *técnicas* distintas por agente: filtragem baseada em
conteúdo, baseada em conhecimento e colaborativa.

**Feature 001 (`specs/001-dinner-pairing-crew/`)** — definiu o produto: a crew de três agentes, o
fluxo prato → vinho → restaurante, a CLI, o `--dry-run`, os fallbacks e o formato do plano. Foi
implementada com recomendadores escritos à mão: TF-IDF para pratos, regras de harmonização em JSON
para vinhos e CF user-based com numpy para restaurantes.

**Constitution 2.0.0** — o pedido seguinte foi "cada agente deve usar Surprise, LightFM ou
implicit". Isso redefine o Princípio I (de técnica para biblioteca), por isso a versão MAJOR. O
relatório de impacto da emenda registrou também a mudança no Princípio II (modelos com semente fixa
em vez de "Python puro") e no IV (as bibliotecas passam a ser dependências sancionadas).

**Feature 002 (`specs/002-library-recommenders/`)** — trocou os três recomendadores sem mexer no
produto. O spec 002 declara explicitamente que substitui só as técnicas de 001; a CLI e o formato
de saída de 001 continuam valendo. O `plan.md` de 002 registra as decisões que não são óbvias
olhando o código: por que cada biblioteca foi para cada agente, por que KNN e não SVD, e por que o
fork `rectools-lightfm`.

Durante a implementação de 002, os testes e o `--dry-run` revelaram problemas que não estavam no
plano — um restaurante sem notas recebendo nota 1, um resultado vazio quando o usuário já tinha
avaliado todos os restaurantes da cidade, ruído na cauda do ALS. Foram corrigidos e cobertos por
testes. Esse é o ciclo esperado: a spec dá a direção, e a implementação devolve aprendizado.

## O que se ganha e o que se paga

**Ganha-se** uma trilha de decisões legível, um ponto de verificação (a constitution) antes de
escrever código, e tarefas pequenas o bastante para um agente executar sem perder o fio.

**Paga-se** em cerimônia. Para um projeto deste tamanho, gerar spec, plano, pesquisa, modelo de
dados, contratos e tarefas para cada mudança é mais documento do que código. O fluxo compensa à
medida que o projeto cresce ou passa a ter mais de uma pessoa (ou agente) trabalhando nele.

## Onde os artefatos estão

| Artefato | Caminho |
|---|---|
| Constitution | `.specify/memory/constitution.md` |
| Feature 001 | `specs/001-dinner-pairing-crew/` (spec, plan, research, data-model, contracts, quickstart, tasks) |
| Feature 002 | `specs/002-library-recommenders/` (spec, plan, contracts, tasks) |
| Feature ativa | `.specify/feature.json` |

Para usar o fluxo numa nova mudança: [Como evoluir o projeto com o Spec Kit](../guias/como-evoluir-com-spec-kit.md).
