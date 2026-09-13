# ADR-001 — adaptação seletiva em vez de dependência obrigatória

Status: proposed
Data: 2026-09-01

## Contexto

O Juscraper possui parsers e rotas úteis, mas usa modelos, dependências e
interfaces diferentes da NanoJuris.

## Decisão

Usar o Juscraper como fonte licenciada de evidência, algoritmos e fixtures,
adotando apenas elementos equivalentes após revisão. Não adicioná-lo como
dependência runtime obrigatória.

## Consequências

- preserva o contrato canônico da NanoJuris;
- evita pandas e autenticação/browser-cookie no núcleo;
- exige manutenção consciente do código adaptado;
- requer atribuição MIT para cópias substanciais.
