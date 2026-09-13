# Verificação — 0065

## Gates locais executados

## Resultados

- `python -m pytest -q`: **1104 passed, 12 skipped** na rechecagem local de
  2026-09-02.
- Os 12 skips são testes live condicionados a credenciais/rede e o parser
  opcional `lxml`; nenhum representa falha de contrato local.

- `pytest -q`: execução final registrada no encerramento desta rodada.
- Suítes de regressão de contrato, federação, armazenamento, coleta, cache,
  documentos, CLI e MCP: aprovadas.
- A federação interrompe páginas repetidas sem novos identificadores, preserva
  `complete=None` quando a fonte não comprova completude e registra o motivo;
  regressão coberta em `test_federation_stops_repeated_source_page_without_marking_complete`.
- O cliente aplica `NanoJurisConfig.unified_max_pages` por fonte (padrão 25),
  evitando coleta indefinida em endpoints sem total confiável; o limite é
  reportado como incompletude, nunca como lista vazia.
- `ruff check src`: aprovado.
- `ruff format --check src`: aprovado após formatação.
- `mypy src/nanojuris`: aprovado.
- `python -m compileall -q src`: aprovado.
- `python tools/build_provider_quality.py --write`: executado.
- `python tools/build_provider_coverage.py --write`: executado.
- `python tools/audit_provider_docs.py --write`: executado.
- `python tools/validate_sdd.py`: aprovado.

As normalizacoes adicionais de grau/colecao dos adapters estaduais foram
registradas no pacote 0066, que complementa este contrato sem alterar seus
gates de compatibilidade.

Nenhum commit, push, deploy ou alteração em produção foi executado.

## Rastreabilidade

Consulte `traceability.md` para o vínculo entre requisitos, arquivos e testes.
