# Como usar a interface gráfica (Streamlit)

## Abrir

```bash
uv run streamlit run src/dinner_crew/app.py
```

O navegador abre em `http://localhost:8501`. Para outra porta: `--server.port 8600`.

## Pedir um jantar

Escreva na caixa de chat, em português, do jeito que falaria:

```text
quero um prato vegetariano com cogumelos, sou u1
```

A resposta começa com o que foi entendido (`Entendi: preferências: cogumelos; restrição:
vegetariano; usuário: u1.`), segue com o **Resumo do anfitrião** — um parágrafo com prato, vinho,
restaurante, preços e custo de prato + vinho — e traz as seções 🍽️ Prato, 🍷 Vinho e
📍 Restaurante, com ingredientes, uva, preço da garrafa e ticket médio de cada item. Abra
**Ver saída dos recomendadores (JSON)** para ver os dados crus de LightFM, implicit e Surprise.

O que o chat reconhece:

| Você escreve | Vira |
|---|---|
| termos de sabor/ingrediente do vocabulário (cogumelos, carne, peixe, picante…) | preferências |
| vegetariano(a), vegano(a), sem glúten, sem lactose | restrições |
| barato, econômico, em conta / caro, sofisticado, especial, premium / médio | faixa de preço |
| São Paulo, SP, Rio de Janeiro, Rio, RJ | cidade |
| `u1` … `u8` | usuário |
| nome exato de um prato ("bife ancho com chimichurri") | prato fixado |

A lista completa de termos de preferência está no campo **Preferências** do painel lateral.

## Refinar o pedido

Mensagens seguintes mudam só o que mencionam:

```text
e um vinho mais caro?        → muda só o preço
agora quero peixe            → troca as preferências (e solta o prato fixado)
estou no Rio                 → muda só a cidade
```

Para recomeçar do zero, clique em **Nova conversa** no painel.

## Usar o painel lateral

O painel mostra o pedido atual e permite editá-lo: usuário, cidade, preço, restrições e
preferências. Depois de editar, clique em **Recomendar com estes filtros**.

## Trocar de base de dados

No painel, **Base de dados** alterna entre **toy (pequena)** e **large (grande)**; a legenda logo
abaixo mostra quantos pratos, vinhos, restaurantes e usuários a base tem. Na base grande, os
usuários vão de `u0001` a `u1500` e há 8 cidades. Detalhes em
[Como usar a base grande](como-usar-a-base-grande.md).

## Escolher o modo

| Modo | O que acontece | Precisa |
|---|---|---|
| **Sem IA (offline)** (padrão) | recomendadores + resumo e plano por template, em ~1 s | nada |
| **Com IA (CrewAI + OpenAI)** | os três especialistas chamam as tools e o Anfitrião redige o plano (~45 s) | `OPENAI_API_KEY` no `.env` ([Como configurar o LLM](como-configurar-o-llm.md)) |

Sem chave, o modo com IA avisa e mostra o plano sem IA.

No modo com IA, um painel mostra cada agente concluindo (prato → vinho → restaurante →
resumo). **Não envie mensagens nem mude filtros enquanto ele roda:** qualquer interação faz o
Streamlit reexecutar a página e interrompe a crew, que recomeça do zero. Se uma chamada à OpenAI
ficar presa, ela falha após 90 s e o erro aparece no chat.
