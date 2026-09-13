# Plano de implementação — execução por lotes

## Preparação

1. Trabalhar em `repos/nanojuris` e preservar alterações existentes.
2. Definir `PYTHONPATH=src` em cada sessão.
3. Ler `AGENTS.md`, `specs/constitution.md`, `specs/README.md`, `docs/coverage/README.md`,
   este pacote e os artefatos apontados em `execution-manifest.json`.
4. Regenerar o baseline; nunca confiar em contagens copiadas de uma conversa.

## Lote 0 — baseline e reconciliação

```powershell
$env:PYTHONPATH = 'src'
python tools/audit_open_tasks.py
python tools/build_provider_coverage.py --write
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/build_fixture_completeness.py
```

Compare os IDs de provider e superfície. Resolva divergências no código,
contrato ou gerador; não edite JSON gerado diretamente.

## Lote 1 — contratos comuns

Fechar `SearchPage`, `SourceTrace`, `FilterApplication`, `DocumentReference`,
`access_status`, `total_state`, datas e grau/instância. Adicionar testes para
erro externo versus vazio autoritativo antes de ampliar providers.

## Lote 2 — primeiro grau

Trabalhar 1–3 tribunais por vez. Procurar somente fontes oficiais de sentenças,
ementários ou acervos selecionados. Classificar cada superfície como geral,
curada ou contextual; curadoria não é acervo completo. Só promover após oito
gates.

## Lote 3 — segundo grau

Ordem recomendada: revalidar TJAC/TJAL/TJAM/TJES/TJMS; fechar TJBA/TJDFT/TJMT/
TJPA/TJPB/TJRN; fechar TJGO/TJPI/TJPR/TJRR/TJRS/TJTO; revisar TJRJ/TJSC/TJRO;
registrar bloqueios TJAP/TJCE/TJPE/TJSP; pesquisar TJMG/TJMA/TJSE.

## Lote 4 — famílias adicionais

Separar TRT/TST, TSE/TRE/SJUR, TRF/STJ/STF/STM/CJF e eproc federal. Cada família
possui contrato próprio; precedente, informativo, contexto e DataJud não contam
como jurisprudência textual geral.

## Lote 5 — dados e documentos

Para cada provider aprovado, provar filtros individualmente, duas páginas quando
suportadas, ordenação, detalhe, PDF/HTML, MIME, hash, extração, datas e
proveniência. Gerar fixtures de drift e bloqueio. OCR só quando permitido e
necessário para documento público.

## Lote 6 — federação e ranking

Executar smoke opt-in. Ativar no rollout apenas providers que cumpram os oito
gates. Atualizar ondas, status e razões de relevância. Comparar benchmark do
SDD 0077 e preservar modo `all`.

## Lote 7 — operação

Configurar smoke de baixa frequência, TTL, schema drift, completude, shadow mode
e rollback de parser. Não executar deploy. Produzir relatório de handoff e
listar dependências externas/humanas.

## Fechamento de cada lote

```powershell
python tools/audit_provider_docs.py --write
python tools/build_provider_coverage.py --write
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/build_fixture_completeness.py
python tools/validate_sdd.py
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

Rode a suíte completa apenas no fechamento do programa; durante os lotes use
testes focados. Nenhuma etapa deste plano inclui commit, push, tag, publicação,
Terraform, OCI, secrets ou produção.
