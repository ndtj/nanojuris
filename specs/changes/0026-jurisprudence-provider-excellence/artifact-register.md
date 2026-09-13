# Registro de artefatos do programa

## Normativos

| Artefato | Função | Dono | Gate |
| --- | --- | --- | --- |
| spec-of-specs.md | decomposição e dependências | Architecture | program |
| spec.md | intenção e requisitos globais | Product/Domain | specification |
| design.md | arquitetura-alvo | Architecture | design |
| threat-model.md | riscos e controles | Security | security |
| traceability.md | requisito até evidência | QA | verification |

## Pesquisa e decisão

| Artefato | Função |
| --- | --- |
| research.md | linha de base e evidência externa |
| clarify.md | perguntas, hipóteses e aprovadores |
| provider-intake-matrix.md | triagem Juscraper versus NanoJuris |
| architecture-review.md | achados, severidade e correções do plano |
| national-coverage-model.md | unidade de contagem e dimensões nacionais |
| adr-001-adaptation-over-dependency.md | estratégia de adoção externa |
| adr-002-provider-contract-boundary.md | limite do contrato comum |
| adr-003-offline-first-evidence.md | política de evidência |

## Execução

| Artefato | Função |
| --- | --- |
| roadmap.md | ondas e critérios de entrada/saída |
| tasks.md | tarefas do programa |
| verification.md | comandos, resultados e desvios |
| pacotes 0027–0034 | contrato, runtime, intake, qualidade, documentos, observabilidade e release |
| pacote 0035 | fila, estado, work packs e execução retomável |
| pacotes 0036–0040 | topologia, identidade, federação, adapters Juscraper e coleta reproduzível |

## Artefatos por provider durante implementação

- pacote SDD próprio;
- dossier canônico;
- source contract compatível;
- capability runtime;
- fixture de sucesso, vazio e falha;
- golden canonical output;
- testes de parser, contrato, identidade e paginação;
- evidência live bounded quando autorizada;
- scorecard e decisão de maturidade;
- changelog e migração quando aplicável.
- fingerprint de evidência e regra de revalidação;
- autoridade, collection ID, grau, período e tipo documental;
- decisão de disposição com owner, prazo e gatilho de retomada.
