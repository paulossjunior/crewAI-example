# Como evoluir o projeto com o Spec Kit

Os comandos abaixo são skills do Claude Code instaladas em `.claude/skills/`. Rode-os numa sessão
do Claude Code aberta na raiz do repositório. O contexto de por que o projeto usa esse fluxo está em
[Sobre o Spec Kit neste projeto](../explicacao/spec-kit-no-projeto.md).

## Adicionar uma nova funcionalidade

1. Crie uma branch para a feature (o Spec Kit não cria sozinho neste projeto):

   ```bash
   git checkout -b 003-sobremesas
   ```

2. Escreva a especificação descrevendo **o quê** e **por quê**, sem tecnologia:

   ```text
   /speckit-specify Adicionar um agente que recomenda sobremesa para o prato escolhido...
   ```

   Gera `specs/003-<nome>/spec.md` e aponta `.specify/feature.json` para ela.

3. (Opcional) Tire ambiguidades: `/speckit-clarify`.

4. Planeje a implementação, agora sim com tecnologia:

   ```text
   /speckit-plan Usar Surprise KNN item-based sobre data/dessert_ratings.csv...
   ```

   Gera `plan.md`, `research.md`, `data-model.md`, `contracts/` e `quickstart.md`, e checa a
   constitution.

5. Gere as tarefas: `/speckit-tasks` → `tasks.md`.

6. (Opcional) Verifique consistência entre spec, plano e tarefas: `/speckit-analyze`.

7. Implemente: `/speckit-implement`. As tarefas concluídas são marcadas `[X]` em `tasks.md`.

8. Rode `uv run pytest` e commite.

## Mudar uma regra do projeto

Se a mudança contraria um princípio (ex.: trocar uma biblioteca, adicionar um serviço externo):

```text
/speckit-constitution Trocar o Princípio III para permitir a API da Anthropic além da OpenAI.
```

A constitution recebe nova versão semântica (MAJOR se um princípio é redefinido ou removido,
MINOR se é acrescentado, PATCH se é só redação) e um relatório de impacto no topo do arquivo.
Remova esse relatório antes de commitar.

## Completar trabalho que ficou para trás

Se o código divergiu do que `tasks.md` descreve:

```text
/speckit-converge
```

Compara código com spec/plano/tarefas e acrescenta as tarefas que faltam.

## Atualizar o Spec Kit

```bash
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git
specify init --here --force --integration claude
```

Confira o `git diff` antes de commitar: o `init` pode sobrescrever templates e skills.
