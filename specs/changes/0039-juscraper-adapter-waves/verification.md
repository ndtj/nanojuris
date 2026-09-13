# Verificação

Status: verified — intake, independent adapters and technical promotion gates
are complete for the currently eligible wave; remaining candidates retain
explicit evidence/access states.

## Gates previstos

- package SDD e verification por superfície;
- equivalência offline e fixtures próprias;
- licença/NOTICE e dependency audit;
- estados negativos e nenhum false empty;
- canonical identity e busca federada;
- suíte completa, docs geradas e release rehearsal sem produção.

## Resultados

O intake estático, a reconciliação de superfícies e os gates por adapter foram
executados. Os adapters independentes da onda elegível possuem contrato,
fixtures, testes e evidência live bounded; fontes candidatas sem esse conjunto
continuam fora da federação.

| Gate | Estado | Evidência |
| --- | --- | --- |
| intake upstream fixado | pass | `docs/provider-discovery/juscraper-intake-20260901.*` |
| pacotes TJ/CJSG/CJPG inventariados | pass | 25 TJ, 3 CJPG e 1 detalhe |
| smoke live bounded TJES/TJRN | pass (evidência) | `juscraper-live-smoke-20260901.*` |
| rechecagem live TJES/TJRN | pass com estados distintos | `juscraper-live-recheck-20260901.*`; TJES 200, TJRN 403 |
| adapter runtime | pass with limits | adapters NanoJuris independentes; nenhum código upstream copiado |
| equivalência e fixtures próprias | pass with limits | concluído para a onda elegível; candidatos restantes aguardam evidência |
| produção | não alterada | sem deploy, push ou promoção de catálogo |

## Rastreabilidade

Os gates previstos correspondem aos requisitos e tarefas de `traceability.md`.

O board offline `adapter-wave-board-20260901.json/.md` continua sendo a fila de
evidências: candidatos sem contrato/live/fixtures ficam adiados, enquanto os
adapters tecnicamente prontos são promovidos somente pelo manifesto gerado.
TJTO/CJPG e demais superfícies bloqueadas permanecem explicitamente fora da
federação; não há promoção implícita por possuir um módulo upstream equivalente.

O check de reuso e uma barreira tecnica adicional, nao uma autorizacao legal.

Atualização de 2026-09-02: o board foi regenerado com o sweep de oito
candidates. TJAP, TJMG e TJRJ possuem `resume_when` e estados explícitos;
nenhum deles foi promovido sem contrato reproduzível.
