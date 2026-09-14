# SDD 0117 - TRT3 ementario de jurisprudencia

Status: `verified`  
Owner: Provider Engineering  
Data: 2026-09-10

## Objetivo

Expor a colecao publica de volumes de ementas do TRT3 como fonte contextual,
com identidade explicita de segundo grau e sem alegar cobertura geral.

## Requisitos

- **REQ-001** - consultar somente a pesquisa avancada e PDFs oficiais allowlisted;
- **REQ-002** - extrair identificadores CNJ e blocos de ementa com parser bounded;
- **REQ-003** - preservar autoridade, ramo, grau, instancia, colecao, URL, raw e trace;
- **REQ-004** - filtrar texto, frase e numero localmente, apos uma janela de no maximo tres volumes;
- **REQ-005** - classificar HTML/PDF invalido, erro HTTP, timeout e schema drift explicitamente;
- **REQ-006** - manter a colecao opt-in/contextual, fora da federacao padrao.

## Fora de escopo

Busca geral do TRT3, total de decisoes do corpus, inteiro teor dos votos, OCR,
bypass de controles e deploy. O total remoto de volumes e preservado apenas
como diagnostico e nao e usado como total de decisoes.

## Acceptance criteria IDs

- `AC-001` - consultar a pesquisa avancada oficial e baixar somente PDFs
  allowlisted, validando MIME e magic bytes;
- `AC-002` - cada registro aceito preserva `authority=TRT3`, `branch=labor`,
  `degree=second`, `instance=second` e `collection=TRT3_EMENTARIO`;
- `AC-003` - texto, frase exata, numero e janela bounded de volumes sao aplicados
  sem confundir PDF invalido ou schema drift com resultado vazio;
- `AC-004` - a sonda live reproduzivel da pesquisa DSpace permanece contextual/
  opt-in e nao habilita a federacao padrao;
- `AC-005` - o documento PDF observado e recuperavel com `SourceTrace` e
  `extraction_status` explicito.

## Aceite

O adapter, fixture sanitizada, testes focados, evidencia live e gates locais
devem passar. A promocao padrao permanece desabilitada por decisao tecnica.
