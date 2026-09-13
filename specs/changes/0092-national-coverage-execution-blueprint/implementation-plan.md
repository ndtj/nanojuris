# Plano de implementação — ondas eficientes

O executor trabalha em lotes de 1–3 providers. Inventários completos só são
regenerados no fechamento do lote; testes focados rodam durante o lote.

## Onda 0 — baseline e divergências

1. Regenerar catálogo, cobertura, qualidade, fixtures, matriz e tarefas.
2. Identificar providers runtime sem dossiê ou dossiê sem runtime.
3. Separar `live_validated` de `federation_enabled`.
4. Reabrir somente workpacks com evidência faltante.

## Onda 1 — contratos transversais

1. Fechar total conhecido/desconhecido/zero.
2. Uniformizar grau, instância, ramo, coleção, tipo, classe, órgão e datas.
3. Fechar `SourceTrace`, `DocumentReference` e estados de acesso.
4. Corrigir paginação, sobreposição, cursores e deduplicação.

## Onda 2 — primeiro grau

1. Descobrir CJPG pública de cada TJ.
2. Separar Banco de Sentenças, consulta processual e jurisprudência textual.
3. Priorizar rotas sem desafio, com filtros e texto verificáveis.
4. Marcar TJAP/TJPA/TJBA e similares como bloqueados quando exigirem acesso
   controlado; procurar export/API oficial, não contornar o desafio.

## Onda 3 — segundo grau estadual

1. Revalidar cinco superfícies completas.
2. Executar APIs B1 e portais B2 na ordem do SDD 0091.
3. Fechar eproc de TJRJ/TJSC e revisar TJRO sem usar Liame como acervo geral.
4. Reavaliar TJAP, TJCE, TJPE, TJSP, TJMG, TJMA e TJSE por rotas oficiais.

## Onda 4 — federal, superior, militar, trabalho e eleitoral

1. Fechar contratos documentais de TRF, STJ, STF, STM e CJF.
2. Separar TST/TRT e TSE/TRE/SJUR de informativos e metadados.
3. Só promover EPROC após identidade de segundo grau e detalhe comprovados.

## Onda 5 — filtros e inteiro teor

1. Exercitar cada filtro declarado em fixture e chamada live.
2. Validar datas e timezone sem substituir ausência por data artificial.
3. Baixar documentos sob demanda, verificar MIME/magic bytes/tamanho/hash.
4. Aplicar OCR apenas em PDF público permitido e registrar confiança.

## Onda 6 — federação e relevância

1. Smoke opt-in por provider promovível.
2. Validar planner, ondas, ranking, deduplicação e razões.
3. Ativar apenas tecnicamente; rótulos humanos e retenção permanecem gates
   humanos.

## Onda 7 — operação

1. Configurar smoke periódico de baixa frequência e TTL por fonte.
2. Alertar schema drift, queda de completude, bloqueio e latência.
3. Testar rollback de parser e shadow mode.

## Fechamento do lote

Executar o checklist em `model-runbook.md` do SDD 0091 e, adicionalmente:

```powershell
$env:PYTHONPATH='src'
python tools/audit_provider_docs.py --write
python tools/build_provider_coverage.py --write
python tools/build_provider_quality.py --write
python tools/build_provider_capability_ledger.py --write
python tools/build_fixture_completeness.py --write
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/validate_sdd.py
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

Não rode a suíte completa após cada provider; execute-a no fechamento da onda.
