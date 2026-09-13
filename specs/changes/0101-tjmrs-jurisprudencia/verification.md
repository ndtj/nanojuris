# Verification — SDD 0101

## Evidência live

- `GET https://www.tjmrs.jus.br/abreJurisprudencia.php?processo=10002045120189210002`
  respondeu HTTP 200 com documento `6270`, ementa, relator e texto integral.
- `GET https://www.tjmrs.jus.br/abreJurisprudencia.php?processo=00704302520239210002&processo_evento=771754928753752953978209109893`
  respondeu HTTP 200 com documento `20558`, ementa, relator e texto integral.
- Processo inexistente retornou HTTP 200 com mensagens explícitas de ausência,
  classificado como `authoritative_empty`.
- Sem credenciais, cookies, tokens, proxy ou bypass; corpos não foram gravados.
- Evidência redigida: `docs/provider-discovery/tjmrs-jurisprudencia-live-20260909.json`.

## Verificação local

Comandos executados após o lote:

```text
python -m pytest -q tests/test_tjmrs_jurisprudencia.py
python tools/validate_sdd.py
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

O provider fica runtime opt-in e fora da federação padrão. Release, push,
deploy e produção não fazem parte desta mudança.

## Resultados

- Parser, transporte, vazio autoritativo, bloqueio, filtros e documento:
  aprovados na suíte focada.
- O catálogo gerado registra o provider como runtime, com inteiro teor e live
  válido, mas `supports_unified_search=false`.
- A consulta geral do TJMRS continua descoberta pendente; a cobertura militar
  nacional não é inferida deste adapter.

## Rastreabilidade

| Requisito | Evidência |
|---|---|
| REQ-001/AC-001 | `tests/test_tjmrs_jurisprudencia.py` e fixtures de sucesso/vazio |
| REQ-002/REQ-003/AC-002 | parser canônico e testes de identidade/filtros |
| REQ-004/AC-004 | `get_document` e `CanonicalDocument` com hash/bytes |
| REQ-005/AC-003 | teste HTTP 403 e fixture vazia explícita |
| REQ-006/AC-006 | `NanoJurisClient` registra runtime opt-in; capability fora da federação |
| AC-005 | `docs/provider-discovery/tjmrs-jurisprudencia-live-20260909.json` |
