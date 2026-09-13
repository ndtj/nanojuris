# SDD 0109 — SJUR/TRE runtime family

Status: verified

## Objetivo

Disponibilizar o binding oficial `tre_sjur_jurisprudencia` no runtime padrão
do NanoJuris para que aplicações possam consultar explicitamente qualquer uma
das 27 autoridades eleitorais regionais (`authority=TRE-XX`). A mudança não
promove a família para a busca federada padrão: a API pública ainda não provou
paginação remota estável por UF.

## Escopo

- Reutilizar o adapter e transporte já implementados em
  `tse_sjur_jurisprudencia.py`.
- Exigir autoridade explícita; nunca inferir uma UF a partir do texto.
- Manter classificação de primeiro grau, desconhecido, bloqueio, schema e
  documento inválido explícita.
- Registrar a família como runtime disponível, mantendo
  `supports_unified_search=false` e `opt_in_unified_search=true`.
- Manter adapters individuais por UF disponíveis somente com
  `include_candidate_providers=True`.

## Critérios de aceitação

- **AC-001:** `NanoJurisClient().list_sources()` contém
  `tre_sjur_jurisprudencia`.
- **AC-002:** A família rejeita consulta sem `authority` e normaliza
  `TRE-SP`/`TRESP`.
- **AC-003:** A rota oficial é chamada apenas com HTTPS, transporte compartilhado e
  pacing configurado.
- **AC-004:** Página repetida, total desconhecido e PDF inválido permanecem estados
  explícitos; nenhum erro externo vira lista vazia.
- **AC-005:** A família continua fora de `_default_unified_sources()` e não é incluída
  no rollout padrão.
- **AC-006:** Suite focada, SDD, Ruff, mypy, compileall e suíte completa permanecem
  verdes.

## Não objetivos

- Não criar escopo agregado `TRE-aggregate`.
- Não contornar CAPTCHA, WAF, login, TLS ou rate limit.
- Não declarar cobertura eleitoral 27/27 nem completude do acervo.
- Não executar commit, push, release, deploy ou mudança de produção.
