# Primeiros passos com o Dinner Pairing Crew

Neste tutorial você vai instalar o projeto, rodar os três recomendadores e ver, na prática, como
uma recomendação muda quando o histórico de um usuário muda. No final, (opcionalmente) vai rodar
a crew completa com o LLM.

**Tempo:** ~15 minutos.
**Pré-requisitos:** macOS ou Linux, [`uv`](https://docs.astral.sh/uv/) instalado e o repositório
clonado. Não é preciso chave de API até o passo 6.

## 1. Instale as dependências

Na raiz do repositório, rode:

```bash
uv sync
```

O `uv` lê o arquivo `.python-version`, baixa o Python 3.12 se necessário e instala CrewAI,
LightFM, implicit e Surprise num ambiente virtual `.venv/`.

## 2. Confirme que tudo funciona

```bash
uv run pytest
```

Você deve ver algo como:

```text
........................................................                 [100%]
56 passed in 12.74s
```

Os testes treinam os três modelos com as duas bases (`data/` e `data/large/`) e não acessam a
internet.

## 3. Peça um jantar como usuário novo

Vamos pedir um jantar para quem gosta de massa e tomate. A opção `--dry-run` roda só os
recomendadores — sem agentes, sem LLM — e mostra o JSON que cada agente receberia:

```bash
uv run dinner-crew --prefs "massa,tomate" --dry-run
```

A saída tem quatro blocos. Observe os nomes e a linha `library` de cada um:

- `"food"` — `"library": "lightfm"`. O primeiro prato é **Spaghetti al pomodoro**.
- `"chosen_dish"` — o prato que segue adiante: `"Spaghetti al pomodoro"`.
- `"wine"` — `"library": "implicit"`. O primeiro vinho é **Chianti Classico**.
- `"restaurant"` — `"library": "surprise"`, com o aviso:

  ```text
  "warning": "Fallback por popularidade (usuário sem histórico)."
  ```

O restaurante veio por popularidade porque não dissemos quem é o usuário. Vamos resolver isso.

## 4. Peça o mesmo jantar como um usuário conhecido

O arquivo `data/ratings.csv` tem notas de 8 usuários (`u1` a `u8`). Repita o pedido como `u1`:

```bash
uv run dinner-crew --prefs "massa,tomate" --user u1 --dry-run
```

Agora o bloco `"restaurant"` não tem aviso, e cada item explica de onde veio a nota:

```text
Osteria del Porto  4.48  Nota prevista 4.48 pelo KNN a partir de usuários parecidos: u2 (pearson 0.94), u3 (pearson 0.79).
Cantina da Vila    2.39  Nota prevista 2.39 pelo KNN a partir de usuários parecidos: u2 (pearson 0.94), u3 (pearson 0.79).
```

O Surprise encontrou `u2` e `u3`, que avaliam restaurantes de forma parecida com `u1`, e usou as
notas deles para prever as de `u1`.

## 5. Crie um usuário com gosto diferente

Vamos criar `u9`, alguém que adora japonês e não gostou da Trattoria. Acrescente três linhas ao
final de `data/ratings.csv`:

```bash
printf 'u9,Sakura Liberdade,5\nu9,Trattoria Nonna Lina,2\nu9,Izakaya Kaze,5\n' >> data/ratings.csv
```

Peça o jantar como `u9`:

```bash
uv run dinner-crew --prefs "massa,tomate" --user u9 --dry-run
```

O ranking de restaurantes inverteu:

```text
Cantina da Vila    4.68  Nota prevista 4.68 pelo KNN a partir de usuários parecidos: u4 (pearson 1.00), u5 (pearson 0.94).
Osteria del Porto  2.17  Nota prevista 2.17 pelo KNN a partir de usuários parecidos: u4 (pearson 1.00).
```

Três notas bastaram para o Surprise achar outros vizinhos (`u4`, `u5`) e mudar a recomendação.
Isso é filtragem colaborativa em ação.

Desfaça a alteração para deixar os dados como estavam:

```bash
git checkout data/ratings.csv
```

## 6. (Opcional) Rode a crew completa

Este passo usa a API da OpenAI e tem custo (pequeno, com o modelo padrão `gpt-4o-mini`).

Crie seu `.env` a partir do exemplo e coloque sua chave:

```bash
cp .env.example .env
# edite .env e preencha OPENAI_API_KEY=...
```

Rode sem `--dry-run`:

```bash
uv run dinner-crew --prefs "massa,tomate" --user u1
```

Depois de uns 45 segundos, você verá um plano em markdown que começa com `🗣️ Resumo do anfitrião`
— um parágrafo escrito pelo quarto agente, com os preços e o custo de prato + vinho — seguido das
seções `🍽️ Prato`, `🍷 Vinho` e `📍 Restaurante`, com ingredientes, uva, preços e uma linha
`**Recomendador:**` dizendo qual biblioteca gerou cada sugestão.

## O que você fez

Você instalou o projeto, rodou os três recomendadores, viu o fallback para usuário novo, viu a
personalização para um usuário conhecido e mudou uma recomendação alterando os dados.

## Próximos passos

- Entenda por que cada biblioteca foi usada onde está:
  [Sobre os sistemas de recomendação](../explicacao/sistemas-de-recomendacao.md).
- Veja como as peças se encaixam: [Arquitetura do projeto](../explicacao/arquitetura.md).
- Adicione seus próprios pratos e restaurantes:
  [Como adicionar dados](../guias/como-adicionar-dados.md).
- Converse com a crew no navegador: [Como usar a interface](../guias/como-usar-a-interface.md).
- Teste com volume: [Como usar a base grande](../guias/como-usar-a-base-grande.md).
