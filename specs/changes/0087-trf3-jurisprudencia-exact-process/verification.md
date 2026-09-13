# Verification

## Resultados

Implementação local concluída com fixtures e contrato explícito. A promoção
federada permanece bloqueada pela ausência de resposta live direta reproduzida.

## Local

- `python -m pytest -q tests/test_trf3_jurisprudencia.py` — 7 passed.
- Ruff check e format no adapter e testes — pass.
- mypy no adapter — pass.

## Live

Tentativas bounded sem credenciais, proxy ou bypass no host oficial estão
registradas em `docs/provider-discovery/trf3-jurisprudencia-live-20260907.json`.
As duas rotas expiraram por timeout de leitura. O estado correto é
`transport_error/source_unavailable`, não vazio.

## Decisão

O provider está disponível para consulta explícita por processo e permanece
fora da federação padrão. A promoção depende exclusivamente de nova evidência
live reproduzível e não de uma resposta HTTP 200 isolada.

## Rastreabilidade

| Critério | Evidência |
| --- | --- |
| AC-001/AC-002 | `tests/test_trf3_jurisprudencia.py`, parser e capabilities |
| AC-003/AC-004 | fixtures de processo vazio/shape inválido e tratamento de exceções |
| AC-005 | `get_document`, hash, bytes e `SourceTrace` |
| AC-006 | `docs/provider-discovery/trf3-jurisprudencia-live-20260907.json` |
