# 0035 — orquestração retomável de conclusão dos providers

Status: verified
Owner: Principal AI Engineer e QA

## Intenção

Permitir execução autônoma, longa e retomável do programa de providers, com
estado persistente, trabalho finito, revisão proporcional ao risco e respeito
aos limites de acesso. Autonomia significa persistência operacional, não
autoridade para publicar, burlar controles ou declarar cobertura sem evidência.

## Requisitos

- REQ-001: inventariar dinamicamente todas as fontes do catálogo e gerar um
  work pack por `source_id`, sem fixar a quantidade atual como limite nacional.
- REQ-002: distinguir instituição, coleção, superfície, provider runtime,
  candidato, família técnica e item fora de escopo.
- REQ-003: manter por fonte estado, fase, tentativas, owner, evidência,
  fingerprint, saúde operacional, disposição e condições de retomada.
- REQ-004: priorizar trabalho por risco, valor jurisprudencial, lacuna de
  cobertura nacional e dependências, sem usar maturidade documental como prova
  de saúde live.
- REQ-005: somente estados `accepted` e `accepted_with_limitations` podem
  representar fechamento positivo; ambos exigem DoD e verification.
- REQ-006: bloqueio externo nunca é fechamento automático. Após três
  ocorrências iguais, o item passa a `waiting_evidence` ou
  `deferred_with_review`, com evidência, owner, `review_after` e `resume_when`.
- REQ-007: execução deve ser checkpointada, idempotente e retomável após
  interrupção.
- REQ-008: chamadas live devem ser bounded, opt-in, responsáveis e separadas da
  geração offline de artefatos.
- REQ-009: release, publicação, credenciais, produção e operações destrutivas
  exigem autorização humana explícita.
- REQ-010: regeneração deve preservar progresso válido, mas invalidar conclusão
  quando o fingerprint de evidência mudar.
- REQ-011: itens terminais válidos são `accepted`,
  `accepted_with_limitations`, `rejected`, `deferred_with_review` e
  `out_of_scope`; `blocked` não é terminal.
- REQ-012: a fila deve começar pela topologia 0036 e pelos gates transversais
  0037/0038 antes de claims nacionais ou ondas de adapters 0039.
- REQ-013: estados v1 `complete`, `blocked` e `deferred` são migrados para
  `stale` ou `waiting_evidence`, preservando evidência e exigindo nova revisão.
- REQ-014: o comando bounded `complete_provider_workpacks.py` deve processar
  cada fonte do catálogo e registrar uma disposição terminal determinística,
  sem chamadas de rede, mutação de federação ou deploy.
- REQ-015: fontes tecnicamente habilitadas devem ser aceitas com limitações
  residuais explícitas; fontes sem contrato, fixture ou evidência live válida
  devem ser adiadas com owner, data de revisão e condição objetiva de retomada.
- REQ-016: work packs regenerados devem marcar o processamento da decisão sem
  transformar evidência ausente em sucesso; lacunas permanecem visíveis no
  texto do work pack e no estado persistente.

## Critérios de aceite

- AC-001: baseline e work packs têm a mesma cardinalidade do catálogo no momento
  da geração e aceitam crescimento sem alterar testes.
- AC-002: cada fonte recebe work pack, prioridade, alvo e fingerprint.
- AC-003: regeneração preserva evidência quando a entrada é igual e muda o estado
  terminal para `stale` quando a evidência relevante muda.
- AC-004: saúde operacional e disposição de programa são campos independentes.
- AC-005: deferimento exige owner, motivo, `review_after` e `resume_when`.
- AC-006: runbook define loop, checkpoints, revisão, ordem dos SDDs e condições
  de parada.
- AC-007: testes do gerador, Ruff, mypy e validação SDD passam.
- AC-008: nenhuma rede ou produção é usada para gerar os artefatos.
- AC-009: teste prova a migração v1→v2 sem perda de evidência.
- AC-010: uma execução bounded preenche disposição, status, saúde operacional,
  owner, evidência, fingerprint e retomada para todas as entradas atuais.
- AC-011: a execução é idempotente, offline e deixa zero checkboxes WP abertas,
  mantendo limitações e bloqueios explícitos.

## Não objetivos

- executar loop infinito sem estado ou objetivo;
- repetir continuamente uma fonte bloqueada;
- garantir disponibilidade de sistemas externos;
- autorizar bypass, credenciais, deploy ou publicação;
- considerar o catálogo atual como toda a jurisprudência brasileira.
