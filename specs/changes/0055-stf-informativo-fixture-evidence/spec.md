# 0055 - Fixture de replay do STF Informativo

Status: verified
Owner: Provider Engineering, Data Quality, QA e Security

## Intencao

Substituir a dependencia exclusiva de um builder XLSX inline por uma fixture
JSON normalizada e versionada para replay do parser do STF Informativo. A
fixture e sintetica e nao representa acervo, URL ou resposta live do tribunal.

## Requisitos

- REQ-001: versionar linhas normalizadas com identificador, classe, numero,
  ementa/tese, relator, orgao e data;
- REQ-002: exercitar `parse_stf_informativo_rows` com a fixture versionada;
- REQ-003: preservar `raw`, identidade, data ISO e SourceTrace;
- REQ-004: manter o builder XLSX para testes de contrato estrutural e falhas;
- REQ-005: atualizar dossie, contrato, auditoria e workpack sem afirmar dados
  reais;
- REQ-006: nenhuma chamada live adicional, promocao, deploy ou alteracao de
  producao.

## Criterios de aceite

- AC-001: `tests/fixtures/stf_informativo_rows.json` e carregada por teste
  provider-especifico;
- AC-002: o parser retorna resultado com id, numero, resumo, data e raw;
- AC-003: a auditoria classifica STF como `versioned_and_inline`, nao como
  `inline_test_only` ou divida sem evidencia;
- AC-004: testes e gates locais passam;
- AC-005: a natureza sintetica e os limites permanecem documentados.

## Fora de escopo

Persistencia do XLSX live, captura de corpo oficial, alteracao do contrato HTTP,
inteiro teor, novos endpoints ou reclassificacao de acesso.
