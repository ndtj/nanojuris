# TJMG Biblioteca Digital — jurisprudência pública de segundo grau

Status: verified

## Objetivo

Disponibilizar a coleção oficial de jurisprudência da Biblioteca Digital do
TJMG por meio da API pública DSpace, sem depender do formulário legado protegido
por CAPTCHA. A superfície retorna registros individuais de acórdãos de segundo
grau e, quando publicado, o PDF original.

## Requisitos

- REQ-001: aceitar termo, número ou frase e rejeitar escopos incompatíveis com
  segundo grau estadual.
- REQ-002: consultar as coleções públicas cível, criminal e órgão especial,
  preservando metadados e `SourceTrace`.
- REQ-003: normalizar autoridade, ramo, grau, instância, coleção, processo,
  classe, órgão julgador, relator, datas, ementa e URL do item.
- REQ-004: resolver o bitstream ORIGINAL sob demanda, limitar o PDF a 20 MB e
  extrair texto com o pipeline canônico.
- REQ-005: expor timeout, TLS, HTTP 401/403/429, schema inválido e documento
  ausente como estados explícitos; nunca convertê-los em vazio.

## Critérios de aceitação

- AC-001: fixture de busca produz registro `authority=TJMG`, `branch=state`,
  `degree=second`, `instance=second` e coleção CJSG específica.
- AC-002: consulta live pública retorna resultados e totais das três coleções;
  item live resolve PDF `application/pdf` e texto não vazio.
- AC-003: filtros incompatíveis são rejeitados e o total conhecido é separado
  de total desconhecido.
- AC-004: fixtures cobrem resultado, vazio, schema inválido e documento
  indisponível, com testes de transporte e normalização.
