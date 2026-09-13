# Reconciliação com mudanças SDD anteriores

Este artefato evita duas filas concorrentes para o mesmo problema.

| Mudança | Evidência reaproveitada | Responsabilidade futura |
| --- | --- | --- |
| 0006-all-provider-discovery | sweep bounded, rotas e TODOs | fonte histórica de discovery; novos ciclos entram no estado 0035 |
| 0007-unified-contract-maturation | matriz de filtros, paginação e completude | requisitos estruturais seguem em 0027 e 0031 |
| 0008-provider-contract-closure | closure ledger e estados de TODO | ledger alimenta gaps e bloqueios do 0035 |
| 0009-candidate-adapter-promotion | gate de candidates | intake segue em 0029 e promoção estadual em 0030 |
| 0011-data-quality-hardening | identidade e quarentena | invariantes seguem obrigatórios em 0031 |
| 0013-provider-local-contract-closure | auditoria offline | base do gerador de work packs |
| 0014-federated-quality-observability | isolamento e erro seguro | pré-requisito do 0033 |
| 0015-provider-evidence-hardening | identidade eproc e evidência | pré-requisito dos work packs eproc |
| 0025-tjes-public-json-adapter | contrato TJES proposto | unidade da onda 1 em 0030 |

## Regra

As mudanças antigas não são marcadas superseded automaticamente. O owner humano
deve aceitar a reconciliação e somente então atualizar status e links. Até lá,
0035 referencia e preserva as evidências existentes.
