# Provider evidence hardening

Status: `verified`

## Intent

Revisar quatro providers prioritarios sem chamadas live, distinguir evidência
local de evidência documentada e impedir que o parser eproc emita registros sem
identidade estável.

## Scope

- `tjpa_jurisprudencia_bff`;
- `tjpb_pje_jurisprudencia`;
- `tjrj_eproc_jurisprudencia`;
- `tjsc_eproc_jurisprudencia`;
- parser eproc compartilhado e testes determinísticos.

## Requirements

- **REQ-001**: um resultado eproc deve possuir `id_jurisprudencia` ou número de
  processo antes de ser normalizado.
- **REQ-002**: falta de identidade deve ser um erro explícito de mudança de
  contrato, nunca um ID vazio ou potencialmente colidido.
- **REQ-003**: a auditoria deve distinguir fixture específica, fixture
  compartilhada, payload inline e evidência live documentada.
- **REQ-004**: nenhuma rota ou comportamento externo deve ser inferido sem
  evidência versionada ou validação autorizada.

## Acceptance criteria

- **AC-001**: card eproc sem ID e sem processo é rejeitado determinísticamente.
- **AC-002**: TJRJ e TJSC continuam usando host, court e prefixo próprios.
- **AC-003**: auditoria dos quatro providers é reproduzível sem rede.
- **AC-004**: testes focados e SDD passam.

## Out of scope

Não inclui chamadas live, coleta em escala, bypass de controles ou promoção de
rotas não comprovadas.
