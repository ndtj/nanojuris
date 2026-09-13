# Verificacao

Status: verified

## Checkpoint do ciclo (2026-09-01)

- `python -m pytest -q tests/test_provider_contract_v2.py` - 16 pass.
- `python -m pytest -q tests/test_bnp_pangea.py tests/test_stj_scon.py tests/test_client_exporters.py` - pass; capabilities v2 e canonicalizacao dos dois providers preservadas.
- conjunto focado de providers, contrato e canonicalizacao - 81 pass.
- `python -m ruff check` nos arquivos do contrato - pass.
- `python -m mypy src/nanojuris` - pass em 96 arquivos.
- `python -m pytest -q` - 931 pass e 9 skips condicionais (incluindo a
  dependência opcional `lxml` e testes live sem a flag de rede).
- bateria live direcionada (`NANOJURIS_RUN_LIVE=1`) - 8 pass.
- `docs/provider-contract-v2.md`, o schema JSON e a matriz documentam a adocao
  incremental e a taxonomia.
- `bnp_pangea` e `stj_scon` adotam metadados v2 de forma aditiva, com filtros,
  ordenacao/detalhe (STJ) e fixtures nativas estaveis; os demais providers
  continuam sem promocao automatica quando nao existe evidencia contratual.
- Producao, deploy e publicacao nao foram executados.

## Resultados

| Gate | Estado | Evidencia |
| --- | --- | --- |
| compatibilidade legada | pass | campos v1 preservados e metadados v2 opcionais |
| semantica de filtros | pass | enum, helper deterministico e testes |
| outcomes e redacao | pass | estados valid/empty/partial e `safe_error_message` |
| schema/matriz v1-v2 | pass | T02; schema e matriz versionados |
| adapter de compatibilidade | pass | T04; `contracts_adapter.py` |
| migracao de providers | pass | T05; BNP/Pangea e STJ/SCON com fixtures, canonicalizacao e capacidades v2 |
| suite completa pos-integracao | pass | T08; 931 pass, 9 skips condicionais |

O ciclo foi encerrado com T01-T08 verificados. A adocao permanece incremental:
providers sem evidencia suficiente continuam explicitamente `unverified` e nao
herdam as declaracoes dos dois providers migrados.

## Rastreabilidade

REQ-001 a REQ-006 estao detalhados em `traceability.md` e verificados no
contrato, nos fixtures representativos e nos gates registrados acima.
