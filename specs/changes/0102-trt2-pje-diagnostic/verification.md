# Verification - SDD 0102

## Evidencia live

- `GET /juris-backend/api/opcoes`: HTTP 200, catalogo publico e
  `captchaOption=2`.
- `POST /juris-backend/api/filtros`: HTTP 200, agregacoes publicas de assunto,
  ano, tipo documental, instancia, orgao e classe.
- `POST /juris-backend/api/documentos`: HTTP 200 com `tokenDesafio`, imagem e
  audio, sem documentos; classificado como `access_blocked`.
- Evidencia redigida: `docs/provider-discovery/trt2-pje-query-contract-live-20260910.json`.

## Verificacao local

```text
python -m pytest -q tests/test_trt2_pje_jurisprudencia.py tests/test_trt2_route_evidence.py
python -m ruff check src/nanojuris/providers/trt2_pje_jurisprudencia.py tests/test_trt2_pje_jurisprudencia.py
python -m ruff format --check src/nanojuris/providers/trt2_pje_jurisprudencia.py tests/test_trt2_pje_jurisprudencia.py
python -m mypy src/nanojuris/providers/trt2_pje_jurisprudencia.py
python -m compileall -q src/nanojuris/providers/trt2_pje_jurisprudencia.py
```

Resultado focado: 6 testes do adapter aprovados. O payload agora reproduz o
`QUERY_INICIAL` do frontend oficial (`andField`, `paginationPosition`,
`paginationSize`, agregações e filtros em listas); a sonda bounded de filtros
confirmou HTTP 200 e catálogo público. O provider continua opt-in;
nenhum commit, push, release, deploy ou alteracao de producao foi executado.

## Resultados

- Adapter diagnóstico implementado com transporte compartilhado, allowlist,
  limite de resposta e classificação explícita de desafio.
- Opções e filtros públicos são utilizáveis para diagnóstico; a rota de
  documentos respondeu desafio (`tokenDesafio`, imagem e áudio), portanto não
  há corpus textual promovível neste ciclo.
- Runtime permanece opt-in e fora da federação padrão. O gate externo T007
  continua pendente sem bloquear as demais superfícies.

## Rastreabilidade

| Requisito | Evidência |
|---|---|
| REQ-001/AC-001 | `tests/test_trt2_pje_jurisprudencia.py::test_get_parameters_redacts_secret` |
| REQ-002 | `tests/test_trt2_pje_jurisprudencia.py::test_filter_catalog` |
| REQ-003/AC-002 | `tests/test_trt2_pje_jurisprudencia.py::test_search_preserves_second_degree_payload` |
| REQ-004/AC-002/AC-003 | `tests/test_trt2_pje_jurisprudencia.py::test_challenge_is_access_control` |
| REQ-005 | parser e contrato do adapter em `src/nanojuris/providers/trt2_pje_jurisprudencia.py` |
| REQ-006/AC-004/AC-005 | capability opt-in e `NanoJurisClient(include_candidate_providers=True)` |
