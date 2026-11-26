# Feature Specification: Streamlit Chat UI

**Feature Branch**: `docs/code-docstrings` (shared with the code-docstrings change)

**Created**: 2026-11-26

**Status**: Implemented

**Input**: User description: "a CrewAI permite ter uma interface de perguntas e resposta? Quero que o usuário solicite um prato ... use o streamlit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pedir um jantar em linguagem natural (Priority: P1)

O usuário abre uma página web local, escreve o que quer ("quero um prato vegetariano com
cogumelos, sou u1") e recebe o plano de jantar (prato, vinho, restaurante) com o recomendador de
cada seção. A página mostra o que foi entendido do pedido.

**Independent Test**: enviar a frase acima e verificar plano com as três seções, restrição
"vegetariano" e usuário "u1" refletidos nos filtros.

**Acceptance Scenarios**:

1. **Given** a página aberta, **When** o usuário envia um pedido em texto livre, **Then** recebe
   "Entendi: ..." e o plano com 🍽️ Prato, 🍷 Vinho e 📍 Restaurante.
2. **Given** um pedido anterior, **When** o usuário envia "e um vinho mais caro?", **Then** só a
   faixa de preço muda e o plano é refeito mantendo as demais preferências.

### User Story 2 - Ajustar filtros pelo painel (Priority: P2)

O painel lateral mostra e permite editar usuário, cidade, preço, restrições e preferências;
"Recomendar com estes filtros" refaz o plano sem digitar.

### User Story 3 - Escolher entre sem IA e com IA (Priority: P2)

Modo **Sem IA** (padrão) funciona offline, com plano por template. Modo **Com IA** usa a crew
CrewAI + OpenAI para redigir o plano; sem chave, avisa e mostra o plano sem IA.

### Edge Cases

- Mensagem sem nada reconhecível → reutiliza o pedido anterior e diz isso.
- Palavras de contexto ("vinho", "prato") não viram preferência.
- "carne" não é confundido com "caro".
- Nenhum prato atende às restrições → mensagem amigável.

## Requirements *(mandatory)*

- **FR-001**: UI MUST accept free-text requests and extract preferences, restrictions, price,
  city, user id and pinned dish without an LLM.
- **FR-002**: Requests MUST persist across messages; follow-ups change only what they mention.
- **FR-003**: Sidebar MUST reflect the current request and allow editing it.
- **FR-004**: Offline mode MUST render the plan from the recommenders only.
- **FR-005**: AI mode MUST use the existing crew; missing key → warning + offline plan.
- **FR-006**: Each reply MUST show the raw recommender output on demand.
- **FR-007**: CLI and UI MUST share the same pipeline code.

## Success Criteria *(mandatory)*

- **SC-001**: Offline reply in under 3 seconds after models are loaded.
- **SC-002**: UI flow is covered by an automated headless test.
- **SC-003**: Follow-up messages keep 100% of unchanged request fields.

## Assumptions

- Local single-user app (`streamlit run`), no authentication or deployment.
- Rule-based intake is enough for the toy vocabulary; LLM-based intake is out of scope.
