# Verificação

## Resultados

- Chamada live bounded em 2026-09-01: HTTP 200, JSON válido, dois documentos
  na janela e total declarado de 313.496; corpo não persistido.
- Fixtures e parser: sucesso, vazio completo, raiz inválida, core incorreto e
  campos desconhecidos preservados.
- Teste focado do adapter: 13 casos aprovados.
- O provider está registrado como `tjes_cjpg`, com `supports_unified_search=True`
  e modo `enabled` no manifesto técnico; a federação mantém o binding `pje1g`
  separado de CJSG.

## Rastreabilidade

| Requisito | Evidência |
| --- | --- |
| REQ-001/004 | `src/nanojuris/providers/tjes_cjpg.py` e `test_tjes_cjpg.py` |
| REQ-002/003 | parser, `raw`, `SourceTrace` e teste de canonicalização |
| REQ-005 | testes parametrizados de 400/401/403/422/429/500 e schema drift |
| REQ-006 | capability e catálogo `tjes_cjpg` opt-in |
| REQ-007 | revisão de código; sem browser/cookies/bypass |

## Gates pendentes

O resultado técnico autoriza o uso local/federado nesta rodada conforme decisão
do operador. Não houve deploy, push ou alteração de produção; coleta em escala
e publicação continuam fora do escopo.
