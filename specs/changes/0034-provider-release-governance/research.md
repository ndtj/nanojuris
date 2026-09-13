# Pesquisa — governança de release

Status: in_progress

## Evidência atual

A biblioteca já usa SemVer, build, testes, documentação gerada e múltiplas
interfaces. Mudanças de provider podem ser não breaking no Python e ainda mudar
resultados, campos, volume e custo operacional.

## Decisão orientada

Tratar contrato de dados e capability como parte da compatibilidade. Release
rehearsal deve provar artefatos e rollback sem publicação.

## Lacunas

- política formal de depreciação;
- feature flags por provider;
- schema diff automatizado;
- modelo de aprovação e provenance da release.
