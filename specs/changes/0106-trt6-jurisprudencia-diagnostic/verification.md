# Verificação — SDD 0106

## Evidência live

- `https://pje.trt6.jus.br/jurisprudencia/`: SPA oficial HTTP 200.
- `https://apps.trt6.jus.br/acordaos/`: formulário oficial HTTP 200, com aviso
  de reCAPTCHA e campos textuais de acórdão.
- `POST /juris-backend/api/documentos` sem token legítimo: resposta JSON
  `Erro na validação do Recaptcha`; classificada como acesso controlado.
- `POST /juris-backend/api/filtros` com payload mínimo: HTTP 200, 85.896 bytes,
  9 agregações públicas e `documents=[]`; evidência redigida em
  `docs/provider-discovery/trt6-filter-catalog-live-20260910.json`.

## Testes

`python -m pytest -q tests/test_trt6_jurisprudencia.py`

O provider não é promovido: não há fixture de resultados, contrato de
paginação, detalhe ou inteiro teor observados sem desafio humano.

## Resultados

- A entrada PJe e o formulário legado foram alcançados por GET HTTPS bounded.
- A busca PJe respondeu erro explícito de reCAPTCHA e foi classificada como
  `access_control_required`.
- O catálogo de filtros foi registrado apenas como metadado de capacidade; não
  constitui evidência de resultados, paginação ou inteiro teor.
- Nenhum erro externo foi convertido em resultado vazio.
- O provider permanece opt-in e fora da federação padrão.

## Rastreabilidade

| Requirement | Evidence |
|---|---|
| AC-001 | `tests/test_trt6_jurisprudencia.py` options metadata test |
| AC-002 | `docs/provider-discovery/trt6-jurisprudencia-live-20260910.json` legacy form probe |
| AC-003 | `tests/test_trt6_jurisprudencia.py` reCAPTCHA boundary test |
| AC-004 | `src/nanojuris/providers/trt6_jurisprudencia.py` access error contract |
| AC-005 | candidate registry and non-federated capability |
| AC-006 | `tests/test_trt6_jurisprudencia.py` filter catalog contract; `docs/provider-discovery/trt6-filter-catalog-live-20260910.json` |
