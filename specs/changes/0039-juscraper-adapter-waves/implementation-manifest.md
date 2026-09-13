# Manifesto de implementacao das superficies Juscraper

Snapshot de planejamento: `604c1dd70d6f313011cc1079790febe6c71807e2`.
Este manifesto transforma a triagem em unidades executaveis. Cada pacote exige
contrato proprio e nao autoriza chamada em escala, deploy ou release.

O quadro de retomada versionado em
`docs/provider-discovery/adapter-wave-board-20260901.*` e a fonte operacional
da ordem da onda. Ele junta o diff semantico com as duas fotografias live e
nao altera o estado de nenhum provider.

## Unidades de ganho novo

| Ordem | Pacote | Collection/binding | Resultado esperado | Dependencias |
| --- | --- | --- | --- | --- |
| A1 | 0025 reconciliado | TJES segundo grau (`pje2g`, `pje2g_mono`, `legado`) | provider JSON sem misturar graus | 0036, 0037, 0027, reuso |
| A2 | 0041 aberto | `tjrn_jurisprudencia` | busca textual oficial de segundo grau | 0029, 0036-0038 |
| A3 | 0042 concluído localmente | `tjro_jurisprudencia` | fonte textual separada do LIAME, habilitada na federação padrão | 0029, 0036-0038 |
| A4 | 0043 aberto | `tjto_ementa_detail` | enriquecimento lazy sem apagar base | 0037 e provider TJTO |
| C1 | 0044 reservado | `tjes_cjpg` | decisoes de primeiro grau | 0025, 0036-0038 |
| C2 | 0045 reservado | `tjes_turma_recursal` | julgados de turma recursal | 0025, 0036-0038 |
| C3 | 0046 reservado | `tjsp_cjpg` | decisoes de primeiro grau | 0036-0038 |
| C4 | 0047 reservado | `tjto_cjpg` | decisoes de primeiro grau | 0036-0038 |

## Hardening diferencial

O pacote coordenador 0048 sera aberto apos comparar os 19 overlaps do ledger
0029. Cada outcome deve ser `adopt_gain`, `no_gain`, `defer` ou
`blocked_access`; nenhum ganho de um tribunal e aplicado a outro sem fixture e
contrato proprio.

## Alto risco

| Item | Estado | Condicao de retomada |
| --- | --- | --- |
| TJAP | `blocked_access` | superficie oficial sem Turnstile ou bypass |
| TJMG | `blocked_access` | rota publica sem OCR de CAPTCHA; parser documental pode ser isolado |
| TJRJ | `deferred_with_review` | confirmacao oficial de acesso e parecer Security/Legal |

## Definition of Ready

- authority, collection e surface reconciliadas em 0036;
- fonte oficial, metodo, payload, filtros, pagina e resposta reproduzidos;
- licenca/provenance decididas e fixture propria sanitizada possivel;
- identidade 0037, semantica 0038 e budgets 0028/0033 definidos.

## Definition of Done

- SDD individual, threat model, dossier, source contract e capability sincronizados;
- fixtures de sucesso, vazio confirmado, invalido, timeout, acesso e schema drift;
- parser preserva raw minimizado, SourceTrace, identidade e completude;
- equivalencia diferencial, Ruff, mypy, suite focada e suite completa verdes;
- nenhuma falha 401/403 vira empty e nenhum provider e default sem gate 0034;
- decisao de maturidade e autorizacao humana registradas.

## Politica de delta upstream

No inicio de cada coverage epoch: consultar HEAD em modo read-only, registrar
commits, comparar arvore/classes/rotas/schemas/licenca e reabrir apenas linhas
cujo fingerprint mudou. Nunca copiar ou promover automaticamente.
