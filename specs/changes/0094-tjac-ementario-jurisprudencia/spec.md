# TJAC Ementario de Jurisprudencia

Status: `verified`

## Objetivo

Adicionar uma fonte oficial e publica do TJAC que entrega ementas textuais de
decisoes de segundo grau em volumes PDF semestrais. A colecao complementa o
provider CJSG online existente e nao sera apresentada como acervo integral.

## Escopo

- baixar somente o volume PDF publicado na pagina oficial do Ementario;
- extrair uma janela local limitada de decisoes identificadas por numero CNJ;
- preservar autoridade, ramo, grau, instancia, colecao, tipo, relator e data
  quando presentes no texto;
- aplicar termo, frase e numero como pos-filtros locais;
- expor `total_known=false` e `is_complete=false` quando o volume nao informar
  total pesquisavel;
- incluir a fonte na busca federada como resultado parcial apos os gates locais.

Fora de escopo: OCR, consulta processual, dados de partes, bypass de controles,
indexacao persistente, cobertura de primeiro grau e afirmacao de completude.

## Requisitos

- REQ-001: aceitar apenas HTTPS no host oficial `tjac.jus.br`.
- REQ-002: rejeitar query sem termo, frase ou numero.
- REQ-003: aceitar somente `degree=second`, `instance=second`, `branch=state`
  e `authority=TJAC` quando informados.
- REQ-004: rejeitar PDF invalido, excesso de bytes ou excesso de paginas como
  erro de contrato, nunca como resultado vazio.
- REQ-005: cada registro aceito deve ter numero CNJ, identidade de segundo grau,
  ementa textual nao vazia e `SourceTrace`.
- REQ-006: documentos oficiais somente podem ser obtidos por URL HTTPS do
  mesmo host e ficam sujeitos ao pipeline compartilhado de limites.
- REQ-007: a federacao deve informar a natureza estatica, janela limitada e
  total desconhecido.

## Criterios de aceite

- AC-001: fixture de volume com duas decisoes produz registros distintos.
- AC-002: termo, numero e frase filtram localmente sem alterar identidade.
- AC-003: primeiro grau, outro ramo e PDF/schema invalido sao rejeitados.
- AC-004: chamada live bounded retorna HTTP 200, PDF e ao menos uma decisao.
- AC-005: catalogo e provider registram a fonte como `valid`, parcial e
  `supports_unified_search=true` sem declarar completude.
- AC-006: suite focada, SDD, Ruff, mypy e suite completa permanecem verdes.
