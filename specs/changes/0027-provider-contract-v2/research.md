# Pesquisa — contrato de provider v2

Status: in_progress

## Evidência atual

- ProviderCapabilities já alimenta catálogo e roteamento.
- CanonicalDecision, CanonicalPrecedent e CanonicalDocument já existem.
- 0007 registra filtros e completude ainda não fechados por provider.
- 0011 endureceu identidade e quarentena sem quebrar a facade.

## Decisão orientada

Evoluir internamente e preservar a API externa por adapter de compatibilidade.
O esquema novo deve representar unknown de forma explícita.

## Lacuna

É necessário gerar uma fotografia pública de assinaturas e serializações antes
de alterar qualquer modelo.
