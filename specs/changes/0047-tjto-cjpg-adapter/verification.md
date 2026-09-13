# Verificacao

## Resultados

- A rechecagem de 2026-09-07 executou `POST https://jurisprudencia.tjto.jus.br/consulta.php`
  com `tip_criterio_inst=1`, `type_minuta_selected=3` e duas paginas bounded.
- Ambas responderam HTTP 200, com 10 registros por pagina, total conhecido
  86.023 e IDs sem sobreposicao. Os cards confirmam sentenca e unidade de
  primeiro grau.
- A rodada anterior, que recebeu HTTP 202/WAF na segunda pagina, permanece
  como evidencia historica. O cliente mantem 202/403 como acesso controlado e
  nunca como vazio.
- O binding `tjto_jurisprudencia` foi promovido tecnicamente para CJPG e passou
  a integrar a matriz/federacao local; isso nao autoriza deploy nem substitui
  revisao humana de governanca.

## Rastreabilidade

| Requisito | Evidencia |
| --- | --- |
| REQ-001/003 | `docs/provider-discovery/tjto-cjpg-live-20260907.json` |
| REQ-002/004 | duas paginas, parser, fixture e estados 202/403 explicitos |

## Gates

Os gates tecnicos estao concluidos localmente. Revisao humana de governanca
permanece separada. Nao houve deploy, push ou alteracao de producao.
