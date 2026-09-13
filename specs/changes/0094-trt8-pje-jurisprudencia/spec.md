# SDD 0094 — superfície TRT8 PJe de jurisprudência

Status: `in_progress`

## Objetivo

Adicionar ao NanoJuris a busca oficial pública de jurisprudência do TRT8 com
contrato explícito de segundo grau, paginação, filtros e inteiro teor sob
demanda, sem automatizar desafios de acesso.

## Requisitos

- **REQ-094-001** — usar somente o host oficial `pje.trt8.jus.br` e o transporte compartilhado.
- **REQ-094-002** — fixar `instancia=2ª Instância` e `tipoDocumento=Acórdão` em toda busca.
- **REQ-094-003** — traduzir apenas filtros comprovados e registrar `filters_applied`.
- **REQ-094-004** — preservar número, classe, órgão, relator, assuntos, datas, raw e SourceTrace.
- **REQ-094-005** — buscar detalhe oficial sob demanda e normalizar `inteiroTeorHTML`.
- **REQ-094-006** — separar vazio autoritativo de bloqueio, timeout, rate limit e schema drift.
- **REQ-094-007** — manter a fonte opt-in até o smoke federado e a promoção técnica.

## Critérios de aceite

- **AC-094-001** — fixture de sucesso e segunda página são parseadas sem sobreposição.
- **AC-094-002** — resultado e detalhe preservam `TRT8/labor/second/CJSG/acordao`.
- **AC-094-003** — vazio, desafio e schema inválido produzem estados distintos.
- **AC-094-004** — filtros de classe, órgão, relator e publicação são traduzidos.
- **AC-094-005** — `CanonicalDocument` contém texto integral e trace oficial.
