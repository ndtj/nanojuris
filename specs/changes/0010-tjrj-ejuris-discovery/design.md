# Design

## Registro

Adicionar `tjrj_ejuris` somente à lista `candidates` de
`docs/registry/providers.json`. O catálogo completo e os índices de coverage
são derivados pelos geradores existentes.

## Dossiês

O README canônico e a cópia em `docs/source-contracts/` descrevem a superfície
WebForms, o estado `candidate_needs_har`, a ausência de schema de resultados e
as condições necessárias para promoção futura.

## Segurança e escopo

Não implementar POST especulativo, reCAPTCHA, persistência de sessão ou
qualquer mecanismo de contorno. O provider eproc do TJRJ continua sendo a
superfície runtime independente.
