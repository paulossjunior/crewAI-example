# Feature Specification: Dinner Pairing Crew

**Feature Branch**: `001-dinner-pairing-crew`

**Created**: 2026-11-26

**Status**: Implemented — recommendation techniques superseded by [002](../002-library-recommenders/spec.md)

**Input**: User description: "Dinner Pairing Crew: um usuário informa suas preferências para um jantar (ingredientes/sabores de que gosta, restrições alimentares, faixa de preço, cidade/bairro e seu id de usuário com histórico de avaliações). Uma crew de 3 agentes monta um plano de jantar: (1) Food Sommelier recomenda top-3 pratos usando filtragem baseada em conteúdo; (2) Wine Sommelier recomenda vinhos para o prato escolhido usando recomendação baseada em conhecimento (regras de harmonização: proteína, molho, intensidade, faixa de preço); (3) Concierge recomenda restaurantes que servem a culinária do prato usando filtragem colaborativa. Saída final: plano de jantar em markdown com prato, vinho e restaurante, cada um com justificativa explicando qual técnica de recomendação gerou a sugestão. Dados toy locais. CLI única."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recomendar pratos pelas preferências (Priority: P1)

O usuário descreve sabores e ingredientes de que gosta (ex.: "cogumelos, cremoso, ervas") e suas
restrições (ex.: vegetariano). O sistema devolve os 3 pratos do catálogo mais parecidos com essas
preferências, cada um com pontuação de similaridade e explicação de que a sugestão veio de
**filtragem baseada em conteúdo** (atributos do prato × preferências).

**Why this priority**: o prato é a âncora do jantar; vinho e restaurante dependem dele. Sozinho
já entrega valor (sugestão de o que comer).

**Independent Test**: informar preferências e restrições e verificar que os 3 pratos retornados
respeitam as restrições e estão ordenados por similaridade decrescente.

**Acceptance Scenarios**:

1. **Given** preferências "cogumelos, cremoso" e nenhuma restrição, **When** o usuário pede
   recomendação, **Then** recebe 3 pratos distintos ordenados por similaridade, com risoto de
   cogumelos (ou prato equivalente com esses atributos) entre os primeiros.
2. **Given** restrição "vegetariano", **When** o usuário pede recomendação, **Then** nenhum prato
   retornado contém carne ou peixe.
3. **Given** as mesmas entradas executadas duas vezes, **When** o usuário compara os resultados,
   **Then** a lista de pratos e a ordem são idênticas.

---

### User Story 2 - Harmonizar vinho com o prato escolhido (Priority: P2)

Com o prato principal definido (o 1º da lista da US1, ou um prato informado pelo usuário), o
sistema recomenda até 3 vinhos dentro da faixa de preço do usuário, aplicando **regras de
harmonização** explícitas (proteína, molho, intensidade). Cada vinho vem com as regras que o
justificam.

**Why this priority**: agrega a experiência de sommelier e demonstra a segunda técnica
(baseada em conhecimento).

**Independent Test**: escolher um prato conhecido e verificar que os vinhos retornados satisfazem
as regras correspondentes e a faixa de preço.

**Acceptance Scenarios**:

1. **Given** prato de carne vermelha com molho intenso e faixa de preço "média", **When** o usuário
   pede vinho, **Then** recebe tintos encorpados dentro da faixa, cada um citando a regra aplicada.
2. **Given** prato de peixe leve, **When** o usuário pede vinho, **Then** recebe brancos leves ou
   espumantes, nunca tintos encorpados.
3. **Given** faixa de preço sem nenhum vinho compatível, **When** o usuário pede vinho, **Then**
   recebe os vinhos compatíveis mais próximos da faixa, com aviso explícito de que a faixa foi
   relaxada.

---

### User Story 3 - Indicar restaurante com base em usuários parecidos (Priority: P3)

O sistema recomenda até 3 restaurantes na cidade/bairro do usuário que servem a culinária do
prato escolhido, ordenados pela nota prevista via **filtragem colaborativa**: notas dadas por
usuários com histórico de avaliações parecido com o do usuário.

**Why this priority**: completa o plano de jantar e demonstra a terceira técnica; depende de
histórico de avaliações.

**Independent Test**: com um usuário de histórico conhecido, verificar que os restaurantes vêm
ordenados pela nota prevista, filtrados por culinária e localização, e que a justificativa cita
usuários semelhantes.

**Acceptance Scenarios**:

1. **Given** usuário com histórico de notas e culinária "italiana" em "São Paulo", **When** pede
   restaurante, **Then** recebe restaurantes italianos de São Paulo que ele ainda não avaliou,
   ordenados por nota prevista.
2. **Given** usuário sem histórico (novo), **When** pede restaurante, **Then** recebe os
   restaurantes mais bem avaliados no geral (fallback por popularidade), com aviso de que não
   houve personalização.

---

### User Story 4 - Plano de jantar completo pela CLI (Priority: P1)

O usuário executa um único comando informando suas preferências e recebe um plano de jantar em
markdown: prato, vinho e restaurante, cada seção com justificativa nomeando a técnica de
recomendação usada. Três agentes especializados colaboram em sequência
(prato → vinho → restaurante).

**Why this priority**: é a experiência final do toy example; demonstra a orquestração dos agentes.

**Independent Test**: executar o comando com preferências de exemplo e verificar que a saída
contém as três seções, cada uma com item existente nos dados e nome da técnica.

**Acceptance Scenarios**:

1. **Given** preferências válidas e credencial do LLM configurada, **When** o usuário executa o
   comando, **Then** recebe markdown com seções Prato, Vinho e Restaurante, cada uma citando a
   técnica ("baseada em conteúdo", "baseada em conhecimento", "filtragem colaborativa").
2. **Given** credencial do LLM ausente, **When** o usuário executa o comando, **Then** recebe
   mensagem clara indicando a variável de ambiente que falta, sem stack trace.
3. **Given** qualquer execução, **When** o plano é exibido, **Then** todos os pratos, vinhos e
   restaurantes citados existem nos dados locais (nenhum item inventado).

---

### Edge Cases

- Nenhum prato atende às restrições → mensagem informando que não há pratos compatíveis; vinho e
  restaurante não são recomendados.
- Preferências vazias → pratos retornados ordenados pela popularidade/ordem padrão do catálogo,
  com aviso.
- Termos de preferência desconhecidos (fora do vocabulário do catálogo) → ignorados; se todos
  forem desconhecidos, mesmo comportamento de preferências vazias.
- Id de usuário inexistente → tratado como usuário novo (fallback por popularidade).
- Nenhum restaurante da culinária na cidade → informa ausência e sugere restaurantes da mesma
  culinária em outra localidade, ou nenhum se não houver.
- Empate de pontuação → ordem determinística (critério de desempate fixo, ex.: nome).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema MUST aceitar como entrada: preferências (lista de termos), restrições
  alimentares (opcional), faixa de preço (baixa/média/alta), cidade e id de usuário (opcional).
- **FR-002**: Sistema MUST recomendar até 3 pratos por similaridade entre preferências e atributos
  dos pratos (filtragem baseada em conteúdo), excluindo pratos que violem restrições.
- **FR-003**: Sistema MUST recomendar até 3 vinhos para um prato aplicando regras de harmonização
  explícitas sobre proteína, molho e intensidade, filtrando pela faixa de preço.
- **FR-004**: Sistema MUST relaxar a faixa de preço e avisar o usuário quando nenhum vinho
  compatível estiver na faixa.
- **FR-005**: Sistema MUST recomendar até 3 restaurantes filtrados por culinária e cidade,
  ordenados por nota prevista via filtragem colaborativa entre usuários, excluindo restaurantes
  já avaliados pelo usuário.
- **FR-006**: Sistema MUST usar fallback por popularidade (nota média) quando o usuário não tem
  histórico ou não existe, sinalizando isso na saída.
- **FR-007**: Cada recomendação MUST incluir justificativa que nomeia a técnica usada e os
  fatores determinantes (atributos semelhantes, regras aplicadas, usuários semelhantes).
- **FR-008**: Sistema MUST produzir um plano de jantar final em markdown com seções Prato, Vinho e
  Restaurante.
- **FR-009**: Sistema MUST ser executável por um único comando de linha de comando.
- **FR-010**: Recomendações MUST ser determinísticas para a mesma entrada e mesmos dados.
- **FR-011**: Plano final MUST citar apenas itens presentes nos dados locais.
- **FR-012**: Sistema MUST informar de forma clara a ausência da credencial do LLM.

### Key Entities

- **Prato**: nome, culinária, proteína (carne vermelha, ave, peixe, vegetal...), molho
  (cremoso, tomate, leve...), intensidade (leve/média/intensa), tags de sabor/ingredientes,
  marcadores de restrição (vegetariano, sem glúten...).
- **Vinho**: nome, tipo (tinto, branco, rosé, espumante), corpo (leve/médio/encorpado), faixa de
  preço, notas descritivas.
- **Regra de harmonização**: condição sobre atributos do prato (proteína, molho, intensidade) →
  tipo/corpo de vinho recomendado, com texto explicativo.
- **Restaurante**: nome, culinária, cidade/bairro, faixa de preço.
- **Usuário**: id, nome.
- **Avaliação**: usuário, restaurante, nota (1–5).
- **Preferências do jantar**: termos de preferência, restrições, faixa de preço, cidade, usuário.
- **Plano de jantar**: prato, vinho e restaurante escolhidos, cada um com justificativa e técnica.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuário obtém um plano de jantar completo com um único comando em menos de 2
  minutos.
- **SC-002**: 100% das recomendações exibidas respeitam as restrições alimentares informadas.
- **SC-003**: 100% dos itens citados no plano existem nos dados locais.
- **SC-004**: 100% das seções do plano nomeiam a técnica de recomendação usada.
- **SC-005**: As três técnicas de recomendação podem ser verificadas isoladamente, sem acesso à
  internet nem credenciais, em menos de 10 segundos.
- **SC-006**: Repetir a mesma entrada produz exatamente as mesmas recomendações de prato, vinho e
  restaurante.

## Assumptions

- Projeto é um exemplo didático (toy): catálogo pequeno (~15–20 pratos, ~15 vinhos, ~12
  restaurantes, ~8 usuários com avaliações), em português.
- Prato usado para vinho e restaurante é o 1º recomendado; o usuário pode opcionalmente fixar um
  prato pelo nome.
- Faixas de preço são categóricas (baixa/média/alta), sem moeda.
- Localização é correspondência exata de cidade (bairro opcional, não obrigatório para filtrar).
- Usuário é único e local; não há autenticação nem persistência de novas avaliações.
- Requer credencial de um provedor de LLM (OpenAI) apenas para a orquestração dos agentes e
  redação do plano; as recomendações em si não dependem do LLM.
