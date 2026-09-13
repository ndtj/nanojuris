# SDD 0073 — STJ Informativo CNOT fetch

Status: `verified`

## Intent

Permitir recuperar a nota pública CNOT referenciada por resultados do
`stj_informativo`, sem confundir esse conteúdo com o acórdão SCON relacionado.

## Requisitos

- **REQ-001** — preservar o vínculo entre resultado e URL CNOT observada.
- **REQ-002** — buscar CNOT pelo transporte compartilhado, com allowlist,
  limites, MIME, hash e `SourceTrace`.
- **REQ-003** — manter URLs SCON separadas; bloqueio do acórdão não pode ser
  convertido em ausência da nota.
- **REQ-004** — rejeitar IDs arbitrários e URLs fora do host oficial.

## Critérios de aceitação

- **AC-001** — um resultado fixture permite `get_document` com texto completo.
- **AC-002** — `get_decisions` empacota a nota CNOT sem baixar SCON.
- **AC-003** — URL não confiável é rejeitada e a suíte existente permanece verde.
