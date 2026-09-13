# Especificação

Status: proposed

## Objetivo

Disponibilizar pesquisa bounded nos boletins oficiais do TJMG com identidade
canônica de segundo grau, paginação offset, documentos PDF públicos e estados
de erro explícitos.

## Requisitos funcionais

- RF-001: consultar somente a coleção DSpace oficial do Boletim de Jurisprudência;
- RF-002: aceitar texto, frase exata, número, página e filtros semânticos validados;
- RF-003: produzir `authority=TJMG`, `branch=state`, `degree=second` e
  `instance=second`;
- RF-004: preservar assuntos, título, data, item, trace e URL do documento;
- RF-005: distinguir total zero, total conhecido e total desconhecido;
- RF-006: obter o bitstream `ORIGINAL` somente sob demanda;
- RF-007: classificar timeout, TLS, 401/403/429, schema e bitstream ausente
  explicitamente;
- RF-008: não usar nem contornar o formulário legado protegido por CAPTCHA.

## Critérios de aceitação

- AC-001: Fixture de sucesso gera registro de segundo grau da coleção correta.
- AC-002: Fixture vazia com `totalElements=0` gera vazio autoritativo.
- AC-003: Envelope inválido gera erro de schema, nunca vazio.
- AC-004: Documento oficial retorna MIME PDF, hash e `access_status=public`.
- AC-005: Testes, Ruff, mypy, compileall e SDD passam.
