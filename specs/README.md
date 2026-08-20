# NanoJuris Spec-Driven Development

Este diretório é a fonte versionada de intenção, contratos e evidências do
NanoJuris. O código implementa as especificações; testes e validações provam
que a implementação continua alinhada.

## Estrutura

```text
specs/
├── constitution.md          # regras invioláveis do projeto
├── product/                 # comportamento e limites do produto
├── architecture/            # arquitetura e operação do sistema
├── contracts/                # contratos executáveis ou normativos
├── templates/                # modelos para novas mudanças
└── changes/                 # mudanças propostas ou concluídas
```

## Fluxo obrigatório

```text
clarify → specify → design → plan → implement → verify → review → release
```

1. Esclareça objetivo, fora de escopo, riscos e dependências.
2. Escreva ou atualize `spec.md`.
3. Registre a arquitetura em `design.md`.
4. Divida o trabalho em `tasks.md`.
5. Implemente em tarefas pequenas e verificáveis.
6. Registre evidências em `verification.md`.
7. Revise contra os critérios de aceite, não apenas contra o diff.

## Regras de precedência

Em caso de conflito, a precedência é:

1. `AGENTS.md` e `specs/constitution.md`;
2. especificação da mudança;
3. contratos de API, provider e dados;
4. design e ADRs;
5. implementação;
6. documentação derivada.

Uma especificação não autoriza acessar fontes externas, burlar controles ou
publicar dados. Essas ações continuam sujeitas às regras de uso responsável.

## Nomenclatura

Use identificadores estáveis e descritivos:

```text
NNNN-nome-curto
```

Exemplo: `0001-oci-initial-deployment`.

Cada mudança deve declarar status: `proposed`, `in_progress`, `verified`,
`accepted` ou `superseded`.
