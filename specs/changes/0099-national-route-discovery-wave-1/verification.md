# Verificação e handoff

## Resultados

Esta meta foi executada localmente. Não há promoção padrão, deploy ou alteração
de produção nesta etapa.

## Registro

### Execucao bounded 2026-09-08

- TRF1/CJF: rechecado em 2026-09-08; HTTP 200, 16687 bytes, hash
  `f671f48e903e67aa348968d46673d8d195a4f04afd7407557c0c6c1f4bed2376`, com
  marcadores CAPTCHA/reCAPTCHA e nenhum resultado autoritativo; classificado
  como `blocked_external`.
- TRF2/eproc: rota oficial validada com HTTP 200, total remoto 228086, um
  resultado de grau/instancia second e detalhe HTML publico de 160114 bytes.
- TRF4/eproc: rota oficial validada com HTTP 200, total remoto 1749378, um
  resultado de grau/instancia second e detalhe textual publico.
- O adapter independente `trf4_eproc_jurisprudencia` usa o `SharedHttpClient`,
  possui contrato, fixtures e testes dedicados e foi exercitado pela evidência
  bounded `docs/provider-discovery/trf4-live-20260908-cycle71.json`: duas
  páginas sem sobreposição, total 477848 e detalhe textual público válido.
  Este registro mais recente é a evidência considerada para T010; a contagem
  1749378 acima pertence à observação anterior.
- Evidencia sanitizada: `docs/provider-discovery/federal-route-live-20260908.json`.
- Nenhum corpo live foi persistido; nenhuma protecao foi contornada e nenhum
  provider foi promovido ao rollout padrao.

### Gates locais

- `python tools/build_national_source_task_matrix.py --write`: passou.
- `python tools/validate_sdd.py`: passou.
- `python -m pytest -q tests/test_trf4_eproc_jurisprudencia.py tests/test_state_eproc_jurisprudencia.py`: 25 passed.
- Suíte completa: 1600 passed, 26 skipped.
- Ruff, format, mypy, compileall e `git diff --check`: passaram.
- Os inventários e auditorias 0091 foram regenerados; a auditoria local ficou
  em 10 gates passed e 0 pending. Tarefas externas e humanas continuam abertas
  por política e não são mascaradas como concluídas.

T002–T004 e T006 também estão concluídas com a evidência acima: TRF1 tem
bloqueio externo explícito, TRF2/TRF4 têm rotas oficiais válidas e os detalhes
foram consultados somente a partir dos identificadores retornados. T010 está
concluída para o contrato TRF4. Isso não promove nenhuma superfície além dos
gates globais; T012 permanece dependente de decisão humana quando aplicável.
Novas tentativas devem registrar data, URL, método, status HTTP, hash, bytes,
latência, classificação e evidência.

## Comandos

```powershell
python tools/build_national_source_task_matrix.py --write
python tools/validate_sdd.py
python -m pytest -q tests/<testes-focados>
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

Critério de saída: três fontes classificadas com evidência ou explicitamente
bloqueadas/fora de jurisprudência. Nenhum resultado será promovido por uma
resposta HTTP 200 sem conteúdo e grau comprovados.

## Rastreabilidade

| Requisito | Tarefas |
| --- | --- |
| REQ-001–REQ-003 | T002–T005 |
| REQ-004–REQ-006 | T005–T007 |
| REQ-007–REQ-008 | T008–T012 |
| AC-001–AC-004 | T005–T011 |
